"""Capteurs de l'intégration Micro Onduleur Hypontech."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import LOGGER
from .coordinator import HypontechConfigEntry, MicroOnduleurHypontechCoordinator
from .entity import MicroOnduleurEntity

PARALLEL_UPDATES = 0

# Capteurs pv3/pv4 — désactivés par défaut, activés auto si onduleur 4 entrées
PV34_KEYS = {"pv3power", "pv3v", "pv3a", "pv4power", "pv4v", "pv4a"}

# Capteurs batterie — désactivés par défaut, activés auto si batterie détectée
BATTERY_KEYS = {"soc", "w_cha"}

# (clé, nom, unité, device_class, state_class, icône, précision, activé_par_défaut)
SENSORS = [
    # ── Données globales ─────────────────────────────────────────────────
    ("power_pv",    "Puissance solaire",        UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-power",          1, False),
    ("e_today",     "Production aujourd'hui",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:solar-power",          2, True),
    ("e_total",     "Production totale",        UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:counter",              2, True),
    ("e_month",     "Production ce mois",       UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar-month",       2, True),
    ("e_year",      "Production cette année",   UnitOfEnergy.KILO_WATT_HOUR,   SensorDeviceClass.ENERGY,      SensorStateClass.TOTAL_INCREASING,  "mdi:calendar",             2, True),
    ("power_load",  "Production instantanée",   UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-power-variant",  1, True),
    ("meter_power", "Puissance réseau",         UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:transmission-tower",   1, False),
    ("w_cha",       "Puissance batterie",       UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:battery-charging",     1, False),
    ("soc",         "Batterie",                 "%",                           SensorDeviceClass.BATTERY,     SensorStateClass.MEASUREMENT,       "mdi:battery",              0, False),
    ("total_co2",   "CO2 économisé",            "kg",                          None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:molecule-co2",         2, True),
    ("total_tree",  "Arbres équivalents",       None,                            None,                          SensorStateClass.TOTAL_INCREASING,  "mdi:tree",                 1, True),
    # ── Données par panneau ──────────────────────────────────────────────
    ("pv1power",    "Panneau 1 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv1v",        "Panneau 1 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv1a",        "Panneau 1 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, True),
    ("pv2power",    "Panneau 2 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv2v",        "Panneau 2 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, True),
    ("pv2a",        "Panneau 2 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, True),
    # pv3/pv4 — désactivés par défaut, activés auto si onduleur 4 entrées
    ("pv3power",    "Panneau 3 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, False),
    ("pv3v",        "Panneau 3 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, False),
    ("pv3a",        "Panneau 3 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, False),
    ("pv4power",    "Panneau 4 - Puissance",    UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, False),
    ("pv4v",        "Panneau 4 - Tension",      UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          1, False),
    ("pv4a",        "Panneau 4 - Courant",      UnitOfElectricCurrent.AMPERE,  SensorDeviceClass.CURRENT,     SensorStateClass.MEASUREMENT,       "mdi:solar-panel",          2, False),
    ("pvtotal",     "Puissance totale DC",      UnitOfPower.WATT,              SensorDeviceClass.POWER,       SensorStateClass.MEASUREMENT,       "mdi:flash",                1, False),
    ("phvpha",      "Tension AC réseau",        UnitOfElectricPotential.VOLT,  SensorDeviceClass.VOLTAGE,     SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            1, True),
    ("hz",          "Fréquence réseau",         UnitOfFrequency.HERTZ,         SensorDeviceClass.FREQUENCY,   SensorStateClass.MEASUREMENT,       "mdi:sine-wave",            2, True),
    ("tmpamb",      "Température onduleur",     UnitOfTemperature.CELSIUS,     SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,       "mdi:thermometer",          1, True),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HypontechConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Créer les capteurs."""
    coordinator = entry.runtime_data
    data = coordinator.data or {}

    def positif(*cles: str) -> bool:
        return any(float(data.get(c) or 0) > 0 for c in cles)

    # Onduleur 4 entrées et batterie : capteurs activés automatiquement s'ils sont détectés
    has_pv34 = positif("pv3power", "pv3v", "pv4power", "pv4v")
    has_battery = positif("soc", "w_cha")
    if has_pv34:
        LOGGER.info("Onduleur 4 entrées détecté : capteurs pv3 / pv4 activés")
    if has_battery:
        LOGGER.info("Batterie détectée : capteurs batterie activés")

    entities = []
    for sensor in SENSORS:
        key, enabled = sensor[0], sensor[7]
        if (key in PV34_KEYS and has_pv34) or (key in BATTERY_KEYS and has_battery):
            enabled = True
        entities.append(MicroOnduleurHypontechSensor(coordinator, entry, *sensor[:7], enabled))
    async_add_entities(entities)


class MicroOnduleurHypontechSensor(MicroOnduleurEntity, SensorEntity):
    """Capteur Micro Onduleur Hypontech."""

    def __init__(
        self,
        coordinator: MicroOnduleurHypontechCoordinator,
        entry: HypontechConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str,
        precision: int,
        enabled_default: bool,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._precision = precision
        self._attr_name = name
        # Identifiant stable : basé sur l'installation, pas sur l'entrée de configuration
        self._attr_unique_id = f"{coordinator.plant_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def native_value(self) -> float | None:
        """Valeur du capteur (None = inconnue, jamais 0 inventé)."""
        value = (self.coordinator.data or {}).get(self._key)
        try:
            return round(float(value), self._precision)
        except (TypeError, ValueError):
            return None
