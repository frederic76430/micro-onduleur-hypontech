"""Tests de l'intégration Micro Onduleur Hypontech (pytest-homeassistant-custom-component)."""

from datetime import timedelta

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER, ConfigEntryState  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from homeassistant.helpers import device_registry as dr, entity_registry as er  # noqa: E402
from homeassistant.util import dt as dt_util  # noqa: E402
from pytest_homeassistant_custom_component.common import (  # noqa: E402
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.micro_onduleur_hypontech.const import DOMAIN  # noqa: E402

BASE = "https://api.hypon.cloud/v2"
PLANT = "P1"
LAYOUT = "L1"
DATA = {"username": "a@b.fr", "password": "pw", "plant_id": PLANT, "layout_id": LAYOUT}

MONITOR = {
    "power_pv": 300, "e_today": 1.25, "e_total": 500.0, "power_load": 290,
    "meter_power": 0, "w_cha": 0, "soc": 0, "total_co2": 250.0, "total_tree": 12.0,
}
PANEL = [{"inv_monitor": [{
    "pv1power": 150, "pv1v": 32.5, "pv1a": 4.6, "pv2power": 140, "pv2v": 31.0, "pv2a": 4.5,
    "pvtotal": 290, "phvpha": 231.0, "hz": 50.01, "tmpamb": 28.0,
}]}]


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
async def _paris(hass):
    await hass.config.async_set_time_zone("Europe/Paris")


def _cloud(aioclient_mock, monitor=None, mois=3.5, annee=420.0, monitor_status=200):
    """Simule hypon.cloud."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE}/login", json={"data": {"token": "T"}})
    aioclient_mock.get(f"{BASE}/plant/list2", json={"data": [
        {"plant_id": PLANT, "plant_name": " Frédéric ", "city": "Rouen", "country": "France"}]})
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/layout", json={"data": [{"id": LAYOUT}]})
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/monitor", status=monitor_status,
                       json={"data": monitor if monitor is not None else MONITOR})
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/layout/{LAYOUT}/datav2", json={"data": PANEL})
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/energy2?type=month", json={"data": {"pvkwh": mois}})
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/energy2?type=year", json={"data": {"pvkwh": annee}})


async def _setup(hass, minor=2):
    entry = MockConfigEntry(
        domain=DOMAIN, data=DATA, unique_id=PLANT, minor_version=minor,
        title="Micro Onduleur Hypontech - Frédéric",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _etat(hass, key):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{PLANT}_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def _tick(hass, freezer, delta):
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_capteurs(hass, freezer, aioclient_mock):
    freezer.move_to("2026-11-05T12:00:00+01:00")
    _cloud(aioclient_mock)
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert float(_etat(hass, "e_today").state) == 1.25
    assert float(_etat(hass, "e_month").state) == 3.5
    assert float(_etat(hass, "e_year").state) == 420.0
    assert float(_etat(hass, "pv1power").state) == 150
    appareil = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, PLANT)})
    assert appareil is not None


async def test_coupure_cloud_garde_les_valeurs_puis_indisponible(hass, freezer, aioclient_mock):
    """Le cloud ne répond plus : jamais de 0, dernière valeur gardée, puis indisponible."""
    freezer.move_to("2026-11-05T12:00:00+01:00")
    _cloud(aioclient_mock)
    await _setup(hass)

    _cloud(aioclient_mock, monitor_status=500)
    await _tick(hass, freezer, timedelta(seconds=61))
    assert float(_etat(hass, "e_total").state) == 500.0
    assert float(_etat(hass, "e_today").state) == 1.25

    for _ in range(16):
        await _tick(hass, freezer, timedelta(seconds=61))
    assert _etat(hass, "e_total").state == "unavailable"

    # Le cloud revient
    _cloud(aioclient_mock)
    await _tick(hass, freezer, timedelta(seconds=61))
    assert float(_etat(hass, "e_total").state) == 500.0


async def test_compteur_ne_baisse_pas(hass, freezer, aioclient_mock):
    """Une valeur en retard du cloud (plus basse) est ignorée, sauf changement de période."""
    freezer.move_to("2026-11-05T12:00:00+01:00")
    _cloud(aioclient_mock)
    await _setup(hass)

    _cloud(aioclient_mock, monitor={**MONITOR, "e_today": 0.4, "e_total": 0})
    await _tick(hass, freezer, timedelta(seconds=61))
    assert float(_etat(hass, "e_today").state) == 1.25
    assert float(_etat(hass, "e_total").state) == 500.0


async def test_nouveau_jour_et_nouveau_mois(hass, freezer, aioclient_mock):
    """Au changement de jour / mois, la remise à zéro est acceptée."""
    freezer.move_to("2026-11-30T21:58:00+01:00")
    _cloud(aioclient_mock)
    await _setup(hass)

    # Nuit : pas d'appel, puissances à 0, compteurs conservés
    _cloud(aioclient_mock)
    await _tick(hass, freezer, timedelta(minutes=3))
    assert float(_etat(hass, "pv1power").state) == 0
    assert float(_etat(hass, "e_today").state) == 1.25
    assert not any("/monitor" in str(r[1]) for r in aioclient_mock.mock_calls)

    # Le matin du 1er décembre
    freezer.move_to("2026-12-01T06:01:00+01:00")
    _cloud(aioclient_mock, monitor={**MONITOR, "e_today": 0.01}, mois=0.01)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert float(_etat(hass, "e_today").state) == 0.01
    assert float(_etat(hass, "e_month").state) == 0.01
    # Le mois demandé est bien décembre (heure de Paris)
    assert any("month=12" in str(r[1]) for r in aioclient_mock.mock_calls)


async def test_jeton_expire_reconnexion(hass, freezer, aioclient_mock):
    """Un 401 provoque une reconnexion ; si elle échoue, Home Assistant demande les identifiants."""
    freezer.move_to("2026-11-05T12:00:00+01:00")
    _cloud(aioclient_mock)
    entry = await _setup(hass)

    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{BASE}/login", status=401)
    aioclient_mock.get(f"{BASE}/plant/{PLANT}/monitor", status=401)
    await _tick(hass, freezer, timedelta(hours=2))
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(f["context"]["source"] == SOURCE_REAUTH for f in flows)
    assert entry.state is ConfigEntryState.LOADED


async def test_config_flow_et_reauth(hass, aioclient_mock):
    _cloud(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "a@b.fr", "password": "pw"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Micro Onduleur Hypontech - Frédéric"
    assert result["data"] == DATA
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == PLANT

    # Réauthentification : met à jour l'entrée existante (pas de doublon)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id}, data=entry.data
    )
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "a@b.fr", "password": "nouveau"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["password"] == "nouveau"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_config_flow_mauvais_identifiants(hass, aioclient_mock):
    aioclient_mock.post(f"{BASE}/login", json={"data": {}})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "a@b.fr", "password": "faux"}
    )
    assert result["errors"] == {"base": "invalid_auth"}


async def test_migration_identifiants(hass, freezer, aioclient_mock):
    """Les anciens identifiants (entry_id_xxx) passent à plant_id_xxx sans changer sensor.xxx."""
    freezer.move_to("2026-11-05T12:00:00+01:00")
    _cloud(aioclient_mock)
    entry = MockConfigEntry(
        domain=DOMAIN, data=DATA, unique_id=PLANT, minor_version=1,
        title="Micro Onduleur Hypontech - Frédéric",
    )
    entry.add_to_hass(hass)
    reg = er.async_get(hass)
    ancien = reg.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_e_month", config_entry=entry,
        suggested_object_id="garage_micro_onduleur_hypontech_frederic_production_ce_mois",
    )
    dreg = dr.async_get(hass)
    dreg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, entry.entry_id)})

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 2
    migre = reg.async_get(ancien.entity_id)
    assert migre.unique_id == f"{PLANT}_e_month"
    assert migre.entity_id == "sensor.garage_micro_onduleur_hypontech_frederic_production_ce_mois"
    assert float(hass.states.get(migre.entity_id).state) == 3.5
    assert dreg.async_get_device(identifiers={(DOMAIN, PLANT)}) is not None


async def test_panneaux_a_zero_quand_plus_de_production(hass, freezer, aioclient_mock):
    """Le soir, le cloud renvoie encore la dernière mesure des panneaux : remise à 0."""
    freezer.move_to("2026-11-05T21:20:00+01:00")
    _cloud(aioclient_mock, monitor={**MONITOR, "power_pv": 0, "power_load": 0})
    await _setup(hass)
    assert float(_etat(hass, "pv1power").state) == 0
    assert float(_etat(hass, "pv1a").state) == 0
    assert float(_etat(hass, "pv1v").state) == 32.5
    assert float(_etat(hass, "e_today").state) == 1.25
