# BOM功能优化方案

本计划旨在补全F1物料管理中缺失的BOM（物料清单）功能，支持两种BOM组成方式：主机+配件方式和完全配件自主组装方式，并提供完整的BOM管理界面。

## 问题分析

### 当前系统现状
- **后端模型**：Bom (TMM41_BOM) 和 BomDt (TMM42_BOMDT) 已存在
- **后端API**：仅有BOM报表查询端点（GET /api/v1/reports/bom/tree），缺少BOM管理CRUD API
- **前端实现**：只有ItemList.vue（物料管理），缺少BOM管理页面
- **前端物料页面字段缺失**：ItemList.vue只显示5个字段（item_cd, item_nm, class_cd, itemanm, unit），缺少库存上下限、最小订购量等重要字段
- **数据迁移**：老系统BOM数据已迁移（103个BOM，1268条明细）

### 老系统BOM数据结构示例
- BOM编码：4Q4LR4
- BOM名称：TFP4000 4LR4(DJR64ACNNS3NN)
- 配件明细：10个配件（主板MB4AL3、内存MMDA4G、存储HDAN16、电源PW4A03、显示屏MT4A01、打印机PTY501、扫描枪BS4001、钱箱CB3400、客显CD4A02、适配器PTY5P1）

### 业务场景
1. **主机+配件方式**：采购完整主机作为物料，通过BOM定义需要搭配的外设配件
   - 适用场景：公司内部不拆主机更换维护，以整机更换方式
   - **BOM编码 = 整机型号**（最终交付给客户的设备型号，如7Q0013）
   - **商品信息**：spec字段填写主机核心参数（处理器、存储、内存、屏幕等）
   - **BOM明细**：只包含外设配件（itemtyp=0，如键盘、鼠标、打印机等），不包含主机核心配件（主板、内存、存储、电源等）
   - **示例**：7Q0013（TFP5000 ANPED），BOM明细包含12个外设配件（键盘、鼠标、打印机等），全部itemtyp=0

2. **完全配件自主组装方式**：所有物料都是最小单位（主板、键盘、内存等），通过BOM组装成整机
   - 适用场景：主机可以拆分成核心配件模块维修更换
   - **BOM编码 = 整机型号**（最终交付给客户的设备型号，如4Q4LR4）
   - **商品信息**：spec字段填写整机规格描述
   - **BOM明细**：包含所有配件，包括核心配件（itemtyp=1，如主板、内存、存储、电源、显示屏）和外设配件（itemtyp=0，如扫描枪、钱箱等）
   - **示例**：4Q4LR4（TFP4000 4LR4），BOM明细包含10个配件（主板、内存、存储、电源、显示屏、扫描枪、钱箱等），itemtyp=0和itemtyp=1混合

### 老系统限制
- 主机+配件方式只能将主机核心参数作为商品信息代表，无法灵活管理BOM结构
- 一个物料编码可以对应多个BOM，但缺乏统一管理界面

### 前端物料页面字段缺失影响
**缺失字段**（TMM12_ITEMS表中存在但前端未显示）：
- **库存管理相关**：upperlimit（库存上限）、lowerlimit（库存下限）、minorder（最小订购量）
- **周期管理相关**：newperiod（新品周期）、oldperiod（旧品周期）
- **规格参数相关**：spec（规格型号）、itembrcd（物料条码）、itemsize（规格尺寸）
- **采购管理相关**：pcrep（采购负责人）、purchasetyp（采购类型）
- **库存管理相关**：keeper（库管员）
- **地理信息相关**：countrycd（产地国家）、provincecd（省份）、citycd（城市）
- **其他**：backup（备注）、typflg（物料类型标志）、consume（消耗标志）、wunit（计量单位）

**影响范围**：
- 安全库存功能依赖lowerlimit字段
- 采购计划依赖minorder字段
- 库存预警依赖upperlimit和lowerlimit字段
- 新品/旧品管理依赖newperiod和oldperiod字段

## 优化方案

### 1. 后端API开发

#### 1.1 创建BOM管理API蓝图
**文件**：`app/api/bom.py`

