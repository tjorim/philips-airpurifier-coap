import logging
import asyncio
import binascii
import os
import sys
import hashlib
import json

from aiocoap import (
    Context,
    Message,
    GET,
    POST,
    PUT,
    NON,
)

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.getLogger("coap").setLevel(logging.DEBUG)


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
        logger.debug(f"Setting client-key: {client_key}")
        self._client_key = client_key

    def _get_client_key_next(self, store=True):
        client_key_next = (int(self._client_key, 16) + 1).to_bytes(4, byteorder="big").hex().upper()
        logger.debug(f"Generated next client-key: {self._client_key} -> {client_key_next}")
        if store:
            self._client_key = client_key_next
        return client_key_next

    def _decrypt_payload(self, payload_encrypted: str) -> str:
        logger.debug(f"decrypting: {payload_encrypted}")
        key = payload_encrypted[0:8]
        logger.debug(f"KEY: {len(key)} - {key}")
        ciphertext = payload_encrypted[8:-64]
        logger.debug(f"CIPHERTEXT: {len(ciphertext)} - {ciphertext}")
        digest = payload_encrypted[-64:]
        logger.debug(f"DIGEST: {digest}")
        digest_calculated = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        logger.debug(f"CALC: {digest_calculated}")
        if digest != digest_calculated:
            raise DigestMismatchException
        cipher = self._create_cipher(key)
        plaintext_padded = cipher.decrypt(bytes.fromhex(ciphertext))
        plaintext_unpadded = unpad(plaintext_padded, 16, style="pkcs7")
        return plaintext_unpadded.decode()

    def _encrypt_payload(self, payload: str) -> str:
        logger.debug(f"encrypting payload: {payload}")
        key = self._get_client_key_next()
        logger.debug(f"KEY: {key}")
        plaintext_padded = pad(payload.encode(), 16, style="pkcs7")
        logger.debug(f"p: {plaintext_padded}")
        cipher = self._create_cipher(key)
        ciphertext = cipher.encrypt(plaintext_padded).hex().upper()
        logger.debug(f"CIPHERTEXT: {ciphertext}")
        digest = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        logger.debug(f"DIGEST: {digest}")
        return key + ciphertext + digest

    async def _sync(self):
        sync_request = os.urandom(4).hex().upper()
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.SYNC_PATH}",
            payload=sync_request.encode()
        )
        logger.debug(f"Sending sync-request: {sync_request}")
        response = await self._client_context.request(request).response
        client_key = response.payload.decode()
        logger.debug(f"Received client-key: {client_key}")
        self._set_client_key(client_key)

    async def get_status(self):
        request = Message(
            code=GET,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}"
        )
        request.opt.observe = 0
        response = await self._client_context.request(request).response
        #  requester = self._client_context.request(request)
        #  print(dir(requester))
        #  response = await requester.response
        #  print(dir(response))
        payload_encrypted = response.payload.decode()
        payload = self._decrypt_payload(payload_encrypted)
        state_reported = json.loads(payload)
        return state_reported["state"]["reported"]

    async def observe_status(self):
        observer_got_exception = asyncio.Event()
        observer_responses = asyncio.Queue()

        def observation_errback(exception):
            observer_got_exception.set()

        def observation_callback(response):
            payload_encrypted = response.payload.decode()
            payload = self._decrypt_payload(payload_encrypted)
            state_reported = json.loads(payload)
            observer_responses.put_nowait(state_reported["state"]["reported"])

        request = Message(
            code=GET,
            uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}"
        )
        request.opt.observe = 0
        requester = self._client_context.request(request)
        requester.observation.register_errback(observation_errback)
        requester.observation.register_callback(observation_callback)
        response = await requester.response
        while not observer_got_exception.is_set():
            response = await observer_responses.get()
            yield response

    async def set_control_value(self, key, value):
        state_desired = {
            "state": {
                "desired": {
                    "CommandType": "app",
                    "DeviceId": "",
                    "EnduserId": "",
                    key: value,
                }
            }
        }
        payload = json.dumps(state_desired)
        payload_encrypted = self._encrypt_payload(payload)
        logger.debug("D: %s", self._decrypt_payload(payload_encrypted))
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.CONTROL_PATH}",
            payload=payload_encrypted.encode()
        )
        response = await self._client_context.request(request).response
        logger.debug("RESPONSE: %s", response.payload)


async def main():
    client = await CoAPClient.create(host="192.168.10.58")
    #  m = "55D0D47084C885DE58673F50E69D946F65F4CBDD12507405CA12D1AE10E86B1347DADAF3C89CCFE71EC956CE097AB1DD781CBFA97CEDAE4CF140DCB7DEBED859FB05CF5C7FE18516E01F789730064CE69EE114E27328CC3503208CF48D59B5374129B3052A19018549FCC02A8083F70C304816755B816A2A8B681D9358FA39FCC71C84F1"
    #  k = m[0:8]
    #  d = client._decrypt_payload(m)
    #  client._set_client_key("55D0D46F")
    #  e = client._encrypt_payload(d)
    #  print("M:", m)
    #  print("K:",k)
    #  print(d)
    #  print(e)
    #  print(m == e)
    #  async for s in client.observe_status():
    #      print(s)
    #  client._set_client_key("2ED7B666")
    #  await client.set_control_value("pwr", "1")
    print("GETTING STATUS")
    print(await client.get_status())
    print("OBSERVING")
    async for s in client.observe_status():
        print("GOT STATE")
    await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
