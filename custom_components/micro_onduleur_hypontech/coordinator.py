"""Coordinator pour Micro Onduleur Hypontech."""

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MicroOnduleurHypontechAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Intervalles de mise à jour
INTERVAL_DAY = timedelta(minutes=5)
INTERVAL_NIGHT = timedelta(minutes=30)

# Heures de production solaire
SOLAR_HOUR_START = 6
SOLAR_HOUR_END = 22


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

    def _is_solar_hours(self) -> bool:
        """Vérifier si on est dans les heures de production solaire."""
        now = datetime.now()
        return SOLAR_HOUR_START <= now.hour < SOLAR_HOUR_END

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
                    "pv1a": 0.0,
                    "pv2a": 0.0,
                    "pvtotal": 0.0,
                    "meter_power": 0.0,
                    "power_load": 0.0,
                    "w_cha": 0.0,
                })
                return nuit_data
        else:
            self.update_interval = INTERVAL_DAY

        # Pendant la journée — appel API normal
        try:
            data = await self.api.get_all_data(self.plant_id, self.layout_id)
            if data:
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

        raise UpdateFailed("Impossible de récupérer les données Hypontech")
