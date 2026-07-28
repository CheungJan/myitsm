## Superpowers 技能分析与 myitsm 项目使用策略

### 一、技能分类与优先级

根据 using-superpowers 技能规则，技能分为两类：

| 类型                      | 技能示例                                      | 作用                 | 优先级         |
| :------------------------ | :-------------------------------------------- | :------------------- | :------------- |
| **Process Skills**        | brainstorming, debugging, writing-plans       | 确定 HOW to approach | 最高（先调用） |
| **Implementation Skills** | frontend-design, mcp-builder, rest-api-design | 引导执行             | 次之           |

------

### 二、完整技能清单与 myitsm 项目适用性

#### 1. Process Skills（流程技能）

| 技能                            | 适用场景                     | myitsm 项目使用建议                                          | 优先级       |
| :------------------------------ | :--------------------------- | :----------------------------------------------------------- | :----------- |
| **brainstorming**               | 方案讨论、需求评审、设计决策 | ✅ **高频使用**<- 新功能设计前- 技术选型决策- 数据模型优化讨论 | 🔴 高         |
| **debugging**                   | Bug排查、测试失败分析        | ✅ **按需使用**<- 数据迁移错误- 前端功能异常- API 返回错误    | 🟡 中         |
| **systematic-debugging**        | 系统化排障流程               | ✅ **复杂问题**<- 数据一致性问题- 性能瓶颈排查                | 🟡 中         |
| **writing-plans**               | 编写实施计划、迁移方案       | ✅ **阶段使用**<- 新模块开发计划- 数据迁移计划- PR 实施计划   | 🟡 中         |
| **executing-plans**             | 按计划逐步执行任务           | ✅ **已使用**<- 系统参数清理计划- 前端表单改造计划            | 🟡 中         |
| **subagent-driven-development** | 大模块拆解为并行子任务       | ✅ **F2+ 阶段**<- ITSM 10 类工单开发- IoT 模块开发- 报表模块开发 | 🟢 低（后续） |

#### 2. Implementation Skills（实现技能）

| 技能                         | 适用场景          | myitsm 项目使用建议                                          | 优先级         |
| :--------------------------- | :---------------- | :----------------------------------------------------------- | :------------- |
| **frontend-design**          | 前端页面/组件开发 | ✅ **高频使用**<- Vue 3 页面开发- Element Plus 组件使用- 响应式布局 | 🔴 高           |
| **frontend-vue-development** | Vue 2/3 开发规范  | ✅ **当前阶段**<- Vue 3 组件开发- Vuex 状态管理- 路由配置     | 🔴 高           |
| **python-backend**           | Python 后端开发   | ✅ **已完成**<- Flask API 开发- SQLAlchemy ORM- JWT 认证      | 🟢 低（已完成） |
| **rest-api-design**          | RESTful API 设计  | ✅ **已使用**<- API 端点设计- 响应格式统一- 错误处理          | 🟡 中           |
| **mcp-builder**              | MCP 服务器开发    | ⚠️ **可选**<- 如需集成外部服务- Figma 集成等                  | 🟢 低（可选）   |

#### 3. Quality Skills（质量技能）

| 技能                               | 适用场景       | myitsm 项目使用建议                                          | 优先级       |
| :--------------------------------- | :------------- | :----------------------------------------------------------- | :----------- |
| **code-review**                    | PR 合并前审查  | ✅ **强制使用**<- 所有 PR 必须审查- 安全漏洞检查- 性能优化建议 | 🔴 高         |
| **requesting-code-review**         | 请求代码审查   | ✅ **配合使用**<- 功能完成后触发- 提交 PR 前执行              | 🔴 高         |
| **security-review**                | 上线前安全检查 | ✅ **上线前**<- OWASP 审查- 注入漏洞检查- 敏感数据检查        | 🔴 高         |
| **verification-before-completion** | 声称完成前验证 | ✅ **强制使用**<- 功能开发完成- 数据迁移完成- 文档更新完成    | 🔴 高         |
| **test-driven-development**        | TDD 流程开发   | ⚠️ **可选**<- 新功能开发时- 复杂业务逻辑时                    | 🟡 中（按需） |

#### 4. Project Management Skills（项目管理技能）

| 技能                               | 适用场景     | myitsm 项目使用建议                                       | 优先级 |
| :--------------------------------- | :----------- | :-------------------------------------------------------- | :----- |
| **finishing-a-development-branch** | 分支完成决策 | ✅ **阶段使用**<- PR 前决策- 合并/回滚/清理                | 🟡 中   |
| **receiving-code-review**          | 接收审查反馈 | ✅ **配合使用**<- 审查反馈处理- 技术争议解决               | 🟡 中   |
| **doc-coauthoring**                | 文档协作编写 | ✅ **文档阶段**<- 技术文档编写- API 文档更新- 用户手册编写 | 🟡 中   |

#### 5. Specialized Skills（专用技能）

