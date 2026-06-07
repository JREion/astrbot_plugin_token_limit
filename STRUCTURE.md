# STRUCTURE

本文档记录 v0.4.0 版本的插件结构、内部 API、页面元素映射和主要函数职责。

## 文件结构

```text
astrbot_plugin_token_limit/
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── README.md
├── DEVELOP.md
├── STRUCTURE.md
├── LICENSE
├── backend/
│   ├── __init__.py
│   └── history_stats.py
└── pages/
    └── dashboard/
        └── index.html
```

运行时在 AstrBot 插件数据目录下生成：

```text
<AstrBot plugin data>/astrbot_plugin_token_limit/
├── group_remarks.json
└── history_usage.json
```

- `group_remarks.json`：保存 QQ 群号到备注名的映射，不跟随 `limited_groups` 删除而删除。
- `history_usage.json`：保存历史 token 用量，包含每个被追踪群的 `tracked_since`、`last_synced_at`、`total_tokens` 和非零小时桶 `hours`。

## 元数据与配置

### metadata.yaml

- `name`：插件名称，当前为 `astrbot_plugin_token_limit`。
- `version`：当前版本 `0.4.0`。
- `repo`：插件仓库地址。
- `support_platforms`：默认支持 `aiocqhttp`、`qq_official`、`qq_official_webhook`。
- `pages`：声明 `dashboard` Plugin Page，页面文件为 `pages/dashboard/index.html`。

### _conf_schema.json

原生 WebUI 配置项：

| 配置项 | 功能 |
| --- | --- |
| `enabled` | 插件总开关。 |
| `limited_groups` | 需要限流的 QQ 群号列表；新群号会从加入时刻开始历史统计。 |
| `daily_token_limit` | 单群当前统计窗口内基础 token 上限。 |
| `over_limit_policy.action` | 超限策略：`stop_llm` 或 `fallback_provider`。 |
| `over_limit_policy.fallback_provider_id` | 回退模型供应商 ID。 |
| `over_limit_policy.fallback_token_limit` | 回退模型额外 token 上限；硬上限为 `daily_token_limit + fallback_token_limit`。 |
| `refresh_time` | 当前窗口刷新时间，按 AstrBot 机器本地时区计算。 |
| `qq_platform_names` | QQ 平台适配器名称白名单。 |
| `match_unique_session` | 是否兼容 `unique_session` 形式的 `umo`。 |
| `block_message` | 达到停止调用条件时发送的提示。 |
| `send_block_message` | 是否发送提示。 |

`main.py` 的 `CONFIG_SCHEMA` 与 `_conf_schema.json` 保持字段一致。Plugin Page 通过 `GET config` 获取运行时 schema，并动态注入回退供应商下拉选项。

## main.py

### 常量与数据结构

- `PLUGIN_NAME`：插件名称和 Web API 前缀。
- `GROUP_REMARKS_FILE`：备注文件名。
- `MAX_GROUP_REMARK_LENGTH`：备注最大长度，当前 64。
- `OVER_LIMIT_STOP` / `OVER_LIMIT_FALLBACK`：超限策略枚举值。
- `TOKEN_FIELDS_SUM`：AstrBot `ProviderStat` 中输入、缓存输入和输出 token 字段求和表达式。
- `CONFIG_SCHEMA`：后端配置 schema。
- `UsageWindow`：当前限流窗口，包含本地和 UTC 起止时间。

### 模块级工具函数

- `_ok()` / `_error()`：生成统一 API 响应。
- `_split_group_values()`：兼容 list、数字、逗号、空格、分号、中文标点和换行。
- `_normalize_group_id()`：标准化群号，兼容 `123.0`。
- `_escape_like()`：转义 SQL `LIKE` 通配符。
- `_format_tokens()`：格式化 token 数为 `K` / `M`。
- `_parse_refresh_time()`：解析 `HH:MM`。
- `_local_timezone()`：获取运行机器本地时区。
- `_build_usage_window()`：根据 `refresh_time` 生成当前 24 小时限流统计窗口。

### Main 初始化

`class Main(HistoryStatsMixin, Star)` 组合历史统计 mixin 和 AstrBot `Star`。

`__init__(context, config)`：

- 保存 `Context` 和配置对象。
- 解析 `group_remarks.json` 与 `history_usage.json` 路径。
- 初始化 `_history_sync_lock`，避免多个请求并发同步同一历史文件。
- 调用 `_ensure_history_tracking_for_current_groups()`，让当前配置中的群号在插件启动时开始历史追踪。
- 注册 Web API：
  - `GET /astrbot_plugin_token_limit/config`
  - `POST /astrbot_plugin_token_limit/config`
  - `GET /astrbot_plugin_token_limit/usage`
  - `GET /astrbot_plugin_token_limit/history`
  - `GET /astrbot_plugin_token_limit/providers`
  - `GET /astrbot_plugin_token_limit/remarks`
  - `POST /astrbot_plugin_token_limit/remarks`

