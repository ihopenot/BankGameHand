from system.economy_service import EconomyService

class Game:
    economy_service: EconomyService

    def __init__(self):
        self.round = 0

    def game_end(self) -> bool:
        if self.round > 20:
            return True
        return False

    def game_loop(self):
        while not self.game_end():
            self.update_phase() # 更新round，

            self.sell_phase() # 实体挂卖单

            self.buy_phase() # 实体买

            self.product_phase() # 公司生产

            self.plan_phase() # 公司决策，投资科技，品牌，扩产。同时申请贷款
            
            self.player_act() # 玩家决策，审批贷款

            self.settlement_phase()

            self.act_phase() # 公司根据账上现金重新决策并执行

            # self.check_end()
    
    def update_phase(self):
        self.round += 1 # 更新round
        self.economy_service.update_phase() # 更新经济周期
        self.company_service.update_phase() # 更新工厂，计算利息，计算维护成本。更新应付账款，不付现金。
        self.market_service.update_phase() # 更新市场，清空挂单


    def sell_phase(self):
        self.company_service.sell_phase(self.market_service) # 公司挂卖单

    
    def buy_phase(self):
        self.folk_service.buy_phase(self.market_service)
        self.company_service.buy_phase(self.market_service)
    

    def product_phase(self):
        self.company_service.product_phase() # 公司生产
    

    def plan_phase(self):
        self.company_service.plan_pahse() # 公司决策
    

    def player_act(self):
        self.show_play_view()
        while True:
            cmd = self.get_player_command()
            if cmd is EndTurnCommand:
                break
            else:
                self.handle(cmd)


    def settlement_phase(self):
        self.company_service.settlement_phase() # 结算贷款，所有应付，清算公司，银行
    

    def act_phase(self):
        self.company_service.act_phase()

