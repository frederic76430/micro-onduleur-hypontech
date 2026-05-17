"""Capteurs Micro Onduleur Hypontech."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MicroOnduleurHypontechCoordinator

_LOGGER = logging.getLogger(__name__)

SENSORS = [
    # ── Données globales ─────────────────────────────────────────────────
    ("power_pv",    "Puissance solaire",       UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-power",          1),
    ("e_today",     "Production aujourd'hui",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:solar-power",          2),
    ("e_total",     "Production totale",        UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:counter",              2),
    ("e_month",     "Production ce mois",       UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar-month",       2),
    ("e_year",      "Production cette année",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar",             2),
    ("power_load",  "Consommation maison",      UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:home-lightning-bolt",  1),
    ("meter_power", "Puissance réseau",         UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:transmission-tower",   1),
    ("w_cha",       "Puissance batterie",       UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:battery-charging",     1),
    ("soc",         "Batterie",                 "%",                           SensorDeviceClass.BATTERY,     SensorStateClass.MEASUREMENT,       "mdi:battery",              0),
    ("total_co2",   "CO2 économisé",            "kg",                          None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:molecule-co2",         2),
    ("total_tree",  "Arbres équivalents",       "",                            None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:tree",                 1),
    # ── Données par panneau ──────────────────────────────────────────────
    ("pv1power",    "Panneau 1 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1),
    ("pv1v",        "Panneau 1 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1),
    ("pv1a",        "Panneau 1 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2),
    ("pv2power",    "Panneau 2 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1),
    ("pv2v",        "Panneau 2 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1),
    ("pv2a",        "Panneau 2 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2),
    ("pvtotal",     "Puissance totale DC",      UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:flash",                1),
    ("phvpha",      "Tension AC réseau",        UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            1),
    ("hz",          "Fréquence réseau",         UnitOfFrequency.HERTZ,         SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            2),
    ("tmpamb",      "Température onduleur",     UnitOfTemperature.CELSIUS,     SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,       "mdi:thermometer",          1),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer tous les capteurs."""
    coordinator: MicroOnduleurHypontechCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MicroOnduleurHypontechSensor(coordinator, entry, *sensor)
        for sensor in SENSORS
    ])


class MicroOnduleurHypontechSensor(CoordinatorEntity, SensorEntity):
    """Capteur Micro Onduleur Hypontech."""

    def __init__(self, coordinator, entry, key, name, unit, device_class, state_class, icon, precision):
        """Initialiser."""
        super().__init__(coordinator)
        self._key = key
        self._precision = precision
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Hypontech",
            "model": "HMS-800W-C",
            "configuration_url": "https://www.hypon.cloud",
        }

    @property
    def native_value(self):
        """Retourner la valeur."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        try:
            return round(float(value), self._precision)
        except (ValueError, TypeError):
            return None
