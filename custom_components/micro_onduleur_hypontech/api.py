"""API client for Micro Onduleur Hypontech."""

import logging
from datetime import date
from time import time

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.hypon.cloud/v2"
TOKEN_VALIDITY = 3600


class MicroOnduleurHypontechAPI:
    """Client API Hypontech - données globales + par panneau."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialiser le client."""
        self._username = username
        self._password = password
        self._session = session
        self._token = ""
        self._token_expires_at = 0

    async def connect(self) -> bool:
        """Se connecter et récupérer le token."""
        if self._token and self._token_expires_at > time():
            return True

        try:
            async with self._session.post(
                f"{BASE_URL}/login",
                json={"username": self._username, "password": self._password},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Échec connexion Hypontech: HTTP %s", response.status)
                    return False
                result = await response.json()
                token = result.get("data", {}).get("token")
                if not token:
                    _LOGGER.error("Token manquant dans la réponse")
                    return False
                self._token = token
                self._token_expires_at = int(time()) + TOKEN_VALIDITY
                _LOGGER.debug("Connexion Hypontech réussie")
                return True
        except Exception as e:
            _LOGGER.error("Erreur connexion Hypontech: %s", e)
            return False

    async def _get(self, url: str) -> dict | None:
        """Faire une requête GET authentifiée."""
        if not await self.connect():
            return None
        try:
            async with self._session.get(
                url,
                headers={"authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Erreur requête %s: HTTP %s", url, response.status)
                    return None
                return await response.json()
        except Exception as e:
            _LOGGER.error("Erreur requête %s: %s", url, e)
            return None

    async def get_plants(self) -> list[dict]:
        """Récupérer la liste des installations."""
        result = await self._get(
            f"{BASE_URL}/plant/list2?page=1&page_size=10&refresh=true"
        )
        if not result:
            return []
        return result.get("data", [])

    async def get_layouts(self, plant_id: str) -> list[dict]:
        """Récupérer les layouts d'une installation."""
        result = await self._get(f"{BASE_URL}/plant/{plant_id}/layout")
        if not result:
            return []
        return result.get("data", [])

    async def get_monitor_data(self, plant_id: str) -> dict | None:
        """Récupérer les données globales temps réel."""
        result = await self._get(
            f"{BASE_URL}/plant/{plant_id}/monitor?refresh=true"
        )
        if not result:
            return None
        return result.get("data")

    async def get_panel_data(self, plant_id: str, layout_id: str) -> dict | None:
        """Récupérer les données par panneau (pv1power, pv2power, etc.)."""
        today = date.today().isoformat()
        url = (
            f"{BASE_URL}/plant/{plant_id}/layout/{layout_id}/datav2"
            f"?start_date={today}&end_date={today}&type=day"
        )
        result = await self._get(url)
        if not result:
            return None

        data_points = result.get("data", [])
        if not data_points:
            return None

        for point in reversed(data_points):
            monitors = point.get("inv_monitor", [])
            if monitors:
                monitor = monitors[0]
                if monitor.get("pvtotal", 0) > 0:
                    return monitor

        last = data_points[-1]
        monitors = last.get("inv_monitor", [])
        if monitors:
            return monitors[0]

        return None

    async def get_all_data(self, plant_id: str, layout_id: str) -> dict:
        """Récupérer toutes les données en une fois."""
        monitor = await self.get_monitor_data(plant_id) or {}
        panel = await self.get_panel_data(plant_id, layout_id) or {}

        return {
            # Données globales
            "e_today": monitor.get("e_today", 0.0),
            "e_total": monitor.get("e_total", 0.0),
            "e_month": monitor.get("e_month", 0.0),
            "e_year": monitor.get("e_year", 0.0),
            "power_pv": monitor.get("power_pv", 0.0),
            "power_load": monitor.get("power_load", 0.0),
            "meter_power": monitor.get("meter_power", 0.0),
            "w_cha": monitor.get("w_cha", 0.0),
            "soc": monitor.get("soc", 0.0),
            "total_co2": monitor.get("total_co2", 0.0),
            "total_tree": monitor.get("total_tree", 0.0),
            # Données par panneau
            "pv1power": panel.get("pv1power", 0.0),
            "pv1v": panel.get("pv1v", 0.0),
            "pv1a": panel.get("pv1a", 0.0),
            "pv2power": panel.get("pv2power", 0.0),
            "pv2v": panel.get("pv2v", 0.0),
            "pv2a": panel.get("pv2a", 0.0),
            "pvtotal": panel.get("pvtotal", 0.0),
            "phvpha": panel.get("phvpha", 0.0),
            "hz": panel.get("hz", 0.0),
            "tmpamb": panel.get("tmpamb", 0.0),
        }
