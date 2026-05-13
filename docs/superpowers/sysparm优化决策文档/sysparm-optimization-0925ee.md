# 系统设置功能优化方案（方案 A）

**本次实施范围**：仅第二层——将系统参数页（`ParamsList.vue`）从只读列表改为分组可编辑表单，后端补充更新接口。第一层个人偏好设置（主题切换/每页条数/侧边栏）为独立功能，本次不实施，仅做架构规划记录。

---

## 设计原则：两层分离

```
顶部导航右上角头像 → 个人设置（主题/偏好）    ← 用户自己改，存 localStorage
系统菜单 → 系统管理 → 系统参数               ← 管理员才能改，存数据库
```

---

## 第一层：个人偏好设置（纯前端）

### 全局布局层次

当前顶部右侧只有 `用户名 | 退出` 两个元素（见 `MainLayout.vue` `header-right`）。改造后：

```
┌──────────────────────────────────────────────────────────────┐
│  ☰  首页 / 当前页面                     🌙  [用户名 ▾]  退出  │
│                                          ↑主题切换  ↑下拉菜单 │
└──────────────────────────────────────────────────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  👤 个人设置          │
                                    │  ────────────────    │
                                    │  🚪 退出登录          │
                                    └─────────────────────┘
```

- **用户名** 改为可点击的下拉按钮
- 下拉菜单包含「个人设置」和「退出登录」
- 顶部 header-right 还新增一个**主题切换图标**（🌙/☀️），点击直接切换亮色/暗色，无需进入设置弹窗

### 「个人设置」弹窗内容

点击下拉菜单中「个人设置」，打开弹窗：

```
┌─────── 个人设置 ───────────┐
│ 界面主题  ○亮色 ●暗色 ○跟随  │
│ 每页条数  [下拉: 20]        │
│ 侧边栏    [折叠] ●展开       │
│                   [确定]   │
└───────────────────────────┘
```

### 入口（代码层面）
`MainLayout.vue` header-right 区域改造：原 `<el-button text @click="handleLogout">退出</el-button>` → 改为用户名下拉 + 独立主题图标按钮。

### 功能项

| 功能 | key | 说明 |
|------|-----|------|
| UI 主题 | `theme` | 亮色 / 暗色 / 跟随系统 |
| 表格每页条数 | `pageSize` | 10 / 20 / 50 |
| 侧边栏默认折叠 | `sidebarCollapsed` | 记住折叠状态 |

### 技术方案
- 主题切换：在 `<html>` 上切换 `dark` class，Element Plus 内置支持
- Pinia store（`useSettingsStore`）管理状态，初始化时从 `localStorage` 读取
- 无需任何后端改动

### 改动文件

| 文件 | 说明 |
|------|------|
| `src/stores/settings.ts` | 新建：Pinia store，管理 theme/pageSize/sidebarCollapsed |
| `src/components/UserSettings.vue` | 新建：个人设置弹窗 |
| `src/layouts/MainLayout.vue` | 头像下拉新增「个人设置」入口 |
| `src/App.vue` | 初始化时应用 theme class |

---

## 第二层：系统参数（方案 A — 单例表单）

### 方案选择理由

- `tmc71_sysparm` 保持**单行单例表**不变，不改表结构
- 参数数量少（6个）且稳定，增减必须经过代码评审，防止随意堆参数
- 改动最小，风险最低

### 有效参数（全部保留，支持编辑）

| 字段 | 中文名 | 控件 | 分组 |
|------|--------|------|------|
| `costtype` | 成本核算方式 | 下拉（1移动加权 / 2先进先出） | 仓储 |
| `centralwarehouse` | 中心仓库编码 | 文本输入 | 仓储 |
| `poinvaliddays` | 采购计划失效天数 | 数字输入 | 采购/销售 |
| `soinvaliddays` | 销售单失效天数 | 数字输入 | 采购/销售 |
| `shopbilltype` | 门店单据类型 | 数字输入 | 采购/销售 |
| `allowmultilogon` | 允许多点登录 | 开关（1是 / 0否） | 系统安全 |

### 字段处理说明

