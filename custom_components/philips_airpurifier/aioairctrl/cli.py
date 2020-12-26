import argparse
import asyncio
import json
import logging

from .coap_client import CoAPClient

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__package__)


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
    parser.add_argument(
        "-D",
        "--debug",
        dest="debug",
        action="store_true",
        help="Enable debug output",
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
    parser_set = subparsers.add_parser(
        "set",
        help="Set value of device",
    )
    parser_set.add_argument(
        "values",
        metavar="K=V",
        type=str,
        nargs="+",
        help="Key-Value pairs to set",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("coap").setLevel(logging.DEBUG)
        logging.getLogger("philips_airpurifier").setLevel(logging.DEBUG)
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
        elif args.command == "set":
            data = {}
            for e in args.values:
                k, v = e.split("=")
                data[k] = v
            if data:
                await client.set_control_values(data=data)
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
