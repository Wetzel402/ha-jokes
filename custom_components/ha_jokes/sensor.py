"""Jokes sensor platform."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import random
from typing import Any

import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_HEADERS_GEEKJOKES,
    API_HEADERS_ICANHAZDADJOKE,
    API_HEADERS_JOKEAPI,
    API_HEADERS_OFFICIAL,
    API_HEADERS_YOMAMA,
    API_URL_GEEKJOKES,
    API_URL_ICANHAZDADJOKE,
    API_URL_JOKEAPI_BASE,
    API_URL_OFFICIAL_BASE,
    API_URL_YOMAMA,
    ATTR_EXPLANATION,
    ATTR_JOKE,
    ATTR_JOKE_ID,
    ATTR_LAST_UPDATED,
    ATTR_REFRESH_INTERVAL,
    ATTR_SOURCE,
    DEFAULT_JOKEAPI_BLACKLIST,
    DEFAULT_JOKEAPI_CATEGORIES,
    DEFAULT_JOKEAPI_SAFE_MODE,
    DEFAULT_OFFICIAL_CATEGORIES,
    DEFAULT_PROVIDERS,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    JOKEAPI_BLACKLIST_FLAGS,
    JOKEAPI_CATEGORIES,
    OFFICIAL_CATEGORIES,
    PROVIDER_GEEKJOKES,
    PROVIDER_ICANHAZDADJOKE,
    PROVIDER_JOKEAPI,
    PROVIDER_OFFICIAL,
    PROVIDER_YOMAMA,
    SENSOR_ICON,
    SENSOR_NAME,
    STATE_ERROR,
    STATE_OK,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Jokes sensor platform."""
    # Get coordinator from hass.data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create main joke sensor and explanation sensor
    async_add_entities([
        JokesSensor(coordinator, config_entry),
        JokeExplanationSensor(coordinator, config_entry),
    ], True)


class JokesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def _jokeapi_url(self) -> str:
        selected = [c for c in JOKEAPI_CATEGORIES if c in self._jokeapi_categories]
        path = "Any"
        if selected and selected != list(JOKEAPI_CATEGORIES):
            path = ",".join(selected)
        query = ["type=single"]
        if self._jokeapi_safe_mode:
            query.append("safe-mode")
        flags = [f for f in JOKEAPI_BLACKLIST_FLAGS if f in self._jokeapi_blacklist]
        if flags:
            query.append(f"blacklistFlags={','.join(flags)}")
        return f"{API_URL_JOKEAPI_BASE}/{path}?{'&'.join(query)}"

    def _official_url(self) -> str:
        selected = [c for c in OFFICIAL_CATEGORIES if c in self._official_categories]
        if not selected:
            selected = list(OFFICIAL_CATEGORIES)
        joke_type = random.choice(selected)
        return f"{API_URL_OFFICIAL_BASE}/jokes/{joke_type}/random"

    def _build_provider_configs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": PROVIDER_ICANHAZDADJOKE,
                "url": API_URL_ICANHAZDADJOKE,
                "headers": API_HEADERS_ICANHAZDADJOKE,
                "parser": self._parse_icanhazdadjoke,
            },
            {
                "name": PROVIDER_JOKEAPI,
                "url": self._jokeapi_url,
                "headers": API_HEADERS_JOKEAPI,
                "parser": self._parse_jokeapi,
            },
            {
                "name": PROVIDER_OFFICIAL,
                "url": self._official_url,
                "headers": API_HEADERS_OFFICIAL,
                "parser": self._parse_official_joke_api,
            },
            {
                "name": PROVIDER_GEEKJOKES,
                "url": API_URL_GEEKJOKES,
                "headers": API_HEADERS_GEEKJOKES,
                "parser": self._parse_geekjokes,
            },
            {
                "name": PROVIDER_YOMAMA,
                "url": API_URL_YOMAMA,
                "headers": API_HEADERS_YOMAMA,
                "parser": self._parse_yomama,
            },
        ]

    def __init__(
        self,
        hass: HomeAssistant,
        refresh_interval: int,
        enabled_providers: list[str],
        jokeapi_categories: list[str] | None = None,
        jokeapi_blacklist: list[str] | None = None,
        jokeapi_safe_mode: bool = DEFAULT_JOKEAPI_SAFE_MODE,
        official_categories: list[str] | None = None,
    ) -> None:
        self.platforms = []
        self._refresh_interval = refresh_interval
        self._enabled_providers = enabled_providers if enabled_providers else DEFAULT_PROVIDERS
        self._jokeapi_categories = jokeapi_categories or DEFAULT_JOKEAPI_CATEGORIES
        self._jokeapi_blacklist = (
            jokeapi_blacklist if jokeapi_blacklist is not None else DEFAULT_JOKEAPI_BLACKLIST
        )
        self._jokeapi_safe_mode = jokeapi_safe_mode
        self._official_categories = official_categories or DEFAULT_OFFICIAL_CATEGORIES
        self._providers = [
            p for p in self._build_provider_configs() if p["name"] in self._enabled_providers
        ]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=refresh_interval),
        )

    def _parse_icanhazdadjoke(self, data: dict) -> dict[str, Any]:
        """Parse icanhazdadjoke.com response."""
        return {
            ATTR_JOKE: data.get("joke", ""),
            ATTR_JOKE_ID: data.get("id", ""),
            ATTR_SOURCE: "icanhazdadjoke.com",
        }

    def _parse_jokeapi(self, data: dict) -> dict[str, Any]:
        if data.get("error"):
            raise ValueError(data.get("message", "JokeAPI returned an error"))
        joke_text = data.get("joke", "")
        joke_id = str(data.get("id", ""))
        return {
            ATTR_JOKE: joke_text,
            ATTR_JOKE_ID: joke_id,
            ATTR_SOURCE: "jokeapi.dev",
        }

    def _parse_official_joke_api(self, data: dict | list) -> dict[str, Any]:
        if isinstance(data, list):
            if not data:
                raise ValueError("Official Joke API returned no jokes")
            data = data[0]
        setup = data.get("setup", "")
        punchline = data.get("punchline", "")
        joke_text = f"{setup} {punchline}" if setup and punchline else ""
        joke_id = str(data.get("id", ""))
        return {
            ATTR_JOKE: joke_text,
            ATTR_JOKE_ID: joke_id,
            ATTR_SOURCE: "official-joke-api.appspot.com",
        }

    def _parse_geekjokes(self, data: dict) -> dict[str, Any]:
        """Parse Geek Jokes response."""
        # Geek Jokes returns a single 'joke' field and no id
        return {
            ATTR_JOKE: data.get("joke", ""),
            ATTR_JOKE_ID: "",
            ATTR_SOURCE: "geek-jokes.sameerkumar.website",
        }

    def _parse_yomama(self, data: dict) -> dict[str, Any]:
        """Parse Yo Mama Jokes response (adult/roast humour)."""
        # Yo Mama returns a 'joke' field (plus a 'category') and no id
        return {
            ATTR_JOKE: data.get("joke", ""),
            ATTR_JOKE_ID: "",
            ATTR_SOURCE: "yomama-jokes.com",
        }

    async def _fetch_from_provider(
        self, session: aiohttp.ClientSession, provider: dict
    ) -> dict[str, Any] | None:
        url = provider["url"]() if callable(provider["url"]) else provider["url"]
        try:
            async with session.get(url, headers=provider["headers"]) as response:
                if response.status != 200:
                    _LOGGER.warning(
                        "Provider %s returned status %s",
                        provider["name"],
                        response.status,
                    )
                    return None
                data = await response.json()
                parsed = provider["parser"](data)
                if not parsed or not parsed.get(ATTR_JOKE):
                    _LOGGER.warning(
                        "Provider %s returned an empty joke", provider["name"]
                    )
                    return None
                _LOGGER.debug("Successfully fetched joke from %s", provider["name"])
                return parsed
        except Exception as err:
            _LOGGER.warning(
                "Error fetching from provider %s: %s", provider["name"], err
            )
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        providers = self._providers.copy()
        random.shuffle(providers)
        _LOGGER.debug("Attempting to fetch joke from providers in random order")
        session = async_get_clientsession(self.hass)
        try:
            async with async_timeout.timeout(30):
                for provider in providers:
                    result = await self._fetch_from_provider(session, provider)
                    if result:
                        result[ATTR_LAST_UPDATED] = datetime.now().isoformat()
                        result[ATTR_REFRESH_INTERVAL] = self._refresh_interval
                        return result
                raise UpdateFailed("All joke providers failed to respond")
        except asyncio.TimeoutError as exception:
            raise UpdateFailed(
                f"Timeout communicating with joke APIs: {exception}"
            ) from exception
        except UpdateFailed:
            raise
        except Exception as exception:
            raise UpdateFailed(
                f"Error communicating with joke APIs: {exception}"
            ) from exception


class JokesSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Jokes sensor."""

    def __init__(
        self,
        coordinator: JokesDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = SENSOR_NAME
        self._attr_icon = SENSOR_ICON
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.last_update_success:
            return STATE_OK
        return STATE_ERROR

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        
        return {
            ATTR_JOKE: self.coordinator.data.get(ATTR_JOKE, ""),
            ATTR_JOKE_ID: self.coordinator.data.get(ATTR_JOKE_ID, ""),
            ATTR_SOURCE: self.coordinator.data.get(ATTR_SOURCE, ""),
            ATTR_LAST_UPDATED: self.coordinator.data.get(ATTR_LAST_UPDATED, ""),
            ATTR_REFRESH_INTERVAL: self.coordinator.data.get(ATTR_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL),
        }


class JokeExplanationSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Joke Explanation sensor."""

    def __init__(
        self,
        coordinator: JokesDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = "Joke Explanation"
        self._attr_icon = "mdi:comment-question-outline"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_explanation"
        self._explanation = None
        # Which joke the current explanation belongs to, so we can drop it once the
        # joke rotates. Prefer joke_id; fall back to the joke text for providers that
        # do not supply an id.
        self._explained_joke_key = None

    def _current_joke_key(self) -> str | None:
        """Identify the joke the coordinator is currently serving."""
        data = self.coordinator.data or {}
        return data.get(ATTR_JOKE_ID) or data.get(ATTR_JOKE) or None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Discard the explanation when it no longer matches the current joke.

        Without this the sensor keeps reporting "Explained" with the previous joke's
        explanation forever, so any dashboard showing it displays an explanation for a
        joke that is no longer on screen.
        """
        if self._explanation:
            current = self._current_joke_key()
            # `current is not None` matters: a failed refresh leaves coordinator.data
            # empty, and we must not wipe a perfectly good explanation because of it.
            # A None _explained_joke_key still clears here, so messages produced when no
            # joke was available disappear once a real joke arrives.
            if current is not None and current != self._explained_joke_key:
                _LOGGER.debug("Joke rotated; clearing the stale explanation")
                self._explanation = None
                self._explained_joke_key = None
        super()._handle_coordinator_update()

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if self._explanation:
            return "Explained"
        return "Not Explained"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            ATTR_EXPLANATION: self._explanation or "No explanation available",
            # Lets a dashboard (or automation) tell which joke this explanation is for.
            ATTR_JOKE_ID: self._explained_joke_key or "",
        }

    async def async_explain_joke(self) -> None:
        """Explain the current joke using AI."""
        _LOGGER.info("=== Starting explain_joke service ===")
        # Find the joke sensor entity dynamically
        joke = None
        joke_key = None
        joke_entity_id = None
        
        # Search for the joke sensor entity
        for entity_id in self.hass.states.async_entity_ids("sensor"):
            if entity_id.startswith(f"sensor.{DOMAIN}_") and "explanation" not in entity_id:
                # This is likely our joke sensor
                state = self.hass.states.get(entity_id)
                if state and state.attributes.get(ATTR_JOKE):
                    joke = state.attributes.get(ATTR_JOKE)
                    joke_key = state.attributes.get(ATTR_JOKE_ID) or joke
                    joke_entity_id = entity_id
                    break
            elif entity_id == "sensor.joke":
                # Check for the main joke sensor by name
                state = self.hass.states.get(entity_id)
                if state and state.attributes.get(ATTR_JOKE):
                    joke = state.attributes.get(ATTR_JOKE)
                    joke_key = state.attributes.get(ATTR_JOKE_ID) or joke
                    joke_entity_id = entity_id
                    break
        
        if not joke:
            _LOGGER.warning("No joke available to explain")
            self._explanation = "No joke available to explain"
            self._explained_joke_key = None
            self.async_write_ha_state()
            return

        # Tie everything we set below (explanation *or* error message) to this joke, so it
        # is discarded as soon as the joke rotates.
        self._explained_joke_key = joke_key
        
        # Check if ai_task service is available
        if not self.hass.services.has_service("ai_task", "generate_data"):
            _LOGGER.error("ai_task.generate_data service is not available. Please configure an AI provider.")
            self._explanation = "AI service not configured. Please configure an AI provider in Home Assistant."
            self.async_write_ha_state()
            return
        
        try:
            # Call the ai_task.generate_data service with correct parameters
            _LOGGER.info("Calling ai_task.generate_data for joke from %s", joke_entity_id)
            _LOGGER.info("Joke to explain: %s", joke[:100])
            response = await self.hass.services.async_call(
                "ai_task",
                "generate_data",
                {
                    "task_name": "explain_joke",
                    "instructions": f"Explain the following joke in plain language:\n{joke}",
                },
                blocking=True,
                return_response=True,
            )
            
            _LOGGER.info("AI service response: %s", response)
            _LOGGER.info("Response type: %s", type(response))
            
            if response:
                # The azure_ai_tasks service returns a dict with 'data' key containing the text
                if isinstance(response, dict):
                    self._explanation = response.get("data", "Unable to generate explanation")
                else:
                    self._explanation = str(response)
            else:
                self._explanation = "No response from AI service"
                
            self.async_write_ha_state()
            _LOGGER.debug("Joke explanation generated successfully")
            
        except Exception as err:
            _LOGGER.error("Failed to generate joke explanation: %s", err)
            self._explanation = f"Error: {str(err)}"
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Store reference to this entity in hass.data for service calls
        if DOMAIN in self.hass.data and self._config_entry.entry_id in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][self._config_entry.entry_id]["explanation_entity"] = self
