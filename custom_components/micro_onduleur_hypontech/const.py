"""Constants for Micro Onduleur Hypontech integration."""

from logging import Logger, getLogger

DOMAIN = "micro_onduleur_hypontech"
LOGGER: Logger = getLogger(__package__)

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PLANT_ID = "plant_id"
CONF_LAYOUT_ID = "layout_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60  # 1 minute

BASE_URL = "https://api.hypon.cloud/v2"
TOKEN_VALIDITY = 3600

# Clés de traduction
TRANSLATION_KEY_CONNECTION_ERROR = "connection_error"
