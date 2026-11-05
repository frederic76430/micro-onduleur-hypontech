"""Micro Onduleur Hypontech - Intégration Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MicroOnduleurHypontechAPI
from .const import CONF_LAYOUT_ID, CONF_PLANT_ID, DOMAIN, LOGGER
from .coordinator import HypontechConfigEntry, MicroOnduleurHypontechCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: HypontechConfigEntry) -> bool:
    """Configurer l'intégration."""
    api = MicroOnduleurHypontechAPI(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], async_get_clientsession(hass)
    )
    coordinator = MicroOnduleurHypontechCoordinator(
        hass, entry, api, str(entry.data[CONF_PLANT_ID]), str(entry.data[CONF_LAYOUT_ID])
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HypontechConfigEntry) -> bool:
    """Décharger l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: HypontechConfigEntry) -> bool:
    """Migration 1.1 → 1.2 : identifiants basés sur l'installation Hypontech.

    Avant la v1.1.0, les identifiants uniques des capteurs et de l'appareil reprenaient
    l'identifiant interne de l'intégration (qui change à chaque réinstallation).
    Ils reprennent maintenant l'identifiant de l'installation (plant_id).
    Les noms d'entités (sensor.xxx) ne changent pas.
    """
    if entry.version > 1:
        return False

    if entry.minor_version < 2:
        plant_id = str(entry.data[CONF_PLANT_ID])
        ancien = f"{entry.entry_id}_"

        @callback
        def _migrer(entite: er.RegistryEntry) -> dict | None:
            if entite.unique_id.startswith(ancien):
                return {"new_unique_id": f"{plant_id}_{entite.unique_id[len(ancien):]}"}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, _migrer)

        registre = dr.async_get(hass)
        appareil = registre.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
        if appareil is not None:
            registre.async_update_device(appareil.id, new_identifiers={(DOMAIN, plant_id)})

        hass.config_entries.async_update_entry(entry, minor_version=2)
        LOGGER.info("Micro Onduleur Hypontech : identifiants migrés vers l'installation %s", plant_id)

    return True