**端点设计**：
- `GET /api/v1/bom` - BOM列表查询（分页、筛选）
- `POST /api/v1/bom` - 创建BOM
- `GET /api/v1/bom/<bomcd>` - BOM详情查询
- `PUT /api/v1/bom/<bomcd>` - 更新BOM
- `DELETE /api/v1/bom/<bomcd>` - 删除BOM
- `GET /api/v1/bom/<bomcd>/details` - BOM明细列表
- `POST /api/v1/bom/<bomcd>/details` - 添加BOM明细
- `PUT /api/v1/bom/<bomcd>/details/<itemcd>` - 更新BOM明细
- `DELETE /api/v1/bom/<bomcd>/details/<itemcd>` - 删除BOM明细

#### 1.2 创建BOM Service层
**文件**：`app/services/bom_service.py`

**职责**：
- BOM主表的CRUD业务逻辑
- BOM明细的CRUD业务逻辑
- BOM与物料的关联校验
- BOM版本管理（如果需要）

#### 1.3 创建BOM Repository层
**文件**：`app/repositories/bom_repository.py`

**职责**：
- BOM数据访问封装
- BOM明细数据访问封装
- 复杂查询（如BOM树形结构查询）

#### 1.4 创建BOM Schema
**文件**：`app/schemas/bom.py`

**Schema定义**：
- `BomCreateRequest` - BOM创建请求
  - bomcd: str (BOM编码，对应整机物料编码)
  - bomnm: str (BOM名称)
- `BomUpdateRequest` - BOM更新请求
- `BomResponse` - BOM响应
- `BomDtCreateRequest` - BOM明细创建请求
  - itemcd: str (物料编码)
  - bomqty: int (BOM数量)
  - itemtyp: str (物料类型：0=外设配件，1=核心配件)
- `BomDtUpdateRequest` - BOM明细更新请求
- `BomDtResponse` - BOM明细响应

#### 1.5 注册BOM蓝图
**文件**：`app/__init__.py`

在blueprint注册中添加：
```python
from app.api import bom as bom_bp
app.register_blueprint(bom_bp.bom_bp, url_prefix="/api/v1/bom")
```

### 2. 前端页面开发

#### 2.1 创建BOM管理页面
**文件**：`frontend/src/views/master/BomList.vue`

**功能**：
- BOM列表展示（分页、筛选）
- 新增/编辑/删除BOM
- 查看BOM明细
- BOM明细的增删改

**UI布局**：
- 左侧：BOM列表
- 右侧：BOM明细编辑区
- 支持双面板布局

#### 2.2 创建BOM API接口
**文件**：`frontend/src/api/master.ts`

**新增接口**：
- `fetchBoms()` - 获取BOM列表
- `createBom()` - 创建BOM
- `updateBom()` - 更新BOM
- `deleteBom()` - 删除BOM
- `fetchBomDetails()` - 获取BOM明细
- `addBomDetail()` - 添加BOM明细
- `updateBomDetail()` - 更新BOM明细
- `deleteBomDetail()` - 删除BOM明细

#### 2.3 更新路由配置
**文件**：`frontend/src/router/index.ts`

**新增路由**：
```typescript
{
  path: '/master/bom',
  name: 'BomList',
  component: () => import('@/views/master/BomList.vue'),
  meta: { title: 'BOM管理' }
}
```

#### 2.4 更新导航菜单
**文件**：`frontend/src/layout/AsideMenu.vue`

**新增菜单项**：
- 基础数据 → BOM管理

#### 2.5 扩展物料页面字段显示
**文件**：`frontend/src/views/master/ItemList.vue`

**当前显示字段**（5个）：
- item_cd（物料编码）
- item_nm（物料名称）
- class_cd（分类编码）
- itemanm（别名）
- unit（单位）

**新增显示字段**（分批显示，避免表格过宽）：

**批次1（库存管理相关）**：
- upperlimit（库存上限）
- lowerlimit（库存下限）
- minorder（最小订购量）

**批次2（规格参数相关）**：
- spec（规格型号）
- itembrcd（物料条码）
- itemsize（规格尺寸）

**批次3（周期管理相关）**：
- newperiod（新品周期）
- oldperiod（旧品周期）

**批次4（采购管理相关）**：
- pcrep（采购负责人）
- purchasetyp（采购类型）
- keeper（库管员）

**批次5（其他）**：
- backup（备注）
- typflg（物料类型标志）
- consume（消耗标志）

**UI设计**：
- 表格列过多时使用折叠/展开功能
- 关键字段（库存上下限）高亮显示
- 使用Tooltip显示字段说明
- 支持列自定义显示/隐藏

