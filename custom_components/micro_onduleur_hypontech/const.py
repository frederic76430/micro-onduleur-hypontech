"""Constantes de l'intégration Micro Onduleur Hypontech."""

from datetime import timedelta
from logging import Logger, getLogger

DOMAIN = "micro_onduleur_hypontech"
LOGGER: Logger = getLogger(__package__)

CONF_PLANT_ID = "plant_id"
CONF_LAYOUT_ID = "layout_id"

BASE_URL = "https://api.hypon.cloud/v2"
# Durée de vie supposée du jeton : on se reconnecte de toute façon dès que l'API répond 401
TOKEN_VALIDITY = 3600
REQUEST_TIMEOUT = 15

# Rythme des mises à jour
INTERVAL_DAY = timedelta(seconds=60)
INTERVAL_NIGHT = timedelta(minutes=30)
# Production mois / année : endpoints plus lents, une fois par heure suffit
INTERVAL_SLOW = timedelta(hours=1)
# Heures (heure locale de Home Assistant) pendant lesquelles l'onduleur peut produire
SOLAR_HOUR_START = 6
SOLAR_HOUR_END = 22
# Au-delà de cette durée sans réponse du cloud, les capteurs passent « indisponible »
# (avant, ils gardent leur dernière valeur connue)
MAX_STALE = timedelta(minutes=15)
