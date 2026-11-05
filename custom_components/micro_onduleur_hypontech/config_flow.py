"""Config flow de l'intégration Micro Onduleur Hypontech."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HypontechAuthError, HypontechConnectionError, MicroOnduleurHypontechAPI
from .const import CONF_LAYOUT_ID, CONF_PLANT_ID, DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


def _libelle(plant: dict) -> str:
    nom = str(plant.get("plant_name") or plant.get("plant_id")).strip()
    lieu = ", ".join(str(x) for x in (plant.get("city"), plant.get("country")) if x)
    return f"{nom} ({lieu})" if lieu else nom


class MicroOnduleurHypontechConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ajout d'une installation hypon.cloud."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._plants: list[dict] = []
        self._username = ""
        self._password = ""
        self._api: MicroOnduleurHypontechAPI | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Étape 1 : identifiants hypon.cloud."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api = MicroOnduleurHypontechAPI(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], async_get_clientsession(self.hass)
            )
            try:
                await api.connect()
                plants = await api.get_plants()
            except HypontechAuthError:
                errors["base"] = "invalid_auth"
            except HypontechConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Erreur inattendue")
                errors["base"] = "unknown"
            else:
                if not plants:
                    errors["base"] = "no_plants"
                else:
                    self._plants = plants
                    self._username = user_input[CONF_USERNAME]
                    self._password = user_input[CONF_PASSWORD]
                    self._api = api
                    if len(plants) == 1:
                        return await self._create_entry_for_plant(plants[0])
                    return await self.async_step_plant()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_plant(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Étape 2 : choix de l'installation (si le compte en a plusieurs)."""
        if user_input is not None:
            plant = next(
                p for p in self._plants if str(p["plant_id"]) == user_input[CONF_PLANT_ID]
            )
            return await self._create_entry_for_plant(plant)

        options = {str(p["plant_id"]): _libelle(p) for p in self._plants}
        return self.async_show_form(
            step_id="plant",
            data_schema=vol.Schema({vol.Required(CONF_PLANT_ID): vol.In(options)}),
        )

    async def _create_entry_for_plant(self, plant: dict) -> ConfigFlowResult:
        """Créer l'entrée pour une installation."""
        plant_id = str(plant["plant_id"])
        await self.async_set_unique_id(plant_id)
        self._abort_if_unique_id_configured()

        assert self._api is not None
        try:
            layouts = await self._api.get_layouts(plant_id)
        except HypontechConnectionError:
            return self.async_abort(reason="cannot_connect")
        if not layouts:
            return self.async_abort(reason="no_layout")

        return self.async_create_entry(
            title=f"Micro Onduleur Hypontech - {str(plant.get('plant_name') or plant_id).strip()}",
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_PLANT_ID: plant_id,
                CONF_LAYOUT_ID: str(layouts[0]["id"]),
            },
        )

    # ------------------------------------------------------------ réauthentification
    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Le cloud refuse les identifiants enregistrés."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ressaisir le mot de passe hypon.cloud."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            api = MicroOnduleurHypontechAPI(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], async_get_clientsession(self.hass)
            )
            try:
                await api.connect()
            except HypontechAuthError:
                errors["base"] = "invalid_auth"
            except HypontechConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Erreur inattendue")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
