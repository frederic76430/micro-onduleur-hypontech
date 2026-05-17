"""Coordinator pour Micro Onduleur Hypontech."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MicroOnduleurHypontechAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.plant_id = plant_id
        self.layout_id = layout_id

    async def _async_update_data(self) -> dict:
        """Récupérer toutes les données depuis l'API."""
        data = await self.api.get_all_data(self.plant_id, self.layout_id)
        if not data:
            raise UpdateFailed("Impossible de récupérer les données Hypontech")
        _LOGGER.debug("Données Hypontech reçues: %s", data)
        return data
