"""Entité de base pour Micro Onduleur Hypontech."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import MicroOnduleurHypontechCoordinator


class MicroOnduleurEntity(CoordinatorEntity[MicroOnduleurHypontechCoordinator]):
    """Entité de base pour Micro Onduleur Hypontech."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MicroOnduleurHypontechCoordinator,
        entry_id: str,
        entry_title: str,
    ) -> None:
        """Initialiser l'entité."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=entry_title,
            manufacturer="Hypontech",
            model="HMS-800W-C",
            configuration_url="https://www.hypon.cloud",
        )

    @property
    def available(self) -> bool:
        """Retourner si l'entité est disponible."""
        return super().available and self.coordinator.data is not None
