"""BankGameHand 游戏入口脚本。"""
import logging

from game.game import Game

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("正在初始化游戏...")
    game = Game()
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
