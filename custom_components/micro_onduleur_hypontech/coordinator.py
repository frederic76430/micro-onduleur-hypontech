"""Coordinator de l'intégration Micro Onduleur Hypontech."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import HypontechAuthError, HypontechConnectionError, MicroOnduleurHypontechAPI
from .const import (
    DOMAIN,
    INTERVAL_DAY,
    INTERVAL_NIGHT,
    INTERVAL_SLOW,
    LOGGER,
    MAX_STALE,
    SOLAR_HOUR_END,
    SOLAR_HOUR_START,
)

# Données globales (endpoint /monitor)
MONITOR_KEYS = (
    "power_pv", "e_today", "e_total", "power_load", "meter_power",
    "w_cha", "soc", "total_co2", "total_tree",
)
# Données par panneau (endpoint /layout/…/datav2)
PANEL_KEYS = (
    "pv1power", "pv1v", "pv1a", "pv2power", "pv2v", "pv2a",
    "pv3power", "pv3v", "pv3a", "pv4power", "pv4v", "pv4a",
    "pvtotal", "phvpha", "hz", "tmpamb",
)
# Données lentes (endpoint /energy2), une fois par heure
SLOW_KEYS = ("e_month", "e_year")

# Puissances et courants remis à 0 la nuit (les compteurs, eux, gardent leur valeur)
NIGHT_ZERO_KEYS = (
    "power_pv", "power_load", "meter_power", "w_cha", "pvtotal",
    "pv1power", "pv2power", "pv3power", "pv4power",
    "pv1a", "pv2a", "pv3a", "pv4a",
)

# Puissances et courants des panneaux, remis à 0 quand l'onduleur ne produit pas
PANEL_ZERO_KEYS = (
    "pv1power", "pv2power", "pv3power", "pv4power",
    "pv1a", "pv2a", "pv3a", "pv4a", "pvtotal",
)

# Compteurs qui ne doivent jamais baisser, sauf au changement de période indiqué
#   jour / mois / annee : remise à zéro autorisée au changement de jour, mois, année
#   None : ne baisse jamais
COUNTERS: dict[str, str | None] = {
    "e_today": "jour",
    "e_month": "mois",
    "e_year": "annee",
    "e_total": None,
    "total_co2": None,
    "total_tree": None,
}

type HypontechConfigEntry = ConfigEntry[MicroOnduleurHypontechCoordinator]


def _periode_changee(periode: str | None, avant: date, apres: date) -> bool:
    if periode == "jour":
        return apres != avant
    if periode == "mois":
        return (apres.year, apres.month) != (avant.year, avant.month)
    if periode == "annee":
        return apres.year != avant.year
    return False


def _nombre(valeur: Any) -> float | None:
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


class MicroOnduleurHypontechCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Récupère toutes les données Hypontech.

    Règles :
      - le cloud ne répond pas → on garde la dernière valeur connue ; au-delà de
        MAX_STALE, les capteurs passent « indisponible » (jamais de 0 inventé) ;
      - un compteur d'énergie ne baisse jamais, sauf au changement de jour / mois / année ;
      - la nuit, pas d'appel au cloud : puissances à 0, compteurs conservés ;
      - identifiants refusés → Home Assistant propose de les ressaisir.
    """

    config_entry: HypontechConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: HypontechConfigEntry,
        api: MicroOnduleurHypontechAPI,
        plant_id: str,
        layout_id: str,
    ) -> None:
        super().__init__(
            hass, LOGGER, config_entry=entry, name=DOMAIN, update_interval=INTERVAL_DAY
        )
        self.api = api
        self.plant_id = plant_id
        self.layout_id = layout_id
        self._last_success: datetime | None = None
        self._last_slow: datetime | None = None
        self._jour_donnees: date | None = None

    @staticmethod
    def _heures_solaires(maintenant: datetime) -> bool:
        return SOLAR_HOUR_START <= maintenant.hour < SOLAR_HOUR_END

    async def _async_update_data(self) -> dict[str, Any]:
        maintenant = dt_util.now()
        jour = maintenant.date()
        precedent: dict[str, Any] = dict(self.data or {})

        # ---- Nuit : pas d'appel au cloud (sauf si on n'a encore aucune donnée)
        if not self._heures_solaires(maintenant):
            self.update_interval = INTERVAL_NIGHT
            if precedent:
                LOGGER.debug("Nuit : onduleur éteint, pas d'appel au cloud")
                nuit = dict(precedent)
                nuit.update(dict.fromkeys(NIGHT_ZERO_KEYS, 0.0))
                return nuit
        else:
            self.update_interval = INTERVAL_DAY

        # ---- Jour : appel au cloud
        try:
            monitor = await self.api.get_monitor_data(self.plant_id)
        except HypontechAuthError as err:
            raise ConfigEntryAuthFailed("Identifiants hypon.cloud refusés") from err
        except HypontechConnectionError as err:
            return self._sans_reponse(precedent, maintenant, err)

        nouveau = dict(precedent)
        for cle in MONITOR_KEYS:
            valeur = _nombre(monitor.get(cle))
            if valeur is not None:
                nouveau[cle] = valeur
            else:
                nouveau.setdefault(cle, 0.0)

        # Panneaux : si l'appel échoue, on garde les valeurs précédentes
        try:
            panneau = await self.api.get_panel_data(self.plant_id, self.layout_id, jour) or {}
        except HypontechConnectionError as err:
            LOGGER.debug("Données par panneau indisponibles : %s", err)
            panneau = None
        for cle in PANEL_KEYS:
            valeur = _nombre(panneau.get(cle)) if panneau is not None else None
            if valeur is not None:
                nouveau[cle] = valeur
            else:
                nouveau.setdefault(cle, 0.0)

        # Les données par panneau renvoient la dernière mesure *avec production* de la journée :
        # le soir, elles restent figées (ex. 5 W à 21 h). Si l'onduleur ne produit plus,
        # puissances et courants des panneaux sont remis à 0.
        if not (nouveau.get("power_load") or 0) and not (nouveau.get("power_pv") or 0):
            nouveau.update(dict.fromkeys(PANEL_ZERO_KEYS, 0.0))

        # Mois / année : une fois par heure, et tout de suite au changement de mois
        mois_change = self._jour_donnees is not None and (
            (jour.year, jour.month) != (self._jour_donnees.year, self._jour_donnees.month)
        )
        if self._last_slow is None or mois_change or maintenant - self._last_slow >= INTERVAL_SLOW:
            try:
                nouveau["e_month"] = await self.api.get_energy_month(self.plant_id, jour)
                nouveau["e_year"] = await self.api.get_energy_year(self.plant_id, jour)
                self._last_slow = maintenant
            except HypontechConnectionError as err:
                LOGGER.debug("Production mois / année indisponible, nouvel essai au prochain passage : %s", err)
        for cle in SLOW_KEYS:
            nouveau.setdefault(cle, 0.0)

        # Les compteurs ne baissent jamais (sauf changement de période)
        if precedent and self._jour_donnees is not None:
            for cle, periode in COUNTERS.items():
                avant, apres = _nombre(precedent.get(cle)), _nombre(nouveau.get(cle))
                if avant is None or apres is None or apres >= avant:
                    continue
                if _periode_changee(periode, self._jour_donnees, jour):
                    continue
                LOGGER.debug("%s : %s < %s ignoré (valeur du cloud en retard)", cle, apres, avant)
                nouveau[cle] = avant

        self._last_success = maintenant
        self._jour_donnees = jour
        return nouveau

    def _sans_reponse(
        self, precedent: dict[str, Any], maintenant: datetime, err: Exception
    ) -> dict[str, Any]:
        """Le cloud ne répond pas : dernière valeur connue, puis indisponible."""
        if precedent and self._last_success and maintenant - self._last_success < MAX_STALE:
            LOGGER.debug("Cloud Hypontech injoignable, dernières valeurs conservées : %s", err)
            return precedent
        raise UpdateFailed(
            translation_domain=DOMAIN,
            translation_key="connection_error",
        ) from err
