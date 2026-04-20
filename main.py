"""BankGameHand 游戏入口脚本。

用法:
    python main.py                              # CLI 模式（终端交互）
    python main.py --mode server                # 服务端模式（WebSocket）
    python main.py --mode server --port 9000    # 指定端口
"""
import argparse
import logging

from game.game import Game

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _build_input_controller(args: argparse.Namespace):
    """根据命令行参数构建 PlayerInputController 实例。"""
    if args.mode == "server":
        from web.server_input_controller import ServerInputController
        return ServerInputController(host=args.host, port=args.port)
    return None  # 默认使用 StdinInputController


def main() -> None:
    parser = argparse.ArgumentParser(description="BankGameHand")
    parser.add_argument(
        "--mode", choices=["cli", "server"], default="cli",
        help="cli: 终端模式（默认）; server: 服务端模式（WebSocket）",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Server port (default: 9000)")
    args = parser.parse_args()

    controller = _build_input_controller(args)

    logger.info("正在初始化游戏...")
    game = Game(input_controller=controller)
    logger.info(
        "初始化完成：%d 家公司，%d 组居民，总回合数 %d",
        len(game.companies),
        len(game.folks),
        game.total_rounds,
    )

    logger.info("游戏开始")
    game.game_loop()
    logger.info("游戏结束，共运行 %d 回合", game.round)


if __name__ == "__main__":
    main()
