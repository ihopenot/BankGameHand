# EconomyEntryComponent

经济实体组件

## 资产负债表

### 资产
[资产详细](#资产)

### 负债
[负债详细](#负债)

## 现金流量表

## 利润表

# 资产

- 现金

- 固定资产
    - [工厂](Factory.md)

- 商品

- 金融资产

- 无形资产

- 应收账款（其他经济实体欠的钱，如赊账卖出商品的货款）

# 负债

- 贷款

- 应付账款（欠其他经济实体的钱，如赊账采购的货款）

# Functions

Transaction(EconomyEntryComponent &A, EconomyEntryComponent &B, Asset Offer[], Asset Recive[]) {
    A提供Offer列表中的资产，交换B资产中的Recive列表

    所有交换只发生在经济实体之间，所有交换**必须**通过这个接口

    这个接口负责校验双方资产，并同步更新资产负债表
}