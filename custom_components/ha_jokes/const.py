"""Constants for the Jokes integration."""

DOMAIN = "ha_jokes"
NAME = "Jokes"
VERSION = "1.7.1"

API_URL_ICANHAZDADJOKE = "https://icanhazdadjoke.com"
API_HEADERS_ICANHAZDADJOKE = {
    "Accept": "application/json",
    "User-Agent": "Home Assistant Jokes Integration",
}

API_URL_JOKEAPI_BASE = "https://v2.jokeapi.dev/joke"
API_HEADERS_JOKEAPI = {
    "Accept": "application/json",
    "User-Agent": "Home Assistant Jokes Integration",
}

API_URL_OFFICIAL_BASE = "https://official-joke-api.appspot.com"
API_HEADERS_OFFICIAL = {
    "Accept": "application/json",
    "User-Agent": "Home Assistant Jokes Integration",
}

API_URL_GEEKJOKES = "https://geek-jokes.sameerkumar.website/api?format=json"
API_HEADERS_GEEKJOKES = {
    "Accept": "application/json",
    "User-Agent": "Home Assistant Jokes Integration",
}

API_URL_YOMAMA = "https://www.yomama-jokes.com/api/v1/jokes/random/"
API_HEADERS_YOMAMA = {
    "Accept": "application/json",
    "User-Agent": "Home Assistant Jokes Integration",
}

API_URL = API_URL_ICANHAZDADJOKE
API_HEADERS = API_HEADERS_ICANHAZDADJOKE

DEFAULT_REFRESH_INTERVAL = 5
MIN_REFRESH_INTERVAL = 1
MAX_REFRESH_INTERVAL = 1440

SENSOR_NAME = "Joke"
SENSOR_ICON = "mdi:emoticon-happy-outline"

CONF_REFRESH_INTERVAL = "refresh_interval"
CONF_PROVIDERS = "providers"
CONF_JOKEAPI_CATEGORIES = "jokeapi_categories"
CONF_JOKEAPI_BLACKLIST = "jokeapi_blacklist"
CONF_JOKEAPI_SAFE_MODE = "jokeapi_safe_mode"
CONF_OFFICIAL_CATEGORIES = "official_categories"

ATTR_JOKE = "joke"
ATTR_JOKE_ID = "joke_id"
ATTR_LAST_UPDATED = "last_updated"
ATTR_REFRESH_INTERVAL = "refresh_interval"
ATTR_SOURCE = "source"
ATTR_CATEGORY = "category"
ATTR_EXPLANATION = "explanation"

PROVIDER_ICANHAZDADJOKE = "icanhazdadjoke"
PROVIDER_JOKEAPI = "jokeapi"
PROVIDER_OFFICIAL = "official_joke_api"
PROVIDER_GEEKJOKES = "geek_jokes"
PROVIDER_YOMAMA = "yomama_jokes"

DEFAULT_PROVIDERS = [
    PROVIDER_ICANHAZDADJOKE,
    PROVIDER_JOKEAPI,
    PROVIDER_OFFICIAL,
]

JOKEAPI_CATEGORIES = [
    "Programming",
    "Misc",
    "Dark",
    "Pun",
    "Spooky",
    "Christmas",
]

JOKEAPI_BLACKLIST_FLAGS = [
    "nsfw",
    "religious",
    "political",
    "racist",
    "sexist",
    "explicit",
]

OFFICIAL_CATEGORIES = [
    "general",
    "knock-knock",
    "programming",
    "dad",
]

DEFAULT_JOKEAPI_CATEGORIES = list(JOKEAPI_CATEGORIES)
DEFAULT_JOKEAPI_BLACKLIST = list(JOKEAPI_BLACKLIST_FLAGS)
DEFAULT_JOKEAPI_SAFE_MODE = True
DEFAULT_OFFICIAL_CATEGORIES = list(OFFICIAL_CATEGORIES)

STATE_OK = "OK"
STATE_ERROR = "Error"
