"""Entité de base de l'intégration Micro Onduleur Hypontech."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HypontechConfigEntry, MicroOnduleurHypontechCoordinator


class MicroOnduleurEntity(CoordinatorEntity[MicroOnduleurHypontechCoordinator]):
    """Entité rattachée à l'appareil de l'installation."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MicroOnduleurHypontechCoordinator, entry: HypontechConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.plant_id)},
            name=entry.title,
            manufacturer="Hypontech",
            model="Micro-onduleur",
            configuration_url="https://www.hypon.cloud",
        )