`initialize()`：

- 插件启用后启动历史统计后台同步任务。

`terminate()`：

- 插件禁用或重载时取消历史统计后台同步任务。

### 配置与备注函数

- `_resolve_group_remarks_path()`：优先使用 `StarTools.get_data_dir()`，失败时回退插件目录。
- `_load_group_remarks()` / `_save_group_remarks()`：读写备注 JSON。
- `_sanitize_group_remark()`：裁剪备注。
- `_config_value()`：读取配置，缺省时使用 schema 默认值。
- `_serialize_config()`：输出完整配置快照。
- `_sanitize_config()`：校验并标准化所有配置项。
- `_sanitize_over_limit_policy()`：校验超限策略，回退策略必须填写且能找到供应商。
- `_normalize_config_list()`：标准化列表型配置。

### 限流目标识别

- `_limited_groups()`：读取并去重限流 QQ 群号。
- `_qq_platform_names()`：读取 QQ 平台适配器名称集合。
- `_qq_platform_ids()`：从 AstrBot platform manager 解析平台实例 ID；无法解析时回退平台名称。
- `_is_enabled()`：判断插件是否启用。
- `_is_qq_group_event(event)`：判断是否为目标 QQ 平台群聊消息。
- `_umo_candidates_for_group(group_id)`：生成标准 `umo` 候选值。
- `_unique_session_like_patterns(group_id)`：生成兼容会话隔离的 `LIKE` 匹配规则。

### 用量、回退和硬上限

- `_daily_limit()`：读取基础 token 上限。
- `_over_limit_policy()`：合并并清洗超限策略。
- `_fallback_provider_id()` / `_fallback_token_limit()`：读取回退供应商和回退额度。
- `_fallback_provider_exists(provider_id)`：检查供应商存在且支持 `text_chat`。
- `_provider_options()`：从 `Context.get_all_providers()` 生成回退供应商选项。
- `_config_schema_for_page()`：向页面 schema 注入 `fallback_provider_id.options`。
- `_query_usage_for_group(group_id, window, provider_id=None, exclude_provider_id=None)`：
  - 查询 AstrBot 原生 `ProviderStat`。
  - 按当前 `umo` 匹配口径统计 token。
  - 返回窗口总量和小时桶。
- `_query_split_usage_for_group()`：
  - 配置回退供应商时，拆分原始供应商用量和回退供应商用量。
  - 未配置回退供应商时，所有用量归入 `primary_used`。
- `_build_limit_state()`：
  - `stop_llm`：`used < limit` 为 `normal`，`used >= limit` 为 `stopped`。
  - `fallback_provider` 且回退额度大于 0：`used < limit` 为 `normal`，`limit <= used < limit + fallback_token_limit` 为 `fallback`，`used >= hard_limit` 为 `stopped`。
  - 回退供应商是否可用不改变硬上限，只影响是否能强制选择该供应商。
- `_build_event_limit_context(event)`：为等待 LLM 和 LLM 请求钩子构造统一限流上下文。
- `_build_usage_payload()`：生成 Plugin Page 当前窗口用量数据，包括备注、状态、硬上限、回退标签所需字段和小时桶。

### Web API 函数

| 函数 | endpoint | 作用 |
| --- | --- | --- |
| `api_get_config()` | `GET config` | 返回 `{config, schema}`。 |
| `api_save_config()` | `POST config` | 保存配置并强制同步一次历史统计。 |
| `api_get_usage()` | `GET usage` | 节流同步历史统计并返回当前窗口用量。 |
| `api_get_history()` | `GET history` | 由 `HistoryStatsMixin` 提供，返回历史下拉菜单和柱状图数据。 |
| `api_get_providers()` | `GET providers` | 返回可用回退供应商列表。 |
| `api_get_remarks()` | `GET remarks` | 返回备注映射。 |
| `api_save_remark()` | `POST remarks` | 保存或删除备注。 |

统一响应结构：

```json
{
  "status": "ok",
  "message": null,
  "data": {}
}
```

### LLM 请求钩子

- `on_waiting_llm_request(event)`：
  - 先调用 `_maybe_sync_history_stats()`，按 5 分钟节流补齐历史统计。
  - 在 AstrBot 选择 provider 之前计算限流状态。
  - 回退区间且回退供应商有效时写入 `event.set_extra("selected_provider", fallback_provider_id)`。
  - 回退供应商失效时不写入，交给 AstrBot 当前可用供应商。
