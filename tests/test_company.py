from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.company.company import Company


class TestCompany:
    def test_inherits_entity(self):
        assert issubclass(Company, Entity)

    def test_has_productor_component(self):
        company = Company()
        prod = company.get_component(ProductorComponent)
        assert isinstance(prod, ProductorComponent)

    def test_has_storage_component(self):
        company = Company()
        storage = company.get_component(StorageComponent)
        assert isinstance(storage, StorageComponent)

    def test_productor_storage_linked(self):
        company = Company()
        prod = company.get_component(ProductorComponent)
        storage = company.get_component(StorageComponent)
        assert prod.storage is storage
