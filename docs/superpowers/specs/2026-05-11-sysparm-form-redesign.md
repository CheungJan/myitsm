# 系统参数表单化改造 Spec

> **Status**: 待实施 | **关联文档**: `sysparm-optimization-0925ee.md`

## 背景

`tmc71_sysparm` 是全局运营配置表，单例模式（1 行 15 列）。当前前端用表格显示单行数据，视觉效果像 bug，且 9 个 PB 遗留字段对 Web 系统无意义。

系统字典（`tmm31_syscodes`）已独立为树状管理页面，系统参数作为不同概念（全局配置值 vs 枚举映射表），保持独立。

## 目标

将系统参数页从单行表格改为**分组可编辑表单**，隐藏废弃字段，后端加 update 接口。

## 不做

- 改 `tmc71_sysparm` 表结构
- 把系统参数并入系统字典
- 预设未使用的业务参数
- 个人偏好设置（独立任务）

---

## 设计

### 后端

**新增 `PUT /api/v1/sysparms/SYSPARM`**

- 请求体：`{ costtype, centralwarehouse, poinvaliddays, soinvaliddays, shopbilltype, allowmultilogon }`
- 通过 URL 中的 `SYSPARM`（即 `parm_cd` 主键）定位记录
- 只更新传入的非空字段

**Repository**: `update_sysparm(parm_cd, data)` — 查记录 → setattr → commit
**Service**: `update_sysparm(parm_cd, data)` — 委托 Repository，返回 dict

### 前端

**ParamsList.vue 改为分组表单**：

表单结构 3 组：

```
系统参数（当前已生效）

[仓储配置]
  成本核算方式    [下拉: 1=移动加权 / 2=先进先出]
  中心仓库编码    [文本]

[采购/销售配置]
  采购计划失效天数  [数字]
  销售单失效天数    [数字]
  门店单据类型      [数字]

[系统安全]
  允许多点登录    [开关: 1=是 / 0=否]

                                    [保存]
```

- 页面加载时调用现有 `fetchSysparms()`（列表接口），取第一条记录填充表单
- 点「保存」→ `PUT /sysparms/SYSPARM` 提交
- 成功/失败提示

**隐藏的字段**（不渲染）：`parm_cd`, `parm_nm`, `parm_val`, `parm_desc`, `pk`, `autobackpath`, `invoicesharepath`, `created_at`, `updated_at`

### 不改动

`GET /sysparms` 和 `GET /sysparms/<parm_cd>` 端点保持不变，向后兼容。

---

## 改动文件

| 文件 | 改动 |
|------|------|
| `app/repositories/system_repository.py` | `update_sysparm(parm_cd, data)` |
| `app/services/system_service.py` | `update_sysparm(parm_cd, data)` |
| `app/api/system.py` | `PUT /sysparms/<parm_cd>` |
| `frontend/src/api/system.ts` | `updateSysparm(cd, data)` |
| `frontend/src/views/system/ParamsList.vue` | 分组表单重写 |

---

## 验证

1. 访问 `/system/params` → 显示 3 组表单，值正确加载
2. 修改成本核算方式 → 保存 → 刷新页面 → 值保持
3. `curl -X PUT /api/v1/sysparms/SYSPARM -d '{"costtype":"2"}'` → 200
