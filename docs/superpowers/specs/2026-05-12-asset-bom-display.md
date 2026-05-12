# 资产台账 BOM 配件明细 Spec

> **Status**: 待实施

## 背景

`tmm44_pos_r_eid` 已从原库迁移 14.7 万条数据。资产详情弹窗需展示主机-配件 BOM 结构。

## 设计

### BOM 表格（8 列）

| 列 | 来源 | 说明 |
|----|------|------|
| 整机名称 | tmm12_items.item_nm (posid→itemcd) | 主机物料名 |
| 整机序列号 | posid | 主机 EID |
| 配件代码 | tmm44_pos_r_eid.itemcd | — |
| 配件名称 | tmm12_items.item_nm | — |
| 配件序列号 | tmm44_pos_r_eid.eid | — |
| 质保类型 | OD 码表(old_degree) | 新品质保/旧品质保 |
| 质保开始 | tmm22_customers.opendate/replacedate | — |
| 质保结束 | 开始+newperiod/oldperiod | — |

### 质保规则

- `asset_owner='01'`(我方)→显示质保；`'03'`(客户)→不显示
- `old_degree='12'`→新品质保(newperiod)；`'3'`→旧品质保(oldperiod)
- 开始=opendate（首次开通），如有更换则取 replacedate

### API

`GET /api/v1/assets/bom?eid=<host_eid>` — 返回该主机的配件 BOM 列表

### 前端

AssetList.vue 详情弹窗 BOM 分组改为 8 列表格