**表单扩展**：
- 物料编辑弹窗增加折叠面板
- 分组显示字段：基础信息、库存管理、规格参数、采购管理、其他
- 必填字段标注
- 字段验证规则

#### 2.6 更新前端类型定义
**文件**：`frontend/src/api/master.ts`

**扩展ItemRecord接口**：
```typescript
export interface ItemRecord {
    item_cd: string
    item_nm: string
    class_cd: string
    itemanm: string
    unit: string
    spec: string
    useflg: string
    // 新增字段
    itembrcd?: string
    itemsize?: string
    countrycd?: string
    provincecd?: string
    citycd?: string
    wunit?: string
    pcrep?: string
    keeper?: string
    upperlimit?: number
    lowerlimit?: number
    minorder?: number
    newperiod?: number
    oldperiod?: number
    backup?: string
    typflg?: string
    purchasetyp?: string
    consume?: string
    [key: string]: unknown
}
```

### 3. 数据模型优化

#### 3.1 Item表字段扩展
**当前字段**：spec（规格型号）

**建议扩展**（如果需要更灵活的主机参数管理）：
- 保持现有spec字段，用于存储规格型号文本
- 新增字段可选：
  - `cpu_spec` - 处理器规格
  - `memory_spec` - 内存规格
  - `storage_spec` - 存储规格
  - `screen_spec` - 屏幕规格
  - `other_params` - 其他参数（JSON格式）

**决策**：暂不扩展Item表，使用现有spec字段存储主机核心参数，后续根据实际需求再扩展。

#### 3.2 BomDt表itemtyp字段含义
**当前字段**：itemtyp（物料类型）

**用途**：区分配件类型（0=外设配件，1=核心配件等）

**建议**：
- 明确itemtyp字段的使用规范
- 0: 外设配件（扫描枪、打印机、钱箱等）
- 1: 核心配件（主板、内存、存储、电源等）
- 2: 其他

### 4. 业务流程优化

#### 4.1 BOM与物料的关系
- **一对多**：一个物料编码可以对应多个BOM
- **查询**：根据物料编码查询该物料的所有BOM
- **展示**：在物料详情页展示该物料关联的BOM列表

#### 4.2 BOM组成方式标识
**老系统设计**：
- **bomcd** = 整机物料编码（主机+配件方式：bomcd = 主机物料编码；完全配件自主组装方式：bomcd = 整机物料编码）
- **bomdt** = 只包含配件，不包含主机本身
- **itemtyp** = 区分配件类型（0=外设配件，1=核心配件）

**BOM类型判断规则**：
- **主机+配件方式**：bomdt只包含itemtyp=0（外设配件），没有itemtyp=1（核心配件）
- **完全配件自主组装方式**：bomdt包含itemtyp=0和itemtyp=1

**前端交互设计**：
1. **创建BOM时**：不需要选择BOM类型
2. **添加BOM明细时**：用户勾选itemtyp（0=外设配件，1=核心配件）
3. **后端自动推断**：根据itemtyp的组合自动推断BOM类型
4. **规则限制**：
   - 如果选择了itemtyp=1（核心配件），则必须包含主机核心配件（主板、内存、存储、电源等）
   - 如果只选择了itemtyp=0（外设配件），则为主机+配件方式
   - 如果同时选择了itemtyp=0和itemtyp=1，则为完全配件自主组装方式

**决策**：采用itemtyp字段推断BOM类型，无需新增字段。

#### 4.3 BOM版本管理
**需求**：是否需要BOM版本管理？

**建议**：暂不实现版本管理，后续根据实际需求再扩展。

### 5. 实施计划

#### 阶段1：后端开发（预计2-3天）
1. 创建BOM Schema（app/schemas/bom.py）
2. 创建BOM Repository（app/repositories/bom_repository.py）
3. 创建BOM Service（app/services/bom_service.py）
4. 创建BOM API蓝图（app/api/bom.py）
5. 注册BOM蓝图（app/__init__.py）
6. 编写单元测试

#### 阶段2：前端开发（预计3-4天）
1. 扩展物料页面字段显示（frontend/src/views/master/ItemList.vue）
   - 批次1：库存管理相关字段（upperlimit, lowerlimit, minorder）
   - 批次2：规格参数相关字段（spec, itembrcd, itemsize）
   - 批次3：周期管理相关字段（newperiod, oldperiod）
   - 批次4：采购管理相关字段（pcrep, purchasetyp, keeper）
   - 批次5：其他字段（backup, typflg, consume）
