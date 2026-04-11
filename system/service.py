from abc import ABC, abstractmethod

class Service(ABC):
    @abstractmethod
    def update_pahse():
        pass

    @abstractmethod
    def sell_phase():
        pass

    @abstractmethod
    def buy_phase():
        pass

    @abstractmethod
    def product_phase():
        pass

    @abstractmethod
    def plan_phase():
        pass

    @abstractmethod
    def settlement_phase():
        pass

    @abstractmethod
    def act_phase():
        pass