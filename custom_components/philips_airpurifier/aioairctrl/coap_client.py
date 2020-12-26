import hashlib
import json
import logging
import os

from . import aiocoap_monkeypatch  # noqa: F401
from aiocoap import (
    Context,
    GET,
    Message,
    NON,
    POST,
)

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


logger = logging.getLogger(__name__)


class DigestMismatchException(Exception):
    pass


class CoAPClient:
    SECRET_KEY = "JiangPan"
    STATUS_PATH = "/sys/dev/status"
    CONTROL_PATH = "/sys/dev/control"
    SYNC_PATH = "/sys/dev/sync"

    def __init__(self, host, port=5683):
        self.host = host
        self.port = port
        self._client_context = None
        self._client_key = None

    async def _init(self):
        self._client_context = await Context.create_client_context()
        await self._sync()

    @classmethod
    async def create(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        await obj._init()
        return obj

    async def shutdown(self) -> None:
        if self._client_context:
            await self._client_context.shutdown()

    def _create_cipher(self, key: str):
        key_and_iv = hashlib.md5((self.SECRET_KEY + key).encode()).hexdigest().upper()
        half_keylen = len(key_and_iv) // 2
        secret_key = key_and_iv[0:half_keylen]
        iv = key_and_iv[half_keylen:]
        cipher = AES.new(
            key=secret_key.encode(),
            mode=AES.MODE_CBC,
            iv=iv.encode(),
        )
        return cipher

    def _set_client_key(self, client_key):
        self._client_key = client_key

    def _get_client_key_next(self, store=True):
        client_key_next = (int(self._client_key, 16) + 1).to_bytes(4, byteorder="big").hex().upper()
        if store:
            self._client_key = client_key_next
        return client_key_next

    def _decrypt_payload(self, payload_encrypted: str) -> str:
        key = payload_encrypted[0:8]
        ciphertext = payload_encrypted[8:-64]
        digest = payload_encrypted[-64:]
        digest_calculated = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        if digest != digest_calculated:
            raise DigestMismatchException
        cipher = self._create_cipher(key)
        plaintext_padded = cipher.decrypt(bytes.fromhex(ciphertext))
        plaintext_unpadded = unpad(plaintext_padded, 16, style="pkcs7")
        return plaintext_unpadded.decode()

    def _encrypt_payload(self, payload: str) -> str:
        key = self._get_client_key_next()
        plaintext_padded = pad(payload.encode(), 16, style="pkcs7")
        cipher = self._create_cipher(key)
        ciphertext = cipher.encrypt(plaintext_padded).hex().upper()
        digest = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        return key + ciphertext + digest

    async def _sync(self):
        logger.debug("syncing")
        sync_request = os.urandom(4).hex().upper()
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.SYNC_PATH}",
            payload=sync_request.encode(),
        )
        response = await self._client_context.request(request).response
        client_key = response.payload.decode()
        logger.debug("synced: %s", client_key)
        self._set_client_key(client_key)

    async def get_status(self):
        logger.debug("retrieving status")
        request = Message(
            code=GET, mtype=NON, uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}"
        )
        request.opt.observe = 0
        response = await self._client_context.request(request).response
        payload_encrypted = response.payload.decode()
        payload = self._decrypt_payload(payload_encrypted)
        logger.debug("status: %s", payload)
        state_reported = json.loads(payload)
        return state_reported["state"]["reported"]

    async def observe_status(self):
        logger.debug("observing status")
        request = Message(code=GET, uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}")
        request.opt.observe = 0
        requester = self._client_context.request(request)
        async for response in requester.observation:
            payload_encrypted = response.payload.decode()
            payload = self._decrypt_payload(payload_encrypted)
            logger.debug("observation status: %s", payload)
            status = json.loads(payload)
            yield status["state"]["reported"]

    async def set_control_value(self, key, value, retry_count=5, resync=True) -> None:
        await self.set_control_values(data={key: value}, retry_count=retry_count, resync=resync)

    async def set_control_values(self, data: dict, retry_count=5, resync=True) -> None:
        state_desired = {
            "state": {
                "desired": {
                    "CommandType": "app",
                    "DeviceId": "",
                    "EnduserId": "",
                    **data,
                }
            }
        }
        payload = json.dumps(state_desired)
        logger.debug("REQUEST: %s", payload)
        payload_encrypted = self._encrypt_payload(payload)
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.CONTROL_PATH}",
            payload=payload_encrypted.encode(),
        )
        response = await self._client_context.request(request).response
        logger.debug("RESPONSE: %s", response.payload)
        result = json.loads(response.payload)
        if result.get("status") != "success" and resync:
            logger.debug("set_control_value failed. resyncing...")
            await self._sync()
        if result.get("status") != "success" and retry_count > 0:
            logger.debug("set_control_value failed. retrying...")
            await self.set_control_values(data, retry_count - 1, resync)
        elif result.get("status") != "success":
            logger.error("set_control_value failed: %s", data)
