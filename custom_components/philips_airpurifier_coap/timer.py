"""Timer class to handle instable Philips CoaP API"""
import asyncio
import logging


_LOGGER = logging.getLogger(__name__)

class CallbackRunningException(Exception):
    pass

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
            except asyncio.exceptions.CancelledError as e:
                _LOGGER.debug(f"Timer cancelled: {e.args}")
                break
            except RuntimeError:
                try:
                    #Ensure that the runtime error, is because hass is going down!
                    asyncio.get_running_loop()
                except RuntimeError:
                    #Yes seems like hass is going down, stepping out
                    _LOGGER.warning("RuntimeError! Stopping Timer...")
                    self._auto_restart = False
                    self._task = None
                    return
            except:
                _LOGGER.exception("Timer callback failure")
            self._in_callback = False
            if not self._auto_restart:
                break

    def setTimeout(self, timeout):
        self._timeout = timeout
        # Set new Timeout immediatly effective
        self.reset()

    def _cancel(self, msg="STOP"):
        if self._in_callback:
            raise CallbackRunningException("Timedout too late to cancel!")
        if self._task is not None:
            self._task.cancel(msg=msg)
            self._task = None

    def reset(self):
        #_LOGGER.debug("Cancel current timer...")
        try:
            self._cancel(msg="RESET")
        except CallbackRunningException:
            pass
        #_LOGGER.debug("Staring new timer...")
        self.start()

    def start(self):
        if self._task is None:
            self._task = asyncio.ensure_future(self._job())