| 技能                                                     | 适用场景                    | myitsm 项目使用建议                                     | 优先级         |
| :------------------------------------------------------- | :-------------------------- | :------------------------------------------------------ | :------------- |
| **sqlalchemy-alembic-expert-best-practices-code-review** | SQLAlchemy/Alembic 最佳实践 | ✅ **数据库相关**<- 模型设计审查- 迁移脚本审查- 查询优化 | 🟡 中           |
| **vercel-react-native-skills**                           | React Native 开发           | ❌ **不适用**<- 项目是 Web 应用- 无移动端需求            | 🟢 无           |
| **claude-api**                                           | Claude API/SDK 开发         | ⚠️ **可选**<- 如需集成 Claude- AI 功能开发               | 🟢 低（可选）   |
| **karpathy-guidelines**                                  | 编码行为准则                | ✅ **参考使用**<- 代码质量检查- 避免过度设计             | 🟡 中           |
| **legacy-modernizer**                                    | 遗留系统现代化              | ⚠️ **已完成**<- PB→Python 重构已完成- 可用于其他遗留系统 | 🟢 低（已完成） |

------

### 三、myitsm 项目技能使用矩阵

#### 当前阶段（F1 前端开发 + 数据迁移）

| 阶段         | 必用技能                                                     | 推荐技能                                        | 可选技能                |
| :----------- | :----------------------------------------------------------- | :---------------------------------------------- | :---------------------- |
| **前端开发** | frontend-design, frontend-vue-development, verification-before-completion | rest-api-design, code-review                    | test-driven-development |
| **数据迁移** | systematic-debugging, verification-before-completion         | brainstorming, writing-plans                    | -                       |
| **文档更新** | doc-coauthoring                                              | brainstorming                                   | -                       |
| **PR 提交**  | code-review, requesting-code-review, verification-before-completion | security-review, finishing-a-development-branch | -                       |

#### 后续阶段（F2+ 工单模块）

| 阶段           | 必用技能                                                  | 推荐技能                         | 可选技能                |
| :------------- | :-------------------------------------------------------- | :------------------------------- | :---------------------- |
| **大模块开发** | brainstorming, writing-plans, subagent-driven-development | frontend-design, rest-api-design | test-driven-development |
| **IoT 集成**   | brainstorming, rest-api-design                            | security-review                  | mcp-builder             |
| **报表开发**   | brainstorming, frontend-design                            | python-backend                   | -                       |

------

### 四、技能调用规则总结

#### 规则 1：Process Skills 优先





```
用户请求 → brainstorming（如果涉及设计/决策）→ Implementation Skills
```

**示例：**

- "实现物料树" → brainstorming → frontend-design
- "修复数据迁移错误" → debugging → verification-before-completion

#### 规则 2：质量检查强制





```
功能完成 → verification-before-completion → requesting-code-review → code-review
```

#### 规则 3：分支管理规范





```
开发完成 → finishing-a-development-branch → 决策（合并/回滚/清理）
```

------

### 五、项目技能使用建议

#### 高优先级（立即应用）

1. **brainstorming** - 所有新功能设计前
2. **frontend-design** + **frontend-vue-development** - 前端开发
3. **code-review** - 所有 PR
4. **verification-before-completion** - 所有任务完成前
5. **requesting-code-review** - 提交 PR 前

#### 中优先级（按需使用）

1. **debugging** / **systematic-debugging** - 问题排查
2. **writing-plans** - 阶段性规划
3. **security-review** - 上线前
4. **doc-coauthoring** - 文档编写
5. **sqlalchemy-alembic-expert-best-practices-code-review** - 数据库相关

#### 低优先级（后续阶段）

1. **subagent-driven-development** - F2+ 大模块开发
2. **test-driven-development** - 复杂业务逻辑
3. **mcp-builder** - 外部服务集成

------

分析完成。已针对 myitsm 项目当前阶段（F1 前端开发 + 数据迁移）制定了详细的技能使用策略，包括：

- **技能分类**：Process Skills（流程）vs Implementation Skills（实现）
- **适用性矩阵**：30+ 技能的使用场景和优先级
- **调用规则**：brainstorming 优先 → Implementation Skills → 质量检查
- **阶段建议**：当前阶段必用技能 vs 后续阶段技能

核心建议：前端开发阶段高频使用 `brainstorming`、`frontend-design`、`frontend-vue-development`、`code-review`、`verification-before-completion`。


Spec缺失的细节
1. 系统字典配置细节
Spec中（第95-100行）：

## 码表新增
 
| code_typ | 用途 |
|----------|------|
| AT | 资产类型（NEW/USED/REFURB/SCRAP） |
| RS | 回收状态（PENDING/RECYCLED/SCRAPPED） |
缺失：

具体的 code_cd 和 codenm 映射关系
配置原因说明
实施方式（SQL语句还是手动配置）
前端如何调用系统字典API
建议补充：

## 系统字典配置
 
### 资产类型（AT）
 
| code_cd | codenm | 对应值 |
|---------|--------|--------|
| 01 | 新机 | NEW |
| 02 | 旧机 | OLD |
| 03 | 翻新机 | RENOVATED |
| 04 | 报废 | SCRAP |
 
**实施**：INSERT INTO tmm31_syscodes (code_typ, code_cd, codenm, useflg) VALUES ...
 
### 回收状态（RS）
 
| code_cd | codenm | 对应值 |
|---------|--------|--------|
| 01 | 无需回收 | NONE |
| 02 | 待回收 | PENDING |
| 03 | 已回收 | RECYCLED |
| 04 | 已报废 | SCRAPPED |
2. 其他可能缺失的细节
前端API调用：如何调用系统字典API获取码表数据
关联查询的JOIN逻辑：具体的SQL JOIN语句示例
权限控制：运维人员只读，资产管理员可编辑
错误处理：API返回错误时的前端处理