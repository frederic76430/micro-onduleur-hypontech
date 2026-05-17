"""Constants for Micro Onduleur Hypontech integration."""

DOMAIN = "micro_onduleur_hypontech"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PLANT_ID = "plant_id"
CONF_LAYOUT_ID = "layout_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

BASE_URL = "https://api.hypon.cloud/v2"
TOKEN_VALIDITY = 3600
