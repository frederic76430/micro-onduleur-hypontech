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

# (clé, nom, unité, device_class, state_class, icône, précision, activé_par_défaut)
SENSORS = [
    # ── Données globales ─────────────────────────────────────────────────
    ("power_pv",    "Puissance solaire",       UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-power",          1, False),
    ("e_today",     "Production aujourd'hui",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:solar-power",          2, True),
    ("e_total",     "Production totale",        UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:counter",              2, True),
    ("e_month",     "Production ce mois",       UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar-month",       2, True),
    ("e_year",      "Production cette année",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar",             2, True),
    ("power_load",  "Production instantanée",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-power-variant",  1, True),
    ("meter_power", "Puissance réseau",         UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:transmission-tower",   1, False),
    ("w_cha",       "Puissance batterie",       UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:battery-charging",     1, False),
    ("soc",         "Batterie",                 "%",                           SensorDeviceClass.BATTERY,     SensorStateClass.MEASUREMENT,       "mdi:battery",              0, False),
    ("total_co2",   "CO2 économisé",            "kg",                          None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:molecule-co2",         2, True),
    ("total_tree",  "Arbres équivalents",       "",                            None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:tree",                 1, True),
    # ── Données par panneau ──────────────────────────────────────────────
    ("pv1power",    "Panneau 1 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv1v",        "Panneau 1 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv1a",        "Panneau 1 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, True),
    ("pv2power",    "Panneau 2 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv2v",        "Panneau 2 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv2a",        "Panneau 2 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, True),
    ("pvtotal",     "Puissance totale DC",      UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:flash",                1, False),
    ("phvpha",      "Tension AC réseau",        UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            1, True),
    ("hz",          "Fréquence réseau",         UnitOfFrequency.HERTZ,         SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            2, True),
    ("tmpamb",      "Température onduleur",     UnitOfTemperature.CELSIUS,     SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,       "mdi:thermometer",          1, True),
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

    def __init__(self, coordinator, entry, key, name, unit, device_class, state_class, icon, precision, enabled_default):
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
        self._attr_entity_registry_enabled_default = enabled_default
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