| 字段 | 处理方式 | 说明 |
|------|----------|------|
| `parm_cd` | 前端不展示 | 主键，固定值 `'SYSPARM'`，后端 update 固定 `WHERE parm_cd='SYSPARM'` 查唯一行 |
| `parm_nm` | 前端不展示 | PB 占位字段，与 `parm_cd` 同值，无实际含义 |
| `parm_val` | 前端不展示 | 原设计存通用值，实际从未使用（当前为空） |
| `parm_desc` | 前端不展示 | 说明字段，当前为空 |
| `pk` | 前端不展示 | Oracle 主键占位，历史遗留 |
| `autobackpath` | 前端不展示 | PB 客户端备份路径，Web 无意义 |
| `invoicesharepath` | 前端不展示 | PB 共享目录路径，Web 无意义 |

> 所有不展示字段均**保留在数据库**，不删除。后端 update 固定用 `WHERE parm_cd = 'SYSPARM'` 更新唯一行，无需前端传主键。

### 前端布局

```
系统参数
┌─ 仓储配置 ──────────────────────────────┐
│  成本核算方式   [下拉：移动加权/先进先出]  │
│  中心仓库编码   [文本输入]               │
├─ 采购/销售配置 ──────────────────────────┤
│  采购计划失效天数  [数字输入]             │
│  销售单失效天数   [数字输入]             │
│  门店单据类型    [数字输入]              │
├─ 系统安全 ───────────────────────────────┤
│  允许多点登录   [开关]                   │
└──────────────────────────── [保存] ─────┘
```

整页一个表单，点「保存」统一提交。

### 改动文件

**后端：**

| 文件 | 改动 |
|------|------|
| `app/repositories/system_repository.py` | 新增 `update_sysparm(data: dict)` |
| `app/services/system_service.py` | 新增 `update_sysparm(data: dict)` |
| `app/api/system.py` | 新增 `PUT /sysparms/SYSPARM` 接口 |

**前端：**

| 文件 | 改动 |
|------|------|
| `src/api/system.ts` | 新增 `updateSysparm(data)` |
| `src/views/system/ParamsList.vue` | 改为分组可编辑表单，废弃字段隐藏 |

---

## 实施步骤（本次范围）

1. **新增** `app/repositories/system_repository.py` — `update_sysparm(data: dict)` 方法
2. **新增** `app/services/system_service.py` — `update_sysparm(data: dict)` 方法
3. **新增** `app/api/system.py` — `PUT /sysparms/SYSPARM` 接口
4. **新增** `src/api/system.ts` — `updateSysparm(data)` API 函数
5. **修改** `src/views/system/ParamsList.vue` — 改为分组可编辑表单，隐藏不展示字段

> 个人偏好设置（步骤 stores/settings.ts / UserSettings.vue / MainLayout.vue / App.vue）为独立任务，本次不做。

---

## 外部集成配置（规划，本次不实施）

与外围系统（IoT/监控终端）的集成涉及两类配置，归属不同：

| 配置项 | 归属 | 现状 |
|--------|------|------|
| 每台设备的心跳间隔、协议、Topic | `tio01_device_conn`（DeviceConn 表，按设备存储） | **已有** |
| 报警规则阈值 | `tio03_alert_rule`（AlertRule 表，按规则存储） | **已有** |
| MQTT Broker 全局地址/端口 | 系统参数「外部集成」分组 | **待加** |
| 全局同步重试次数/超时 | 系统参数「外部集成」分组 | **待加** |

**本次不实施**，待 IoT 中间件（MQTT Broker）建设时，在系统参数中补充「外部集成」分组：

```
外部集成配置（IoT 中间件建设时新增）
  mqtt_broker_host     MQTT Broker 地址     [文本]
  mqtt_broker_port     MQTT Broker 端口     [数字，默认 1883]
  mqtt_connect_timeout MQTT 连接超时(秒)    [数字，默认 30]
  data_sync_retry      数据同步重试次数      [数字，默认 3]
```

届时方案 A 的单例表直接加字段即可，无需改架构。

---

## 不做

- 改 `tmc71_sysparm` 表结构（方案 A 保持单例不变）
- 把系统参数并入系统字典（边界不同，不混用）
- 预设未使用的业务参数（等业务模块真正需要时再添加）
- 主题偏好存数据库（localStorage 足够）
