# DEVELOP

本文档记录每个版本对插件结构、配置、页面和运行逻辑的变动。

## 0.5.0 - 2026-06-08

新增群聊个性化每日上限配置，并增强历史柱状图点击详情。

- `metadata.yaml`
  - 版本号更新为 `0.5.0`。
- `main.py`
  - 新增持久化文件常量 `GROUP_LIMITS_FILE`，运行时生成 `group_limits.json`。
  - 新增 `_resolve_group_limits_path()`、`_load_group_limits()`、`_save_group_limits()`，按 QQ 群号保存个性化每日 token 上限。
  - 新增 `_daily_limit_for_group()`，统一读取群聊有效基础上限；存在个性化上限时覆盖全局 `daily_token_limit`。
  - `_build_event_limit_context()` 改为使用群聊有效上限，确保 LLM 请求限流立即按个性化配置执行。
  - `_build_usage_payload()` 返回每个群聊的 `global_limit_tokens`、`custom_limit_tokens`、`has_custom_limit` 和对应显示值，Plugin Page 可展示并编辑当前有效上限。
  - 注册 `GET /astrbot_plugin_token_limit/group-settings` 与 `POST /astrbot_plugin_token_limit/group-settings`。
  - 新增 `api_get_group_settings()` 和 `api_save_group_settings()`，用于读取/保存“群聊个性化配置”弹窗中的每日上限。
- `pages/dashboard/index.html`
  - 用量统计每个群聊的铅笔备注按钮后新增齿轮按钮，打开“群聊个性化配置”弹窗。
  - 新增 `#groupSettingsOverlay`、`#groupLimitInput`、`#saveGroupSettingsBtn`、`#cancelGroupSettingsBtn`、`#groupSettingsToast` 等页面元素。
  - 新增 `createGearIcon()`、`setGroupSettingsToast()`、`openGroupSettings()`、`closeGroupSettings()`、`saveGroupSettings()`。
  - 保存群聊上限后刷新用量列表，使进度条、回退状态和停止响应状态立即按新上限显示。
  - 历史柱状图柱子新增 hover/active 视觉反馈，并支持点击显示气泡 tag。
  - 新增 `#historyTooltip`、`showHistoryTooltip()`、`hideHistoryTooltip()`；气泡在鼠标点击位置显示横坐标和 token 用量，文本不省略，宽度随最长行自适应。
- `STRUCTURE.md`
  - 更新到 v0.5.0，补充 `group_limits.json`、新增 API、页面元素映射、函数职责、群聊个性化上限与 tooltip 交互规则。

## 0.4.1 - 2026-06-08

优化“历史 token 用量统计”弹窗的图表密度、下拉菜单状态展示和重新进入时的默认状态。

- `metadata.yaml`
  - 版本号更新为 `0.4.1`。
- `backend/history_stats.py`
  - `_format_history_tokens()` 增加小数位参数，支持近 24 小时和近一个月柱顶数值使用 1 位小数。
  - 新增 `_hour_range_label()` 和 `_day_range_label()`，用于多小时、多日聚合后的横坐标标签。
  - `api_get_history()` 在选中群聊时返回 `range_total_tokens` 和 `range_total_display`，供页面显示当前时间跨度内该群 token 用量总和。
  - `_history_recent_hour_bars()` 支持按多小时聚合；随后同版本迭代中，近 24 小时恢复返回 24 个小时原始桶，由页面按宽度动态聚合。
  - `_history_recent_day_bars()` 支持按多日聚合；近一个月从 30 根日柱调整为 10 根 3 天柱，并使用英文月份缩写显示横坐标。
- `pages/dashboard/index.html`
  - “插件功能”按钮顺序调整为：黄色“插件基础配置 ...”在最上方，其下为“用量超限策略配置”和“历史 token 用量统计”。
  - 历史统计弹窗的工具栏新增 `#historyRangeTotal` 右侧总量显示区域。
  - 新增 `renderHistoryTotal()`，根据 `history` API 返回值展示选中群聊在当前时间跨度内的 token 总量；未选群聊时保持为空。
  - 新增 `aggregateHistoryBars()`、`resolveHistoryBarsForViewport()` 和 `handleHistoryResize()`，近 24 小时图表优先使用 2 小时聚合，空间不足时依次降为 3 小时、4 小时聚合。
  - 群聊下拉菜单中状态圆点移动到每日 token 用量数字前方，不再放在群号前方。
  - 每次打开历史统计弹窗时重置为“选择群聊 ...”和“近 24 小时”，并恢复展示历史总量 Top N。
  - 切换群聊或时间跨度时会清空旧总量占位，避免加载期间短暂显示过期数据。
- `STRUCTURE.md`
  - 更新到 v0.4.1，补充历史统计 API 返回字段、图表聚合粒度、`#historyRangeTotal` 元素映射和弹窗重置规则。

## 0.4.0 - 2026-06-08

新增“历史 token 用量统计”能力，并把历史统计后端拆分到独立 mixin。

- `metadata.yaml`
  - 版本号更新为 `0.4.0`。
- `_conf_schema.json`
  - 补充 `limited_groups` 提示：新加入群号会从加入时刻开始历史统计，移除后仍继续统计。
  - 补充 `match_unique_session` 提示：当前窗口与历史统计均使用该匹配口径。