- `on_llm_request(event, req)`：
  - 复用 `_build_event_limit_context()` 做兜底。
  - `normal` 和 `fallback` 放行。
  - `stopped` 时按配置发送 `block_message` 并 `event.stop_event()`。

## backend/history_stats.py

`HistoryStatsMixin` 独立维护历史统计逻辑，避免 `main.py` 继续膨胀。

### 常量

- `HISTORY_STATS_FILE`：持久化文件名 `history_usage.json`。
- `HISTORY_STATS_VERSION`：历史文件结构版本。
- `HISTORY_SYNC_OVERLAP`：同步回看窗口，当前 2 小时，用于修正 AstrBot 延迟写入。
- `HISTORY_SYNC_MIN_INTERVAL`：非强制同步最短间隔，当前 5 分钟。
- `HISTORY_BACKGROUND_SYNC_INTERVAL`：后台同步间隔，当前 3600 秒。
- `HISTORY_DEFAULT_TOP_LIMIT`：未选择群聊时展示 Top N，当前 10。
- `HISTORY_RANGE_KEYS`：`24h`、`7d`、`30d`、`all`。

### 数据结构

- `HistoryUsageWindow`：历史查询窗口，字段与 `UsageWindow` 同名，可复用 `Main._query_usage_for_group()`。

### 模块级工具函数

- `_history_ok()` / `_history_error()`：历史 API 响应。
- `_normalize_history_group_id()`：标准化群号。
- `_format_history_tokens()`：格式化 token。
- `_local_timezone()` / `_now_utc()`：时间工具。
- `_parse_datetime()` / `_iso_utc()` / `_hour_start()`：UTC 小时桶规范化。
- `_month_key()` / `_hour_label()`：图表标签格式化。

### Mixin 函数

- `_resolve_history_stats_path()`：与备注文件同目录存放历史文件。
- `_load_history_stats()` / `_save_history_stats()`：读写历史 JSON。
- `_empty_history_stats()`：生成空结构。
- `_sanitize_history_stats()`：清洗历史文件，移除非法桶，重算 `total_tokens`。
- `_ensure_history_tracking_for_current_groups(data=None)`：
  - 扫描当前 `limited_groups`。
  - 新群号写入 `tracked_since=now`。
  - 不删除旧群号，因此被移除的群仍会继续追踪。
- `_history_background_sync_loop()`：插件启用后每小时强制同步一次历史统计。
- `_start_history_background_sync()`：在 `initialize()` 中创建后台同步任务。
- `_stop_history_background_sync()`：在 `terminate()` 中取消后台同步任务。
- `_maybe_sync_history_stats(force=False)`：
  - 使用 `_history_sync_lock` 串行化历史同步。
  - 非强制调用受 5 分钟节流保护；节流期内且群列表未变化时返回内存缓存，避免重复读写文件。
  - 强制调用用于打开历史弹窗和保存配置。
  - 遍历所有已追踪群，调用 `_sync_history_group()`。
- `_sync_history_stats_locked(force)`：持有锁后的实际同步流程。
- `_sync_history_group(group_id, group_data, now)`：
  - 查询范围为 `last_synced_at - 2h` 到当前时刻；首次同步从 `tracked_since` 开始。
  - 查询起点按小时对齐，首个追踪小时保留从加入时刻开始的部分小时。
  - 删除被查询窗口内旧桶，再写入 AstrBot `ProviderStat` 计算出的新桶。
  - 使用“小时绝对值覆盖”而不是增量累加，避免页面刷新、配置变更或 `refresh_time` 修改导致重复统计。
- `api_get_history()`：
  - 查询参数：`group_id`、`range`、`limit`。
  - 强制同步历史统计。
  - 调用 `_build_usage_payload()` 获取当前限流群下拉菜单、每日用量和状态圆点。
  - 未选择群聊时返回历史总量 Top N。
  - 选择群聊时按时间范围返回趋势柱状图。
- `_history_dropdown_groups()`：生成当前 `limited_groups` 下拉菜单数据，状态为 `normal`、`fallback`、`stopped`。
- `_history_top_bars()`：按 `total_tokens` 降序返回 Top N。
- `_history_group_bars()`：按 `24h`、`7d`、`30d`、`all` 分派桶聚合。
- `_history_recent_hour_bars()`：近 24 小时按小时展示。
- `_history_recent_day_bars()`：近 7 天/近一个月按日展示。
- `_history_all_bars()`：历史总和短跨度按日展示，超过 31 天按月展示。
- `_history_hour_values()` / `_history_iter_hours()`：遍历规范化小时桶。
- `_history_bar()`：统一柱状图数据结构。

## pages/dashboard/index.html

### 页面结构

