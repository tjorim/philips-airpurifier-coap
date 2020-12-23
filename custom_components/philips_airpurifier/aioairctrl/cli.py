import argparse
import asyncio
import json

from .coap_client import CoAPClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="sub-command help",
    )
    parser.add_argument(
        "-H",
        "--host",
        metavar="HOST",
        dest="host",
        type=str,
        required=True,
        help="Address of CoAP-device",
    )
    parser.add_argument(
        "-P",
        "--port",
        metavar="PORT",
        dest="port",
        type=int,
        required=False,
        default=5683,
        help="Port of CoAP-device (default: %(default)s)",
    )
    parser_status = subparsers.add_parser(
        "status",
        help="get status of device",
    )
    parser_status.add_argument(
        "-J",
        "--json",
        dest="json",
        action="store_true",
        help="Output status as JSON",
    )
    parser_status_observe = subparsers.add_parser(
        "status-observe",
        help="Observe status of device",
    )
    parser_status_observe.add_argument(
        "-J",
        "--json",
        dest="json",
        action="store_true",
        help="Output status as JSON",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    client = None
    try:
        client = await CoAPClient.create(host=args.host, port=args.port)
        if args.command == "status":
            status = await client.get_status()
            if args.json:
                print(json.dumps(status))
            else:
                print(status)
        elif args.command == "status-observe":
            async for status in client.observe_status():
                if args.json:
                    print(json.dumps(status))
                else:
                    print(status)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        if client:
            await client.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