- `backend/`
  - 新增后端目录，按 mixin 方式承载可独立演进的后端能力。
- `backend/__init__.py`
  - 新增包初始化文件。
- `backend/history_stats.py`
  - 新增 `HistoryStatsMixin`。
  - 新增历史持久化文件 `history_usage.json`，保存 `tracked_since`、`last_synced_at`、`total_tokens` 和小时桶。
  - 新增 `_ensure_history_tracking_for_current_groups()`：首次发现 `limited_groups` 中的新群号时建立追踪记录。
  - 新增 `_maybe_sync_history_stats()`：通过异步锁串行同步；非强制同步按 5 分钟节流并复用内存缓存，强制同步用于配置保存和历史弹窗。
  - 新增 `_sync_history_group()`：从 AstrBot `ProviderStat` 查询每小时绝对桶值，覆盖最近 2 小时窗口，避免重复累加并修正延迟写入。
  - 新增 `api_get_history()`：返回历史统计下拉菜单、状态圆点数据、Top N 或趋势柱状图数据。
  - 新增按小时、按日、按月的历史桶聚合函数。
- `main.py`
  - 引入 `HistoryStatsMixin`，`Main` 继承改为 `class Main(HistoryStatsMixin, Star)`。
  - 初始化时解析 `history_stats_path` 并为当前 `limited_groups` 建立历史追踪。
  - 新增 `initialize()` / `terminate()`，插件启用时启动每小时后台历史同步，禁用或重载时取消任务。
  - 注册 `GET /astrbot_plugin_token_limit/history` Web API。
  - `api_save_config()` 保存配置后强制同步历史统计，确保新群号立即拥有追踪起点。
  - `api_get_usage()` 和 `on_waiting_llm_request()` 增加节流历史同步，使已追踪群即使后续从限流列表移除也能继续补齐统计。
- `pages/dashboard/index.html`
  - 在“插件功能”中新增蓝色“历史 token 用量统计”按钮，位于“用量超限策略配置”下方。
  - 新增 `#historyOverlay` 历史统计弹窗。
  - 新增自绘群聊下拉菜单：展示当前限流群号、备注、每日 token 用量和绿/黄/红状态圆点。
  - 新增自绘时间跨度下拉菜单：`近 24 小时`、`近 7 天`、`近一个月`、`历史总和`。
  - 新增动态柱状图：未选择群聊时展示历史总量 Top N；选择群聊后展示对应时间跨度趋势。
  - 柱状图横纵坐标随数据变化，柱顶显示数值，并使用高度过渡动画切换数据。
- `README.md`
  - 新增历史统计功能、持久化策略和 Plugin Page 入口说明。
- `STRUCTURE.md`
  - 更新到 v0.4.0，补全后端 mixin、历史数据文件、`history` API、页面元素映射和函数职责。

## 0.3.1 - 2026-06-07

修复回退策略下配置变更后硬上限失效的问题。

- `metadata.yaml`
  - 版本号更新为 `0.3.1`。
- `_conf_schema.json`
  - 更新 `daily_token_limit` 和 `fallback_token_limit` 提示，明确当前统计窗口内总用量与硬上限规则。
- `main.py`
  - 新增 `_query_split_usage_for_group()`，集中拆分原始供应商用量和回退供应商用量。
  - 新增 `_build_limit_state()`，统一计算 `normal`、`fallback`、`stopped` 三种状态。
  - 新增 `_build_event_limit_context()`，让等待 LLM 阶段和 LLM 请求阶段共用同一套限流上下文。
  - 新增 `on_waiting_llm_request()`，在 AstrBot 选择 provider 和构建 agent 之前写入 `selected_provider`，修复回退区间仍使用原始模型的问题。
  - 修复请求判断口径：
    - `used < daily_token_limit` 时使用原始模型。
    - 选择回退策略时，`daily_token_limit <= used < daily_token_limit + fallback_token_limit` 进入回退区间。
    - 回退供应商有效时强制使用回退供应商；回退供应商失效时交由 AstrBot 使用当前可用供应商。
    - `used >= hard_limit` 时必须阻止该群所有 LLM 调用。
    - 选择停止调用策略时，`used >= daily_token_limit` 必须阻止该群所有 LLM 调用。
  - `on_llm_request()` 保留硬上限兜底拦截，不再承担 provider 选择职责，因为该钩子触发时 AstrBot 已完成 provider 选择。
  - `_build_usage_payload()` 改为使用同一套状态计算逻辑，返回 `stopped`、`status`、`hard_limit_tokens`、`hard_limit_display`。
  - 硬上限随当前配置实时变化，用户调低上限后下一次请求立即生效。
- `pages/dashboard/index.html`
  - 新增 `.stop-tag`、`.usage-value.stopped`、`.progress-fill.stopped`。
  - 用量统计中达到硬上限时显示红色“停止响应”标签。
  - 达到硬上限时 token 用量值字体变红，进度条变红。
  - 红色停止状态优先于黄色回退状态。
- `STRUCTURE.md`
  - 更新到 v0.3.1，补全硬上限规则、三态状态机、页面红色状态映射和新增函数职责。

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
- LLM 请求钩子与 Plugin Page 用量状态必须共用同一套限流状态计算规则。
- 历史统计使用 AstrBot 原生 `ProviderStat` 作为数据源，插件只保存小时级绝对桶值和总量，不维护独立请求明细。