2. 更新前端类型定义（frontend/src/api/master.ts）
3. 创建BOM API接口（frontend/src/api/master.ts）
4. 创建BOM管理页面（frontend/src/views/master/BomList.vue）
5. 更新路由配置（frontend/src/router/index.ts）
6. 更新导航菜单（frontend/src/layout/AsideMenu.vue）
7. 前端联调测试

#### 阶段3：测试与优化（预计1天）
1. 功能测试
2. 界面优化
3. 文档更新

### 6. 风险与决策

#### 风险1：BOM数据迁移完整性
- **风险**：老系统BOM数据可能存在不一致
- **缓解**：数据迁移时已验证完整性（103个BOM，1268条明细）
- **决策**：无需额外处理

#### 风险2：Item表字段是否扩展
- **风险**：扩展Item表字段可能影响现有功能
- **缓解**：暂不扩展，使用现有spec字段
- **决策**：暂不扩展，后续根据需求再评估

#### 风险3：BOM版本管理
- **风险**：暂不实现版本管理可能无法满足未来需求
- **缓解**：保留扩展性，后续可快速实现
- **决策**：暂不实现，后续根据需求再扩展

### 7. 验收标准

#### 后端验收
- [ ] BOM CRUD API全部实现并通过测试
- [ ] BOM明细CRUD API全部实现并通过测试
- [ ] API符合RESTful规范
- [ ] 单元测试覆盖率≥80%

#### 前端验收
- [ ] BOM列表页面正常展示
- [ ] BOM创建/编辑/删除功能正常
- [ ] BOM明细增删改功能正常
- [ ] 物料页面字段扩展完成（批次1-5）
- [ ] 物料页面表单字段扩展完成
- [ ] 库存上下限字段正常显示和编辑
- [ ] 界面美观，用户体验良好

#### 集成验收
- [ ] 前后端联调通过
- [ ] BOM数据与老系统数据一致
- [ ] 功能符合业务需求

### 8. 文档更新

需要更新的文档：
- `docs/core/系统功能对比分析与扩展规划.md` - 补充BOM功能完成状态
- `docs/core/CORE_DOCS_INDEX.md` - 更新索引
- `docs/superpowers/specs/2026-05-14-F2业务主链前端权威设计文档.md` - 补充BOM管理页面

## 附录

### A. 数据库表结构

#### TMM41_BOM（BOM主表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| bomcd | CHAR(6) | BOM编码（主键） |
| bomnm | VARCHAR2(50) | BOM名称 |
| opercd | CHAR(6) | 操作员 |
| gendate | DATE | 创建日期 |
| upddate | DATE | 更新日期 |
| useflg | CHAR(1) | 有效标志 |
| created_at | TIMESTAMP | 创建时间（ORM字段） |
| updated_at | TIMESTAMP | 更新时间（ORM字段） |

#### TMM42_BOMDT（BOM明细表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| bomcd | CHAR(6) | BOM编码（主键） |
| itemcd | CHAR(6) | 物料编码（主键） |
| bomqty | NUMBER | BOM数量 |
| opercd | CHAR(6) | 操作员 |
| gendate | DATE | 创建日期 |
| upddate | DATE | 更新日期 |
| itemtyp | VARCHAR2(1) | 物料类型（0=外设配件，1=核心配件） |
| created_at | TIMESTAMP | 创建时间（ORM字段） |
| updated_at | TIMESTAMP | 更新时间（ORM字段） |

### B. 老系统BOM数据统计
- BOM主表：103条记录
- BOM明细表：1268条记录
- 平均每个BOM包含12.3个配件

### C. PB源码参考文件
虽然PB源码文件无法读取（包含null字节），但以下文件可作为业务逻辑参考：
- `PBsrc/base_cust.pbl/u_mm_bom.sru` - BOM管理
- `PBsrc/base_cust.pbl/u_mm_bom_list.sru` - BOM列表
- `PBsrc/base_cust.pbl/u_mm_bom_new.sru` - 新增BOM
- `PBsrc/base_cust.pbl/u_mm_bomitem.sru` - BOM明细管理
