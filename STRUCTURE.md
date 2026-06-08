# STRUCTURE

本文档记录 v0.6.1 版本的插件结构、内部 API、页面元素映射和主要函数职责。

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
│   ├── history_stats.py
│   ├── user_limits.py
│   └── user_stats.py
└── pages/
    └── dashboard/
        └── index.html
```

运行时在 AstrBot 插件数据目录下生成：

```text
<AstrBot plugin data>/astrbot_plugin_token_limit/
├── group_remarks.json
├── group_limits.json
├── history_usage.json
└── user_usage_48h.json
```

- `group_remarks.json`：保存 QQ 群号到备注名的映射，不跟随 `limited_groups` 删除而删除。
- `group_limits.json`：保存 QQ 群号到个性化每日 token 上限的映射；一旦保存即覆盖全局 `daily_token_limit`，不随后续全局上限变化。
- `history_usage.json`：保存历史 token 用量，包含每个被追踪群的 `tracked_since`、`last_synced_at`、`total_tokens` 和非零小时桶 `hours`。
- `user_usage_48h.json`：保存近 48 小时的群内用户 token 用量小时桶和尽量缓存到的 QQ 昵称，超过 48 小时的数据会在同步时丢弃。

## 元数据与配置

### metadata.yaml

- `name`：插件名称，当前为 `astrbot_plugin_token_limit`。
- `version`：当前版本 `0.6.1`。
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
| `user_daily_token_limit` | 单个群聊内单个用户当前统计窗口 token 上限；`-1` 表示不启用。 |
| `over_limit_policy.action` | 超限策略：`stop_llm` 或 `fallback_provider`。 |
| `over_limit_policy.fallback_provider_id` | 回退模型供应商 ID。 |
| `over_limit_policy.fallback_token_limit` | 回退模型额外 token 上限；硬上限为 `daily_token_limit + fallback_token_limit`。 |
| `over_limit_policy.block_wake_words_after_limit` | 超过群聊基础每日上限后是否阻断唤醒词触发；`@bot` 仍可继续进入回退或停止响应策略。 |
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
- `GROUP_LIMITS_FILE`：群聊个性化每日上限文件名。
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

`class Main(UserLimitMixin, UserStatsMixin, HistoryStatsMixin, Star)` 组合单用户限流、今日用户统计、历史统计 mixin 和 AstrBot `Star`。

`__init__(context, config)`：

- 保存 `Context` 和配置对象。
- 解析 `group_remarks.json`、`history_usage.json` 与 `user_usage_48h.json` 路径。
- 解析 `group_limits.json` 路径。
- 初始化 `_history_sync_lock` 与 `_user_sync_lock`，避免多个请求并发同步同一持久化统计文件。
- 调用 `_ensure_history_tracking_for_current_groups()`，让当前配置中的群号在插件启动时开始历史追踪。
- 调用 `_ensure_user_tracking_for_current_groups()`，让当前配置中的群号在插件启动时建立今日用户统计结构。
- 注册 Web API：
  - `GET /astrbot_plugin_token_limit/config`
  - `POST /astrbot_plugin_token_limit/config`
  - `GET /astrbot_plugin_token_limit/usage`
  - `GET /astrbot_plugin_token_limit/history`
  - `GET /astrbot_plugin_token_limit/user-usage`
  - `GET /astrbot_plugin_token_limit/providers`
  - `GET /astrbot_plugin_token_limit/remarks`
  - `POST /astrbot_plugin_token_limit/remarks`
  - `GET /astrbot_plugin_token_limit/group-settings`
  - `POST /astrbot_plugin_token_limit/group-settings`

`initialize()`：

- 插件启用后启动历史统计与今日用户统计后台同步任务。

`terminate()`：

- 插件禁用或重载时取消历史统计与今日用户统计后台同步任务。

### 配置与备注函数

- `_resolve_group_remarks_path()`：优先使用 `StarTools.get_data_dir()`，失败时回退插件目录。
- `_load_group_remarks()` / `_save_group_remarks()`：读写备注 JSON。
- `_sanitize_group_remark()`：裁剪备注。
- `_resolve_group_limits_path()`：与备注文件同目录存放群聊个性化上限文件。
- `_load_group_limits()` / `_save_group_limits()`：读写 `group_limits.json`，按群号保存非负整数 token 上限。
- `_config_value()`：读取配置，缺省时使用 schema 默认值。
- `_serialize_config()`：输出完整配置快照。
- `_sanitize_config()`：校验并标准化所有配置项；`user_daily_token_limit` 最小值为 `-1`，`-1` 表示关闭单用户限流。
- `_sanitize_over_limit_policy()`：校验超限策略，回退策略必须填写且能找到供应商，并保存“超限后不再响应唤醒词”开关。
- `_normalize_config_list()`：标准化列表型配置。

### 限流目标识别

- `_limited_groups()`：读取并去重限流 QQ 群号。
- `_qq_platform_names()`：读取 QQ 平台适配器名称集合。
- `_qq_platform_ids()`：从 AstrBot platform manager 解析平台实例 ID；无法解析时回退平台名称。
- `_is_enabled()`：判断插件是否启用。
- `_is_qq_group_event(event)`：判断是否为目标 QQ 平台群聊消息。
- `_event_get_extra(event, key)`：兼容读取 AstrBot 事件 `extra` 数据，失败时返回空。
- `_event_truthy_attr(event, name)`：兼容读取事件布尔属性或无参方法。
- `_event_has_at_bot(event)`：尽量通过事件属性、消息链 At 组件和原始消息判断是否由 `@bot` 触发；识别为 `@bot` 时不会被唤醒词开关阻断。
- `_is_wake_word_invocation(event)`：在非 `@bot` 触发前提下，识别唤醒词触发事件。
- `_should_block_wake_word_invocation(event, limit_context)`：当开关启用且群聊用量达到有效基础上限时，判断本次唤醒词触发是否需要阻断。
- `_umo_candidates_for_group(group_id)`：生成标准 `umo` 候选值。
- `_unique_session_like_patterns(group_id)`：生成兼容会话隔离的 `LIKE` 匹配规则。

### 用量、回退和硬上限

- `_daily_limit()`：读取基础 token 上限。
- `_daily_limit_for_group(group_id, group_limits=None)`：读取某个群聊的有效基础上限；存在个性化上限时优先使用 `group_limits.json`，否则回退全局 `daily_token_limit`。
- `_over_limit_policy()`：合并并清洗超限策略，包括回退配置和唤醒词阻断开关。
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
- `_build_usage_payload()`：生成 Plugin Page 当前窗口用量数据，包括备注、群聊有效上限、是否使用个性化上限、状态、硬上限、回退标签所需字段和小时桶。

### Web API 函数

| 函数 | endpoint | 作用 |
| --- | --- | --- |
| `api_get_config()` | `GET config` | 返回 `{config, schema}`。 |
| `api_save_config()` | `POST config` | 保存配置并强制同步一次历史统计。 |
| `api_get_usage()` | `GET usage` | 节流同步历史统计和今日用户统计，并返回当前窗口用量。 |
| `api_get_history()` | `GET history` | 由 `HistoryStatsMixin` 提供，返回历史下拉菜单和柱状图数据。 |
| `api_get_user_usage()` | `GET user-usage` | 由 `UserStatsMixin` 提供，返回当前刷新周期内某群 Top N 用户 token 用量排行。 |
| `api_get_providers()` | `GET providers` | 返回可用回退供应商列表。 |
| `api_get_remarks()` | `GET remarks` | 返回备注映射。 |
| `api_save_remark()` | `POST remarks` | 保存或删除备注。 |
| `api_get_group_settings()` | `GET group-settings` | 返回某个群聊的有效每日上限、全局上限和是否已设置个性化上限。 |
| `api_save_group_settings()` | `POST group-settings` | 保存某个群聊的个性化每日上限到 `group_limits.json`。 |

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
  - 先调用 `_remember_user_usage_event()` 尽量缓存群内用户 QQ 昵称。
  - 调用 `_block_user_daily_limit_if_needed()`；启用单用户上限且该用户在该群当前窗口用量达到上限时，静默 `event.stop_event()`，不进入回退模型，也不发送群聊提示。
  - 先调用 `_maybe_sync_history_stats()`，按 5 分钟节流补齐历史统计。
  - 调用 `_maybe_sync_user_stats()`，按 2 分钟节流补齐近 48 小时用户统计。
  - 在 AstrBot 选择 provider 之前计算限流状态。
  - 若 `block_wake_words_after_limit` 启用，且群聊用量已经达到该群有效基础上限，则阻断唤醒词触发事件；`@bot` 触发继续进入后续回退或停止响应策略。
  - 回退区间且回退供应商有效时写入 `event.set_extra("selected_provider", fallback_provider_id)`。
  - 回退供应商失效时不写入，交给 AstrBot 当前可用供应商。
- `on_llm_request(event, req)`：
  - 先补充带 `conversation_id` 的用户请求归因快照，并再次执行单用户上限兜底静默阻断。
  - 复用 `_build_event_limit_context()` 做兜底。
  - 再次执行唤醒词阻断判断，避免等待 LLM 钩子未生效时漏拦。
  - `normal` 和 `fallback` 放行。
  - `stopped` 时按配置发送 `block_message` 并 `event.stop_event()`。

## backend/user_limits.py

`UserLimitMixin` 独立承载“单个用户每日用量上限”的判定逻辑。该 mixin 只在 `user_daily_token_limit >= 0` 时工作；默认 `-1` 不同步、不查询、不拦截，以节约资源。

### Mixin 函数

- `_user_daily_limit()`：读取 `user_daily_token_limit`，非法值按 `-1` 处理。
- `_user_daily_limit_enabled()`：判断单用户限流是否启用。
- `_user_usage_total_for_event(event)`：
  - 仅处理已启用插件、目标 QQ 群聊、群号在 `limited_groups` 内且可获取发送者 ID 的 LLM 事件。
  - 强制同步该群今日用户统计。
  - 合并 ProviderStat 实时聚合结果和 `user_usage_48h.json` 中已归因小时桶，得到该用户在该群当前刷新周期内的 token 总量。
- `_should_block_user_daily_limit(event)`：当用户当前窗口用量达到或超过上限时返回阻断上下文。
- `_block_user_daily_limit_if_needed(event, stage)`：静默阻断该用户本次 LLM 请求，仅写 AstrBot 日志，不发送 `block_message`，不切换回退供应商。

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
- `_format_history_tokens()`：格式化 token，支持指定 `K` / `M` 小数位数。
- `_local_timezone()` / `_now_utc()`：时间工具。
- `_parse_datetime()` / `_iso_utc()` / `_hour_start()`：UTC 小时桶规范化。
- `_month_key()` / `_hour_label()` / `_hour_range_label()` / `_day_range_label()`：图表标签格式化。

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
  - 选择群聊时额外返回 `range_total_tokens` 和 `range_total_display`，用于显示当前时间跨度内该群 token 用量总和。
- `_history_dropdown_groups()`：生成当前 `limited_groups` 下拉菜单数据，状态为 `normal`、`fallback`、`stopped`。
- `_history_top_bars()`：按 `total_tokens` 降序返回 Top N。
- `_history_group_bars()`：按 `24h`、`7d`、`30d`、`all` 分派桶聚合。
- `_history_recent_hour_bars()`：近 24 小时按小时返回原始桶；页面根据宽度动态聚合为 2、3 或 4 小时桶。
- `_history_recent_day_bars()`：近 7 天按日展示；近一个月按 3 天聚合，并使用英文月份缩写标签。
- `_history_all_bars()`：历史总和短跨度按日展示，超过 31 天按月展示。
- `_history_hour_values()` / `_history_iter_hours()`：遍历规范化小时桶。
- `_history_bar()`：统一柱状图数据结构，可为近 24 小时和近一个月柱顶数值指定 1 位小数显示。

## backend/user_stats.py

`UserStatsMixin` 独立维护近 48 小时群内用户 token 用量统计，用于 Plugin Page 的“今日用户 token 用量统计”弹窗。

### 常量与数据结构

- `USER_USAGE_STATS_FILE`：持久化文件名 `user_usage_48h.json`。
- `USER_USAGE_RETENTION`：用户小时桶保留时间，当前 48 小时。
- `USER_USAGE_REQUEST_RETENTION`：用户请求归因快照保留时间，当前 48 小时。
- `USER_USAGE_REQUEST_LOOKBACK`：把 ProviderStat 记录回配到最近一次用户请求的最大回看时间，当前 10 分钟。
- `USER_USAGE_REQUEST_FUTURE_TOLERANCE`：允许事件记录时间略晚于 provider `start_time` 的容差，当前 5 秒。
- `USER_USAGE_SYNC_OVERLAP`：同步回看窗口，当前 2 小时，用于修正 AstrBot 延迟写入。
- `USER_USAGE_SYNC_MIN_INTERVAL`：非强制同步最短间隔，当前 2 分钟。
- `USER_USAGE_BACKGROUND_SYNC_INTERVAL`：后台同步间隔，当前 3600 秒。
- `USER_USAGE_DEFAULT_TOP_LIMIT`：默认展示 Top N，当前 10。
- `UserUsageWindow`：今日用户统计查询窗口，按 `refresh_time` 生成当前 24 小时统计周期。

### 模块级工具函数

- `_normalize_user_group_id()` / `_sanitize_user_id()`：标准化群号和用户号。
- `_sanitize_user_name()`：清洗 QQ 昵称或群名片。
- `_format_user_tokens()`：格式化 token 数为 `K` / `M`。
- `_build_user_usage_window()`：按 `refresh_time` 生成当前刷新周期窗口。
- `_extract_user_id_from_umo(umo, group_id)`：从 AstrBot `ProviderStat.umo` 中解析群内用户 ID；支持常见 `用户ID_群号`、`群号_用户ID` 以及带冒号的平台会话格式。
- `_timestamp_to_utc()`：将 AstrBot provider 统计中的 Unix 秒级 `start_time` 转为 UTC 时间，用于请求归因。

### Mixin 函数

- `_resolve_user_stats_path()`：与备注文件同目录存放 `user_usage_48h.json`。
- `_load_user_stats()` / `_save_user_stats()`：读写近 48 小时用户统计 JSON。
- `_sanitize_user_stats()`：清洗历史文件，丢弃超过 48 小时的小时桶和请求归因快照。
- `_ensure_user_tracking_for_current_groups(data=None)`：为当前 `limited_groups` 建立用户统计群结构。
- `_start_user_background_sync()` / `_stop_user_background_sync()`：在插件启停时管理用户统计后台任务。
- `_maybe_sync_user_stats(force=False, group_id=None)`：带锁同步用户统计；非强制同步按 2 分钟节流，打开用户统计弹窗时可按群强制同步。
- `_sync_user_group(group_id, group_data, now)`：查询 AstrBot `ProviderStat`，结合请求归因队列覆盖最近同步窗口内的用户小时桶。
- `_assign_user_usage_records()` / `_match_user_usage_request()`：将 `umo` 只能定位到群会话的 ProviderStat 明细按同 `umo`、同会话 ID（如有）和最近请求时间回配到群内用户 LLM 请求；群聊共用 `conversation_id` 时不会只按会话 ID 合并。
- `_merge_user_hours()`：合并可直接从 `umo` 解析出的小时桶和请求归因得到的小时桶。
- `_prune_user_group_data()`：删除超过 48 小时或即将被重新查询窗口覆盖的旧桶。
- `_prune_user_usage_requests()`：清理超过 48 小时或非法的请求归因快照。
- `_query_hourly_user_usage_for_group()`：查询某群在时间段内的 ProviderStat，返回可直接按用户聚合的小时桶和需要归因的记录明细。
- `_query_user_totals_for_group()`：查询当前刷新周期内某群按用户聚合的 token 总量。
- `_stored_user_totals_for_group()` / `_combine_user_totals()`：将实时 ProviderStat 直接聚合结果和持久化归因小时桶合并为当前窗口排行数据。
- `_remember_user_usage_event(event, conversation_id=None)`：在 LLM 等待钩子和 LLM 请求钩子里尽量从消息事件缓存用户 QQ 昵称，并记录请求归因快照；LLM 请求阶段会补充 `conversation_id`。
- `_event_user_id()` / `_event_user_name()`：兼容不同 AstrBot 事件字段读取用户号与昵称。
- `api_get_user_usage()`：返回群聊下拉菜单、当前窗口、同步时间，以及选中群的用户 Top N 横向柱状图数据。
- `_user_usage_dropdown_groups()`：复用当前用量状态生成用户统计弹窗的群聊下拉菜单。
- `_user_usage_rows()`：将用户 token 总量转为前端排行行，过滤 0 用量用户，昵称缺失时显示 QQ 号；启用单用户上限时附带 `over_user_limit` 供页面标红。

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
  - 齿轮 `.icon-button`：打开“群聊个性化配置”弹窗，为单个群聊保存每日用量上限。
  - `.fallback-tag`：黄色“回退模型”标签。
  - `.stop-tag`：红色“停止响应”标签。
  - `.usage-value.fallback` / `.usage-value.stopped`：黄色/红色用量值。
  - `.progress-fill.fallback` / `.progress-fill.stopped`：黄色/红色进度条。
- 右侧 `.panel`：插件功能。
  - `#openConfigBtn`：打开插件基础配置，位于功能按钮区最上方。
  - `#openStrategyBtn`：打开“用量超限策略配置”。
  - `#openHistoryBtn`：打开“历史 token 用量统计”。
  - `#openUserUsageBtn`：打开“今日用户 token 用量统计”。
  - `#statusLine`：插件启用状态。

