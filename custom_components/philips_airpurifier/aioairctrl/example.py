import asyncio

from .coap_client import CoAPClient


async def main():
    client = await CoAPClient.create(host="192.168.10.58")
    print("GETTING STATUS")
    print(await client.get_status())
    print("OBSERVING")
    async for s in client.observe_status():
        print("GOT STATE")
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
