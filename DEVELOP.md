# DEVELOP

本文档记录每个版本对插件结构、配置、页面和运行逻辑的变动。

## 0.3.0 - 2026-06-07

新增“用量超限时的措施”能力。

- `metadata.yaml`
  - 版本号更新为 `0.3.0`。
- `_conf_schema.json`
  - 新增 `over_limit_policy` 配置集合。
  - 集合内包含 `action`、`fallback_provider_id`、`fallback_token_limit`。
  - `daily_token_limit` 和 `block_message` 文案调整为同时适配停止调用与回退策略。
- `main.py`
  - 新增策略常量 `OVER_LIMIT_STOP`、`OVER_LIMIT_FALLBACK`。
  - 新增 `over_limit_policy` 到 `CONFIG_SCHEMA`。
  - 新增 `/providers` Web API，用于 Plugin Page 获取当前可作为回退模型的供应商列表。
  - 新增 `_over_limit_policy()`、`_fallback_provider_id()`、`_fallback_token_limit()`、`_fallback_provider_exists()`。
  - 新增 `_provider_options()`、`_config_schema_for_page()`，让 Plugin Page 的回退供应商字段可动态渲染下拉选项。
  - 扩展 `_query_usage_for_group()`，支持按 `provider_id` 统计或排除某个供应商。
  - 扩展 `_build_usage_payload()`，返回原始模型用量、回退模型用量、回退上限、回退状态和有效总上限。
  - 扩展 `_sanitize_config()` 和新增 `_sanitize_over_limit_policy()`，保存配置时校验回退策略。
  - 扩展 `on_llm_request()`：
    - 原始模型未超限时保持默认供应商。
    - 原始模型超限且回退额度未耗尽时，通过 `event.set_extra("selected_provider", fallback_provider_id)` 切换供应商。
    - 回退额度耗尽或策略为停止调用时，发送拦截提示并 `event.stop_event()`。
- `pages/dashboard/index.html`
  - 在“插件功能”中新增蓝色“用量超限策略配置”按钮。
  - 新增 `#strategyOverlay`、`#strategyForm`、`#saveStrategyBtn`、`#cancelStrategyBtn`、`#strategyToast`。
  - 抽象配置控件渲染函数，普通配置弹窗和策略弹窗共用同一套 schema 渲染逻辑。
  - 策略弹窗只在选择“回退到其他模型”时显示回退供应商和回退上限。
  - 用量统计在回退阶段显示黄色进度条、黄色用量文本和“回退模型”标签。
  - 回退阶段的显示上限改为 `daily_token_limit + fallback_token_limit`。
- `README.md`
  - 更新功能说明、配置项、超限策略示例和兼容性说明。
- `STRUCTURE.md`
  - 重写为 v0.3.0 结构文档，补充完整文件结构、Web API、HTML 元素映射和 `main.py` 函数职责。

## 0.2.0 - 2026-06-07

增强 Plugin Page 的可读性和可编辑性。

- `main.py`
  - 新增群备注持久化文件 `group_remarks.json`。
  - 新增 `GROUP_REMARKS_FILE`、`MAX_GROUP_REMARK_LENGTH`。
  - 新增 `_resolve_group_remarks_path()`、`_load_group_remarks()`、`_save_group_remarks()`、`_sanitize_group_remark()`。
  - 新增 `/remarks` GET/POST Web API。
  - `_build_usage_payload()` 返回每个群号的备注。
- `pages/dashboard/index.html`
  - “用量统计”中的 QQ 群号右侧新增铅笔按钮。
  - 新增 `#remarkOverlay` 备注编辑弹窗。
  - 备注以浅灰色 `（备注）` 形式紧跟群号显示。
  - 所有按钮补充 hover 和 active 视觉反馈。
  - 配置 textarea 渲染时把显式 `\n` 转为真实换行。
- `metadata.yaml`
  - 版本号更新为 `0.2.0`。
- `README.md`、`STRUCTURE.md`、`DEVELOP.md`
  - 记录备注、按钮状态和页面配置渲染逻辑。

## 0.1.0 - 2026-06-06

初始版本。

- 新增 `main.py` 插件主体：
  - 注册 `/astrbot_plugin_token_limit/config`、`/astrbot_plugin_token_limit/usage` Web API。
  - 通过 `filter.on_llm_request(priority=1000)` 在 LLM 请求前执行限流判断。
  - 查询 AstrBot 原生 `ProviderStat` 表统计窗口内群聊 token 用量。
  - 支持 `unique_session` 常见 QQ 群 session 形式匹配。
- 新增 `_conf_schema.json`：
  - 定义原生 WebUI 插件配置项。
  - Page 悬浮配置页复用同一份字段含义。
- 新增 `pages/dashboard/index.html`：
  - 左栏展示群 token 用量进度条。
  - 右栏提供悬浮配置页。
  - 使用 `window.AstrBotPluginPage.apiGet/apiPost` 调用插件后端 API。
- 新增 `metadata.yaml`：
  - 声明插件元数据、支持平台和 Plugin Page。
- 新增 `README.md`、`DEVELOP.md`、`STRUCTURE.md` 文档。

## 长期结构约束

- 不维护独立 token 计数数据库，统计来源始终为 AstrBot 原生 `ProviderStat`。
- 不拦截无需调用 LLM 的插件命令或普通消息。
- 配置保存始终写回 AstrBot 注入的插件 `AstrBotConfig` 对象。
- 群备注是插件页面辅助数据，不属于限流配置，独立保存在插件数据目录。
