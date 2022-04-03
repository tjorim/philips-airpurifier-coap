from __future__ import annotations

from typing import Any, Callable

import logging
import asyncio
from asyncio.tasks import Task

from aioairctrl import CoAPClient
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class Coordinator:
    def __init__(self, client: CoAPClient) -> None:
        self.client = client

        # It's None before the first successful update.
        # Components should call async_first_refresh  to make sure the first
        # update was successful. Set type to just DeviceStatus to remove
        # annoying checks that status is not None when it was already checked
        # during setup.
        self.status: DeviceStatus = None  # type: ignore[assignment]

        self._listeners: list[CALLBACK_TYPE] = []
        self._task: Task | None = None

    async def async_first_refresh(self) -> None:
        try:
            self.status = await self.client.get_status()
        except Exception as ex:
            raise ConfigEntryNotReady from ex

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> Callable[[], None]:
        """Listen for data updates."""
        start_observing = not self._listeners

        self._listeners.append(update_callback)

        if start_observing:
            self._start_observing()

        @callback
        def remove_listener() -> None:
            """Remove update listener."""
            self.async_remove_listener(update_callback)

        return remove_listener

    @callback
    def async_remove_listener(self, update_callback) -> None:
        """Remove data update."""
        self._listeners.remove(update_callback)

        if not self._listeners and self._task:
            self._task.cancel()
            self._task = None

    async def _async_observe_status(self) -> None:
        async for status in self.client.observe_status():
            _LOGGER.debug("Status update: %s", status)
            self.status = status
            for update_callback in self._listeners:
                update_callback()

    def _start_observing(self) -> None:
        """Schedule state observation."""
        if self._task:
            self._task.cancel()
            self._task = None
        self._task = asyncio.create_task(self._async_observe_status())


class PhilipsEntity(Entity):
    def __init__(self, coordinator: Coordinator) -> None:
        super().__init__()
        _LOGGER.debug("PhilipsEntity __init__ called")
        _LOGGER.debug(f"coordinator.status is: {coordinator.status}")
        self.coordinator = coordinator
        self._serialNumber = coordinator.status["DeviceId"]
        self._name = coordinator.status["name"]
        self._modelName = coordinator.status["modelid"]
        self._firmware = coordinator.status["WifiVersion"]
        self._manufacturer = "Philips"

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._serialNumber)
            },
            "name": self._name,
            "model": self._modelName,
            "manufacturer": self._manufacturer,
            "sw_version": self._firmware,
        }

    @property
    def available(self):
        return self.coordinator.status is not None

    @property
    def _device_status(self) -> dict[str, Any]:
        return self.coordinator.status

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
