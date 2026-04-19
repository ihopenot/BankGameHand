from entity.goods import GoodsType, GoodsBatch
from core.types import Radio, Money


class TestGoodsType:
    def test_attributes(self):
        gt = GoodsType(name="芯片", base_price=5000)
        assert gt.name == "芯片"
        assert gt.base_price == 5000

    def test_type_annotations(self):
        gt = GoodsType(name="硅", base_price=1000)
        assert isinstance(gt.base_price, int)  # Money


class TestGoodsBatch:
    def test_attributes(self):
        gt = GoodsType(name="芯片", base_price=5000)
        batch = GoodsBatch(goods_type=gt, quantity=100, quality=0.75, brand_value=50)
        assert batch.goods_type is gt
        assert batch.quantity == 100
        assert batch.quality == 0.75
        assert batch.brand_value == 50

    def test_quality_is_radio(self):
        gt = GoodsType(name="硅", base_price=1000)
        batch = GoodsBatch(goods_type=gt, quantity=50, quality=0.5, brand_value=0)
        assert 0.0 <= batch.quality <= 1.0