- `.app` / `.layout`：页面根容器和两栏布局。
- 左侧 `.panel`：用量统计。
  - `#windowText`：当前窗口时间。
  - `#refreshBtn`：刷新当前窗口用量。
  - `#usageList`：群用量列表。
  - `.group-id`：QQ 群号。
  - `.group-remark`：灰色括号备注。
  - `.icon-button`：编辑备注铅笔按钮。
  - `.fallback-tag`：黄色“回退模型”标签。
  - `.stop-tag`：红色“停止响应”标签。
  - `.usage-value.fallback` / `.usage-value.stopped`：黄色/红色用量值。
  - `.progress-fill.fallback` / `.progress-fill.stopped`：黄色/红色进度条。
- 右侧 `.panel`：插件功能。
  - `#openStrategyBtn`：打开“用量超限策略配置”。
  - `#openHistoryBtn`：打开“历史 token 用量统计”。
  - `#openConfigBtn`：打开插件基础配置。
  - `#statusLine`：插件启用状态。

### 弹窗元素

- `#overlay`：插件基础配置弹窗。
  - `#configForm`：动态配置表单，不渲染 `over_limit_policy`。
  - `#saveBtn` / `#cancelBtn` / `#toast`：保存、取消和状态。
- `#strategyOverlay`：超限策略弹窗。
  - `#strategyForm`：渲染 `over_limit_policy`。
  - 仅当 `action=fallback_provider` 时显示回退供应商和回退上限。
- `#historyOverlay`：历史统计弹窗。
  - `#groupSelect` / `#groupSelectTrigger` / `#groupSelectMenu`：自绘群聊下拉菜单。
  - `#rangeSelect` / `#rangeSelectTrigger` / `#rangeSelectMenu`：自绘时间跨度下拉菜单。
  - `#historyYAxis`：动态纵轴标签。
  - `#historyChart`：柱状图容器。
  - `#historyXAxis`：动态横轴标签。
  - `#historyFooter`：最后同步时间。
- `#remarkOverlay`：备注编辑弹窗。
  - `#remarkTarget`、`#remarkInput`、`#saveRemarkBtn`、`#cancelRemarkBtn`、`#remarkToast`。

### 前端函数

- 通用：`setToast()`、`setStrategyToast()`、`setRemarkToast()`、`formatDate()`、`normalizeTextareaText()`、`normalizeListText()`、`parseListText()`。
- 配置渲染：`renderConfigControl()`、`appendConfigRow()`、`renderConfigForm()`、`renderStrategyForm()`。
- 当前用量：`renderUsage()`、`loadUsage()`。
- 历史统计：
  - `historyRangeLabel()`：时间跨度标签。
  - `closeCustomSelects()` / `toggleCustomSelect()`：自绘下拉菜单开合。
  - `statusDotClass()`：绿/黄/红状态圆点。
  - `selectedHistoryGroup()`：当前选中群。
  - `reloadHistory()` / `loadHistory()`：请求 `history` API。
  - `renderHistoryControls()`：渲染两个下拉菜单。
  - `renderHistoryChart()`：渲染动态轴、数值标签和柱状图动画。
  - `formatTokenNumber()`：前端轴标签格式化。
- 弹窗：`openConfig()`、`closeConfig()`、`openStrategy()`、`closeStrategy()`、`openHistory()`、`closeHistory()`、`openRemark()`、`closeRemark()`。
- 保存：`saveConfig()`、`saveStrategy()`、`saveRemark()`。
- `init()`：等待 bridge ready 后加载配置和当前用量。

### 页面交互规则

- 所有按钮都有 `:hover` 与 `:active` 颜色/位移反馈。
- 备注显示在群号右侧，格式为 `（备注）`；铅笔图标跟在群号或备注右侧。
- 配置 textarea 会把保存值中的显式 `\n` 渲染为真实换行。
- 历史统计下拉菜单左侧状态圆点：绿色正常、黄色回退、红色停止响应。
- 未选择群聊时，历史图展示历史总 token Top N 群聊。
- 选择群聊后，按 `近 24 小时`、`近 7 天`、`近一个月`、`历史总和` 展示趋势。
- 柱状图切换数据时通过高度过渡动画平滑变化；横纵坐标和柱顶数值由数据动态生成。

## 配置与统计同步逻辑

- 当前窗口限流统计使用 `refresh_time` 切分 24 小时窗口。
- 历史统计不依赖 `refresh_time`；它以群号首次加入 `limited_groups` 的时间为起点，按小时桶持久化。
- 历史同步基于 AstrBot 原生 `ProviderStat`，保存的是每小时绝对桶值，不是累加 delta。
- 配置保存会强制同步一次历史统计；页面 `usage` 和 LLM 等待钩子会节流同步。
- 旧群号不会因为从 `limited_groups` 移除而从 `history_usage.json` 删除，因此再次加入时历史总量和趋势可以继续显示。
