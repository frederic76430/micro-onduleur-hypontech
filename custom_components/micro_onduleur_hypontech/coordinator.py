"""Coordinator pour Micro Onduleur Hypontech."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MicroOnduleurHypontechAPI
from .const import DOMAIN

from .const import DOMAIN, LOGGER
_LOGGER = LOGGER

# Intervalles de mise à jour
INTERVAL_DAY = timedelta(seconds=60)    # 1 minute en journée
INTERVAL_NIGHT = timedelta(minutes=30)  # 30 minutes la nuit

# Heures de production solaire
SOLAR_HOUR_START = 6
SOLAR_HOUR_END = 22

# Intervalle pour les données lentes (mois/année) — 1 heure
INTERVAL_SLOW = timedelta(hours=1)


@dataclass
class MicroOnduleurData:
    """Structure des données du coordinator."""

    # Données globales
    power_pv: float = 0.0
    e_today: float = 0.0
    e_total: float = 0.0
    e_month: float = 0.0
    e_year: float = 0.0
    power_load: float = 0.0
    meter_power: float = 0.0
    w_cha: float = 0.0
    soc: float = 0.0
    total_co2: float = 0.0
    total_tree: float = 0.0
    # Données par panneau
    pv1power: float = 0.0
    pv1v: float = 0.0
    pv1a: float = 0.0
    pv2power: float = 0.0
    pv2v: float = 0.0
    pv2a: float = 0.0
    pv3power: float = 0.0
    pv3v: float = 0.0
    pv3a: float = 0.0
    pv4power: float = 0.0
    pv4v: float = 0.0
    pv4a: float = 0.0
    pvtotal: float = 0.0
    phvpha: float = 0.0
    hz: float = 0.0
    tmpamb: float = 0.0

    def to_dict(self) -> dict:
        """Convertir en dictionnaire pour les capteurs."""
        return {k: v for k, v in self.__dict__.items()}


class MicroOnduleurHypontechCoordinator(DataUpdateCoordinator):
    """Coordinator pour récupérer toutes les données Hypontech."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MicroOnduleurHypontechAPI,
        plant_id: str,
        layout_id: str,
        scan_interval: int,
    ) -> None:
        """Initialiser le coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=INTERVAL_DAY,
        )
        self.api = api
        self.plant_id = plant_id
        self.layout_id = layout_id
        self._last_data: dict = {}
        self._last_slow_update: datetime | None = None

    def _is_solar_hours(self) -> bool:
        """Vérifier si on est dans les heures de production solaire."""
        now = datetime.now()
        return SOLAR_HOUR_START <= now.hour < SOLAR_HOUR_END

    def _should_update_slow(self) -> bool:
        """Vérifier si on doit mettre à jour les données lentes (mois/année)."""
        if self._last_slow_update is None:
            return True
        return datetime.now() - self._last_slow_update >= INTERVAL_SLOW

    async def _async_update_data(self) -> dict:
        """Récupérer les données de façon intelligente."""

        # La nuit : ralentir et retourner données avec puissances à 0
        if not self._is_solar_hours():
            self.update_interval = INTERVAL_NIGHT
            if self._last_data:
                _LOGGER.debug("Nuit — onduleur éteint, pas d'appel API")
                nuit_data = dict(self._last_data)
                nuit_data.update({
                    "power_pv": 0.0,
                    "pv1power": 0.0,
                    "pv2power": 0.0,
                    "pv3power": 0.0,
                    "pv4power": 0.0,
                    "pv1a": 0.0,
                    "pv2a": 0.0,
                    "pv3a": 0.0,
                    "pv4a": 0.0,
                    "pvtotal": 0.0,
                    "meter_power": 0.0,
                    "power_load": 0.0,
                    "w_cha": 0.0,
                })
                return nuit_data
        else:
            self.update_interval = INTERVAL_DAY

        # Pendant la journée — appel API
        try:
            monitor = await self.api.get_monitor_data(self.plant_id) or {}
            panel = await self.api.get_panel_data(self.plant_id, self.layout_id) or {}

            # Données lentes (mois/année) — seulement 1 fois par heure
            if self._should_update_slow():
                e_month = await self.api.get_energy_month(self.plant_id)
                e_year = await self.api.get_energy_year(self.plant_id)
                self._last_slow_update = datetime.now()
                _LOGGER.debug("Mise à jour données lentes (mois/année)")
            else:
                e_month = self._last_data.get("e_month", 0.0)
                e_year = self._last_data.get("e_year", 0.0)

            data = {
                # Données globales
                "power_pv": monitor.get("power_pv", 0.0),
                "e_today": monitor.get("e_today", 0.0),
                "e_total": monitor.get("e_total", 0.0),
                "e_month": e_month,
                "e_year": e_year,
                "power_load": monitor.get("power_load", 0.0),
                "meter_power": monitor.get("meter_power", 0.0),
                "w_cha": monitor.get("w_cha", 0.0),
                "soc": monitor.get("soc", 0.0),
                "total_co2": monitor.get("total_co2", 0.0),
                "total_tree": monitor.get("total_tree", 0.0),
                # Données par panneau
                "pv1power": panel.get("pv1power", 0.0),
                "pv1v": panel.get("pv1v", 0.0),
                "pv1a": panel.get("pv1a", 0.0),
                "pv2power": panel.get("pv2power", 0.0),
                "pv2v": panel.get("pv2v", 0.0),
                "pv2a": panel.get("pv2a", 0.0),
                "pv3power": panel.get("pv3power", 0.0),
                "pv3v": panel.get("pv3v", 0.0),
                "pv3a": panel.get("pv3a", 0.0),
                "pv4power": panel.get("pv4power", 0.0),
                "pv4v": panel.get("pv4v", 0.0),
                "pv4a": panel.get("pv4a", 0.0),
                "pvtotal": panel.get("pvtotal", 0.0),
                "phvpha": panel.get("phvpha", 0.0),
                "hz": panel.get("hz", 0.0),
                "tmpamb": panel.get("tmpamb", 0.0),
            }

            self._last_data = data
            _LOGGER.debug(
                "Données reçues — puissance totale: %sW",
                data.get("pvtotal", 0)
            )
            return data

        except Exception as e:
            _LOGGER.warning("Erreur API Hypontech: %s", e)

        # Si erreur mais données précédentes disponibles
        if self._last_data:
            _LOGGER.warning("Erreur API — utilisation des dernières données")
            return self._last_data

        raise UpdateFailed(
            translation_domain=DOMAIN,
            translation_key="connection_error",
        )