### 弹窗元素

- `#overlay`：插件基础配置弹窗。
  - `#configForm`：动态配置表单，不渲染 `over_limit_policy`。
  - `#saveBtn` / `#cancelBtn` / `#toast`：保存、取消和状态。
- `#strategyOverlay`：超限策略弹窗。
  - `#strategyForm`：渲染 `over_limit_policy`。
  - 始终显示“超限后不再响应唤醒词”开关。
  - 仅当 `action=fallback_provider` 时显示回退供应商和回退上限。
- `#historyOverlay`：历史统计弹窗。
  - `#groupSelect` / `#groupSelectTrigger` / `#groupSelectMenu`：自绘群聊下拉菜单。
  - `#rangeSelect` / `#rangeSelectTrigger` / `#rangeSelectMenu`：自绘时间跨度下拉菜单。
  - `#historyRangeTotal`：右侧总量占位；选中群聊后显示该群当前时间跨度内 token 用量总和。
  - `#historyYAxis`：动态纵轴标签。
  - `#historyChart`：柱状图容器。
  - `#historyXAxis`：动态横轴标签。
  - `#historyFooter`：最后同步时间。
- `#userUsageOverlay`：今日用户 token 用量统计弹窗。
  - `#userGroupSelect` / `#userGroupSelectTrigger` / `#userGroupSelectMenu`：自绘群聊下拉菜单，行为与历史统计群聊下拉一致。
  - `#refreshUserUsageBtn`：刷新按钮，保持当前群聊选择并重新请求今日用户 token 用量。
  - `#userUsageWindow`：当前刷新周期窗口文本。
  - `#userUsageChart`：横向柱状图容器，展示选中群聊内 Top N 用户 token 用量；超出 `user_daily_token_limit` 的用户柱子和数值显示为红色。
  - `#userUsageFooter`：最后同步时间。
