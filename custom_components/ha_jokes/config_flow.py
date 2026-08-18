"""Config flow for Jokes integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_JOKEAPI_BLACKLIST,
    CONF_JOKEAPI_CATEGORIES,
    CONF_JOKEAPI_SAFE_MODE,
    CONF_OFFICIAL_CATEGORIES,
    CONF_PROVIDERS,
    CONF_REFRESH_INTERVAL,
    DEFAULT_JOKEAPI_BLACKLIST,
    DEFAULT_JOKEAPI_CATEGORIES,
    DEFAULT_JOKEAPI_SAFE_MODE,
    DEFAULT_OFFICIAL_CATEGORIES,
    DEFAULT_PROVIDERS,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    JOKEAPI_BLACKLIST_FLAGS,
    JOKEAPI_CATEGORIES,
    MAX_REFRESH_INTERVAL,
    MIN_REFRESH_INTERVAL,
    NAME,
    OFFICIAL_CATEGORIES,
    PROVIDER_GEEKJOKES,
    PROVIDER_ICANHAZDADJOKE,
    PROVIDER_JOKEAPI,
    PROVIDER_OFFICIAL,
    PROVIDER_YOMAMA,
)


def _providers_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                PROVIDER_ICANHAZDADJOKE,
                PROVIDER_JOKEAPI,
                PROVIDER_OFFICIAL,
                PROVIDER_GEEKJOKES,
                PROVIDER_YOMAMA,
            ],
            multiple=True,
            mode=SelectSelectorMode.LIST,
            translation_key="providers",
        )
    )


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_REFRESH_INTERVAL): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_REFRESH_INTERVAL,
                    max=MAX_REFRESH_INTERVAL,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Required(CONF_PROVIDERS): _providers_selector(),
        }
    )


def _jokeapi_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_JOKEAPI_CATEGORIES): SelectSelector(
                SelectSelectorConfig(
                    options=list(JOKEAPI_CATEGORIES),
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                    translation_key="jokeapi_categories",
                )
            ),
            vol.Required(CONF_JOKEAPI_BLACKLIST): SelectSelector(
                SelectSelectorConfig(
                    options=list(JOKEAPI_BLACKLIST_FLAGS),
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                    translation_key="jokeapi_blacklist",
                )
            ),
            vol.Required(CONF_JOKEAPI_SAFE_MODE): BooleanSelector(),
        }
    )


def _official_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_OFFICIAL_CATEGORIES): SelectSelector(
                SelectSelectorConfig(
                    options=list(OFFICIAL_CATEGORIES),
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                    translation_key="official_categories",
                )
            ),
        }
    )


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(user_input)
    if CONF_REFRESH_INTERVAL in normalized:
        normalized[CONF_REFRESH_INTERVAL] = int(normalized[CONF_REFRESH_INTERVAL])
    return normalized


def _finalize_options(options: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_REFRESH_INTERVAL: int(
            options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        ),
        CONF_PROVIDERS: options.get(CONF_PROVIDERS, DEFAULT_PROVIDERS),
        CONF_JOKEAPI_CATEGORIES: options.get(
            CONF_JOKEAPI_CATEGORIES, DEFAULT_JOKEAPI_CATEGORIES
        ),
        CONF_JOKEAPI_BLACKLIST: options.get(
            CONF_JOKEAPI_BLACKLIST, DEFAULT_JOKEAPI_BLACKLIST
        ),
        CONF_JOKEAPI_SAFE_MODE: options.get(
            CONF_JOKEAPI_SAFE_MODE, DEFAULT_JOKEAPI_SAFE_MODE
        ),
        CONF_OFFICIAL_CATEGORIES: options.get(
            CONF_OFFICIAL_CATEGORIES, DEFAULT_OFFICIAL_CATEGORIES
        ),
    }


class JokesFlowMixin:
    def _init_flow_state(self, options=None) -> None:
        self._options = dict(options) if options else {}
        self._jokeapi_done = False
        self._official_done = False

    def _user_errors(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not user_input.get(CONF_PROVIDERS):
            errors[CONF_PROVIDERS] = "no_providers_selected"
        return errors

    def _jokeapi_errors(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not user_input.get(CONF_JOKEAPI_CATEGORIES):
            errors[CONF_JOKEAPI_CATEGORIES] = "no_jokeapi_categories"
        return errors

    def _official_errors(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not user_input.get(CONF_OFFICIAL_CATEGORIES):
            errors[CONF_OFFICIAL_CATEGORIES] = "no_official_categories"
        return errors

    async def _async_next_step(self) -> ConfigFlowResult:
        providers = self._options.get(CONF_PROVIDERS, [])
        if PROVIDER_JOKEAPI in providers and not self._jokeapi_done:
            return await self.async_step_jokeapi()
        if PROVIDER_OFFICIAL in providers and not self._official_done:
            return await self.async_step_official()
        return await self._async_finish()

    async def async_step_jokeapi(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._jokeapi_errors(user_input)
            if not errors:
                self._options.update(user_input)
                self._jokeapi_done = True
                return await self._async_next_step()

        suggested = {
            CONF_JOKEAPI_CATEGORIES: self._options.get(
                CONF_JOKEAPI_CATEGORIES, DEFAULT_JOKEAPI_CATEGORIES
            ),
            CONF_JOKEAPI_BLACKLIST: self._options.get(
                CONF_JOKEAPI_BLACKLIST, DEFAULT_JOKEAPI_BLACKLIST
            ),
            CONF_JOKEAPI_SAFE_MODE: self._options.get(
                CONF_JOKEAPI_SAFE_MODE, DEFAULT_JOKEAPI_SAFE_MODE
            ),
        }
        if user_input is not None:
            suggested.update(user_input)

        return self.async_show_form(
            step_id="jokeapi",
            data_schema=self.add_suggested_values_to_schema(
                _jokeapi_schema(), suggested
            ),
            errors=errors,
        )

    async def async_step_official(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._official_errors(user_input)
            if not errors:
                self._options.update(user_input)
                self._official_done = True
                return await self._async_next_step()

        suggested = {
            CONF_OFFICIAL_CATEGORIES: self._options.get(
                CONF_OFFICIAL_CATEGORIES, DEFAULT_OFFICIAL_CATEGORIES
            ),
        }
        if user_input is not None:
            suggested.update(user_input)

        return self.async_show_form(
            step_id="official",
            data_schema=self.add_suggested_values_to_schema(
                _official_schema(), suggested
            ),
            errors=errors,
        )

    async def _async_finish(self) -> ConfigFlowResult:
        raise NotImplementedError


class JokesConfigFlow(JokesFlowMixin, ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jokes."""

    VERSION = 2

    def __init__(self) -> None:
        super().__init__()
        self._init_flow_state()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize_user_input(user_input)
            errors = self._user_errors(user_input)
            if not errors:
                self._options.update(user_input)
                return await self._async_next_step()

        suggested = {
            CONF_REFRESH_INTERVAL: DEFAULT_REFRESH_INTERVAL,
            CONF_PROVIDERS: DEFAULT_PROVIDERS,
        }
        if user_input is not None:
            suggested.update(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_user_schema(), suggested),
            errors=errors,
        )

    async def _async_finish(self) -> ConfigFlowResult:
        return self.async_create_entry(
            title=NAME,
            data={},
            options=_finalize_options(self._options),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> JokesOptionsFlow:
        return JokesOptionsFlow()


class JokesOptionsFlow(JokesFlowMixin, OptionsFlowWithReload):
    """Handle options flow for Jokes."""

    def __init__(self) -> None:
        super().__init__()
        self._init_flow_state()
        self._copied = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._copied:
            self._init_flow_state(dict(self.config_entry.options))
            self._copied = True

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalize_user_input(user_input)
            errors = self._user_errors(user_input)
            if not errors:
                self._options.update(user_input)
                return await self._async_next_step()

        suggested = {
            CONF_REFRESH_INTERVAL: self._options.get(
                CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL
            ),
            CONF_PROVIDERS: self._options.get(CONF_PROVIDERS, DEFAULT_PROVIDERS),
        }
        if user_input is not None:
            suggested.update(user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(_user_schema(), suggested),
            errors=errors,
        )

    async def _async_finish(self) -> ConfigFlowResult:
        return self.async_create_entry(data=_finalize_options(self._options))
