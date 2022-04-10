"""Timer class to handle instable Philips CoaP API"""
import asyncio
import logging


_LOGGER = logging.getLogger(__name__)

class Timer:
    _in_callback: bool = False
    _auto_restart:bool = False

    def __init__(self, timeout, callback, autostart=True):
        self._timeout = timeout
        self._callback = callback
        self._task = None
        
        if autostart:
            self.start()

    async def _job(self):
        while True:
            try:
                self._in_callback = False
                _LOGGER.debug(f"Starting Timer {self._timeout}s.")
                await asyncio.sleep(self._timeout)
                self._in_callback = True
                _LOGGER.info("Calling timeout callback...")
                await self._callback()
                _LOGGER.debug("Timeout callback finished!")
            except asyncio.exceptions.CancelledError:
                _LOGGER.debug("Timer cancelled")
            except:
                _LOGGER.exception("Timer callback failure")
            self._in_callback = False
            if not self._auto_restart:
                break

    def setTimeout(self, timeout):
        self._timeout = timeout

    def _cancel(self):
        if self._in_callback:
            raise Exception("Timedout too late to cancel!")
        if self._task is not None:
            self._task.cancel()

    def reset(self):
        self._cancel()
        self.start()

    def start(self):
        if self._task is None:
            self._task = asyncio.ensure_future(self._job())