- `#remarkOverlay`：备注编辑弹窗。
  - `#remarkTarget`、`#remarkInput`、`#saveRemarkBtn`、`#cancelRemarkBtn`、`#remarkToast`。
- `#groupSettingsOverlay`：群聊个性化配置弹窗。
  - `#groupSettingsTarget`：当前配置目标群号。
  - `#groupLimitInput`：该群聊每日 token 上限输入框，默认显示当前有效上限。
  - `#groupSettingsHint`：说明当前值来自全局上限还是个性化上限。
  - `#saveGroupSettingsBtn` / `#cancelGroupSettingsBtn` / `#groupSettingsToast`：保存、取消和状态提示。
- `#historyTooltip`：历史柱状图点击后显示的气泡 tag。
  - `#historyTooltipLabel`：柱子横坐标内容。
  - `#historyTooltipValue`：柱子 token 数值统计量，粗体显示。

### 前端函数

- 通用：`setToast()`、`setStrategyToast()`、`setRemarkToast()`、`formatDate()`、`normalizeTextareaText()`、`normalizeListText()`、`parseListText()`。
- 配置渲染：`renderConfigControl()`、`appendConfigRow()`、`renderConfigForm()`、`renderStrategyForm()`。
- 当前用量：`renderUsage()`、`loadUsage()`。
- 群聊个性化配置：`openGroupSettings()`、`closeGroupSettings()`、`saveGroupSettings()`。
- 历史统计：
  - `historyRangeLabel()`：时间跨度标签。
  - `closeCustomSelects()` / `toggleCustomSelect()`：自绘下拉菜单开合。
  - `statusDotClass()`：绿/黄/红状态圆点。
  - `selectedHistoryGroup()`：当前选中群。
  - `reloadHistory()` / `loadHistory()`：请求 `history` API。
  - `renderHistoryControls()`：渲染两个下拉菜单。
  - `renderHistoryTotal()`：渲染历史弹窗右侧的当前时间跨度用量总和；未选群聊时保持为空。
  - `formatHistoryTokenNumber()`：按指定小数位格式化历史图柱顶数值。
  - `aggregateHistoryBars()`：前端按指定小时数聚合近 24 小时原始小时桶。
  - `resolveHistoryBarsForViewport()`：根据图表可用宽度选择 2、3 或 4 小时聚合粒度。
  - `handleHistoryResize()`：历史弹窗打开时随窗口宽度变化重新计算 24 小时聚合粒度。
  - `showHistoryTooltip()` / `hideHistoryTooltip()`：点击柱状图柱子时，在鼠标位置显示/隐藏完整内容气泡。
  - `renderHistoryChart()`：渲染动态轴、数值标签和柱状图动画。
  - `formatTokenNumber()`：前端轴标签格式化。
