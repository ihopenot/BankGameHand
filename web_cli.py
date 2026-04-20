"""BankGameHand Web 客户端入口脚本。

连接到游戏服务端，在本地提供 Web 界面。
用法：python web_cli.py --server ws://host:9000 [--port 8000]
"""
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="BankGameHand Web Client")
    parser.add_argument(
        "--server", required=True,
        help="Game server WebSocket URL (e.g. ws://localhost:9000)",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Local HTTP host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Local HTTP port (default: 8000)",
    )
    args = parser.parse_args()

    from web.web_controller import WebClient

    logger.info(
        "Starting Web client on http://%s:%d, proxying to %s",
        args.host, args.port, args.server,
    )
    client = WebClient(server_url=args.server)
    client.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
