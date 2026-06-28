DOMAIN = "paxton_net2"
PLATFORMS = ["switch", "binary_sensor", "button", "sensor"]

CONF_BASE_URL = "base_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CLIENT_ID = "client_id"
CONF_VERIFY_SSL = "verify_ssl"
CONF_TOKEN_PATH = "token_path"
CONF_DOORS_PATH = "doors_path"
CONF_DOOR_STATUS_PATH = "door_status_path"
CONF_POLL_INTERVAL = "poll_interval"
CONF_DOOR_ID_FIELD = "door_id_field"
CONF_DOOR_NAME_FIELD = "door_name_field"

DEFAULT_TOKEN_PATH = "/api/v1/authorization/tokens"
DEFAULT_DOORS_PATH = "/api/v1/doors"
DEFAULT_DOOR_STATUS_PATH = "/api/v1/doors/status"
DEFAULT_HOLD_OPEN_PATH = "/api/v1/commands/door/holdopen"
DEFAULT_CLOSE_PATH = "/api/v1/commands/door/close"
DEFAULT_POLL_INTERVAL = 30
DEFAULT_DOOR_ID_FIELD = "Id"
DEFAULT_DOOR_NAME_FIELD = "Name"

DEFAULT_OPEN_PATH = "/api/v1/commands/door/open"

SERVER_SETTINGS_PATHS = {
    "features": "/api/v1/serverSettings/features",
    "properties": "/api/v1/serverSettings/properties",
    "product_type": "/api/v1/serverSettings/productType",
    "version": "/api/v1/serverSettings/version",
    "version_history": "/api/v1/serverSettings/version/history",
}

CONF_TOGGLE_DOOR_IDS = "toggle_door_ids"
CONF_RELAY2_DOOR_IDS = "relay2_door_ids"
DEFAULT_TOGGLE_DOOR_IDS = ""
DEFAULT_RELAY2_DOOR_IDS = ""
DEFAULT_CONTROL_PATH = "/api/v1/commands/door/control"

CONF_EXCLUDED_CONTROL_DOOR_IDS = "excluded_control_door_ids"
DEFAULT_EXCLUDED_CONTROL_DOOR_IDS = ""