- 今日用户统计：
  - `selectedUserUsageGroup()`：读取当前选中的用户统计群聊。
  - `renderUserUsageControls()`：渲染群聊下拉菜单。
  - `renderUserUsageWindow()`：渲染当前刷新周期时间窗口。
  - `renderUserUsageChart()`：渲染横向柱状图；未选择群聊时显示操作提示。
  - `loadUserUsage()` / `reloadUserUsage()`：请求 `user-usage` API。
- 弹窗：`openConfig()`、`closeConfig()`、`openStrategy()`、`closeStrategy()`、`openHistory()`、`closeHistory()`、`openUserUsage()`、`closeUserUsage()`、`openRemark()`、`closeRemark()`、`openGroupSettings()`、`closeGroupSettings()`。
- 保存：`saveConfig()`、`saveStrategy()`、`saveRemark()`、`saveGroupSettings()`。
- `init()`：等待 bridge ready 后加载配置和当前用量。

### 页面交互规则

- 所有按钮都有 `:hover` 与 `:active` 颜色/位移反馈。
- 备注显示在群号右侧，格式为 `（备注）`；铅笔图标跟在群号或备注右侧。
- 用量统计每个群聊的铅笔按钮后方显示齿轮按钮；点击后可保存该群聊个性化每日用量上限。
- 群聊个性化上限保存后立即影响当前用量进度条、回退/停止状态和 LLM 请求限流判断；其他群聊继续使用全局上限。
- 开启“超限后不再响应唤醒词”后，群聊用量达到该群有效基础每日上限时，唤醒词触发不再进入 LLM 流程；`@bot` 触发仍会继续执行回退模型或停止响应规则。
- 配置 textarea 会把保存值中的显式 `\n` 渲染为真实换行。
- 历史统计群聊下拉菜单中，状态圆点放在每日 token 用量数字前方：绿色正常、黄色回退、红色停止响应。
- 未选择群聊时，历史图展示历史总 token Top N 群聊。
- 选择群聊后，按 `近 24 小时`、`近 7 天`、`近一个月`、`历史总和` 展示趋势。
- 每次重新打开历史统计弹窗时，群聊下拉菜单恢复为“选择群聊 ...”，时间跨度恢复为“近 24 小时”，图表恢复历史总 token Top N。
- 近 24 小时柱状图由页面按宽度动态选择聚合粒度：优先 2 小时 12 根柱；空间不足时降为 3 小时 8 根柱；仍不足时降为 4 小时 6 根柱。
- 近一个月柱状图按 3 天聚合，横坐标月份使用英文缩写，例如 `Jun 06-08`；近 24 小时和近一个月柱顶数值保留 1 位小数，其他口径保持原有小数位。
- 选中群聊后，两个下拉菜单右侧显示所选时间跨度内该群 token 用量总和。
- 点击历史柱状图中的任一柱子会显示气泡 tag，第一行为横坐标，第二行为 token 用量值；文本强制完整显示，宽度随最长文本行自适应。
- 柱状图切换数据时通过高度过渡动画平滑变化；横纵坐标和柱顶数值由数据动态生成。
- 今日用户 token 用量统计弹窗默认显示“选择群聊 ...”和操作提示；选中群聊后展示当前刷新周期内 token 消耗最高的 Top N 用户。
- 今日用户统计使用横向柱状图，纵向标签为 QQ 昵称；无法获取昵称时显示 QQ 号；消耗量为 0 的用户不显示。柱子按最长纵坐标文字统一确定左侧起点，紧贴标签右侧对齐。启用单用户上限且用户用量达到上限时，该用户柱子和 token 数值为红色。
- 今日用户统计弹窗每次打开、选择群聊或点击“刷新”都会重新请求后端；后端会强制同步选中群聊的 ProviderStat 和请求归因数据。

