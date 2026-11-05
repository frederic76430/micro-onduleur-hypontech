"""Client de l'API cloud Hypontech (hypon.cloud)."""

from __future__ import annotations

from datetime import date
from time import time
from typing import Any

import aiohttp

from .const import BASE_URL, LOGGER, REQUEST_TIMEOUT, TOKEN_VALIDITY


class HypontechError(Exception):
    """Erreur générique de l'API Hypontech."""


class HypontechConnectionError(HypontechError):
    """Le cloud ne répond pas ou répond une erreur."""


class HypontechAuthError(HypontechError):
    """Identifiants refusés."""


class MicroOnduleurHypontechAPI:
    """Client API Hypontech : données globales et par panneau.

    Toutes les méthodes lèvent une exception en cas d'échec : elles ne renvoient
    jamais de valeur par défaut (0) qui pourrait être prise pour une vraie mesure.
    """

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token = ""
        self._token_expires_at = 0.0

    # ---------------------------------------------------------------- connexion
    async def connect(self, force: bool = False) -> None:
        """Se connecter (ou réutiliser le jeton encore valable)."""
        if not force and self._token and self._token_expires_at > time():
            return
        try:
            async with self._session.post(
                f"{BASE_URL}/login",
                json={"username": self._username, "password": self._password},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                if response.status in (401, 403):
                    raise HypontechAuthError(f"HTTP {response.status}")
                if response.status != 200:
                    raise HypontechConnectionError(f"Connexion : HTTP {response.status}")
                result = await response.json(content_type=None)
        except HypontechError:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise HypontechConnectionError(f"Connexion : {err}") from err

        token = (result or {}).get("data", {}) if isinstance(result, dict) else {}
        token = token.get("token") if isinstance(token, dict) else None
        if not token:
            # Réponse 200 sans jeton : le cloud refuse les identifiants
            raise HypontechAuthError("Jeton absent de la réponse")
        self._token = token
        self._token_expires_at = time() + TOKEN_VALIDITY
        LOGGER.debug("Connexion Hypontech réussie")

    async def _get(self, path: str) -> Any:
        """GET authentifié. Se reconnecte une fois si le jeton a expiré (401)."""
        await self.connect()
        for tentative in (1, 2):
            try:
                async with self._session.get(
                    f"{BASE_URL}{path}",
                    headers={"authorization": f"Bearer {self._token}"},
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as response:
                    if response.status == 401 and tentative == 1:
                        LOGGER.debug("Jeton expiré, nouvelle connexion")
                        await self.connect(force=True)
                        continue
                    if response.status == 401:
                        raise HypontechAuthError("HTTP 401 après reconnexion")
                    if response.status != 200:
                        raise HypontechConnectionError(f"{path} : HTTP {response.status}")
                    result = await response.json(content_type=None)
            except HypontechError:
                raise
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                raise HypontechConnectionError(f"{path} : {err}") from err
            if not isinstance(result, dict):
                raise HypontechConnectionError(f"{path} : réponse inattendue")
            return result.get("data")
        raise HypontechConnectionError(f"{path} : échec")  # pragma: no cover

    # ---------------------------------------------------------------- données
    async def get_plants(self) -> list[dict]:
        """Liste des installations du compte."""
        return await self._get("/plant/list2?page=1&page_size=50&refresh=true") or []

    async def get_layouts(self, plant_id: str) -> list[dict]:
        """Agencements (layouts) d'une installation."""
        return await self._get(f"/plant/{plant_id}/layout") or []

    async def get_monitor_data(self, plant_id: str) -> dict:
        """Données globales temps réel."""
        data = await self._get(f"/plant/{plant_id}/monitor?refresh=true")
        if not isinstance(data, dict):
            raise HypontechConnectionError("monitor : données absentes")
        return data

    async def get_panel_data(self, plant_id: str, layout_id: str, jour: date) -> dict | None:
        """Dernière mesure par panneau du jour (pv1power, pv2power…), None si aucune."""
        points = await self._get(
            f"/plant/{plant_id}/layout/{layout_id}/datav2"
            f"?start_date={jour.isoformat()}&end_date={jour.isoformat()}&type=day"
        ) or []
        dernier = None
        for point in points:
            monitors = point.get("inv_monitor") or []
            if monitors:
                dernier = monitors[0]
        # Mesure la plus récente avec de la production, sinon la toute dernière
        for point in reversed(points):
            monitors = point.get("inv_monitor") or []
            if monitors and (monitors[0].get("pvtotal") or 0) > 0:
                return monitors[0]
        return dernier

    async def _energy(self, path: str) -> float:
        data = await self._get(path)
        if not isinstance(data, dict) or data.get("pvkwh") is None:
            raise HypontechConnectionError(f"{path} : pvkwh absent")
        return float(data["pvkwh"])

    async def get_energy_month(self, plant_id: str, jour: date) -> float:
        """Production du mois (l'endpoint /monitor renvoie une valeur fausse pour e_month)."""
        return await self._energy(
            f"/plant/{plant_id}/energy2?type=month&month={jour.month:02d}&year={jour.year}"
        )

    async def get_energy_year(self, plant_id: str, jour: date) -> float:
        """Production de l'année."""
        return await self._energy(f"/plant/{plant_id}/energy2?type=year&year={jour.year}")
