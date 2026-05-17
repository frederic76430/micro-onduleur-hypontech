"""Config flow pour Micro Onduleur Hypontech."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MicroOnduleurHypontechAPI
from .const import (
    CONF_LAYOUT_ID,
    CONF_PASSWORD,
    CONF_PLANT_ID,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MicroOnduleurHypontechConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration Micro Onduleur Hypontech."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialiser."""
        self._plants: list[dict] = []
        self._username = ""
        self._password = ""

    async def async_step_user(self, user_input=None):
        """Étape 1 : Saisie des identifiants."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            api = MicroOnduleurHypontechAPI(username, password, session)

            if await api.connect():
                plants = await api.get_plants()
                if plants:
                    self._plants = plants
                    self._username = username
                    self._password = password
                    if len(plants) == 1:
                        return await self._create_entry_for_plant(plants[0], api)
                    return await self.async_step_plant()
                else:
                    errors["base"] = "no_plants"
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={"url": "hypon.cloud"},
        )

    async def async_step_plant(self, user_input=None):
        """Étape 2 : Choisir l'installation (si plusieurs)."""
        errors = {}

        plant_options = {
            p["plant_id"]: f"{p['plant_name']} - {p['city']} ({p['country']})"
            for p in self._plants
        }

        if user_input is not None:
            plant_id = user_input[CONF_PLANT_ID]
            plant = next(p for p in self._plants if p["plant_id"] == plant_id)
            session = async_get_clientsession(self.hass)
            api = MicroOnduleurHypontechAPI(self._username, self._password, session)
            return await self._create_entry_for_plant(plant, api)

        return self.async_show_form(
            step_id="plant",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PLANT_ID): vol.In(plant_options),
                }
            ),
            errors=errors,
        )

    async def _create_entry_for_plant(self, plant: dict, api: MicroOnduleurHypontechAPI):
        """Créer l'entrée de configuration pour une installation."""
        plant_id = plant["plant_id"]
        plant_name = plant["plant_name"].strip()

        await self.async_set_unique_id(plant_id)
        self._abort_if_unique_id_configured()

        layouts = await api.get_layouts(plant_id)
        if not layouts:
            return self.async_abort(reason="no_layout")

        layout_id = str(layouts[0]["id"])

        return self.async_create_entry(
            title=f"Micro Onduleur Hypontech - {plant_name}",
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_PLANT_ID: plant_id,
                CONF_LAYOUT_ID: layout_id,
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            },
        )