## 配置与统计同步逻辑

- 当前窗口限流统计使用 `refresh_time` 切分 24 小时窗口。
- 群聊个性化上限只覆盖基础 `daily_token_limit`；回退模型额外上限仍来自全局 `over_limit_policy.fallback_token_limit`；唤醒词阻断阈值使用该群最终有效基础上限。
- 单用户上限 `user_daily_token_limit` 只按“某群内某用户”统计，不跨群合并；达到上限后静默阻断该用户发起的 LLM 请求，不使用回退模型，也不发送群聊提示。
- 历史统计不依赖 `refresh_time`；它以群号首次加入 `limited_groups` 的时间为起点，按小时桶持久化。
- 历史同步基于 AstrBot 原生 `ProviderStat`，保存的是每小时绝对桶值，不是累加 delta。
- 今日用户统计也基于 AstrBot 原生 `ProviderStat`；持久化文件保留近 48 小时群内用户小时桶、请求归因快照和昵称缓存，不跨群合并同一个用户。
- 配置保存会强制同步一次历史统计；页面 `usage` 和 LLM 等待钩子会节流同步。
- 配置保存会强制同步一次今日用户统计；页面 `usage` 和 LLM 等待钩子会节流同步，打开用户统计弹窗时会按选中群强制同步。
- 旧群号不会因为从 `limited_groups` 移除而从 `history_usage.json` 删除，因此再次加入时历史总量和趋势可以继续显示。
