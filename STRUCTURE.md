# STRUCTURE

本文档记录 v0.3.0 版本的插件结构、内部 API、页面元素映射和主要函数职责。

## 文件结构

```text
astrbot_plugin_token_limit/
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── README.md
├── DEVELOP.md
├── STRUCTURE.md
├── astrbot_plugin_token_limit_v0.2.0.zip
├── astrbot_plugin_token_limit_v0.2.0b.zip
├── astrbot_plugin_token_limit/
│   └── LICENSE
└── pages/
    └── dashboard/
        └── index.html
```

运行时还会在 AstrBot 插件数据目录下生成：

```text
<AstrBot plugin data>/astrbot_plugin_token_limit/
└── group_remarks.json
```

`group_remarks.json` 保存 QQ 群号到备注名的映射，不跟随 `limited_groups` 删除而删除。

## 元数据与配置

### metadata.yaml

- `name`：插件名称，当前为 `astrbot_plugin_token_limit`。
- `description` / `short_desc`：插件描述。
- `version`：当前版本 `0.3.0`。
- `support_platforms`：默认支持 `aiocqhttp`、`qq_official`、`qq_official_webhook`。
- `astrbot_version`：最低 AstrBot 版本要求。
- `pages`：声明 `dashboard` Plugin Page，页面文件位于 `pages/dashboard/index.html`。

### _conf_schema.json

供 AstrBot 原生 WebUI 插件配置界面使用。当前配置项：

- `enabled`：插件总开关。
- `limited_groups`：限流 QQ 群号列表。
- `daily_token_limit`：单群每日原始模型 token 上限。
- `over_limit_policy`：用量超限时的措施配置集合。
  - `action`：`stop_llm` 或 `fallback_provider`。
  - `fallback_provider_id`：回退模型供应商 ID。
  - `fallback_token_limit`：回退模型额外 token 上限。
- `refresh_time`：每日统计窗口刷新时间。
- `qq_platform_names`：QQ 平台适配器名称白名单。
- `match_unique_session`：是否兼容 `unique_session` 形式的 `umo`。
- `block_message`：达到停止调用条件时发送的提示。
- `send_block_message`：是否发送提示。

`main.py` 中的 `CONFIG_SCHEMA` 与 `_conf_schema.json` 保持字段一致。Plugin Page 通过后端 `GET config` 获取运行时 schema，并为 `fallback_provider_id` 注入当前已加载供应商的下拉选项。

## main.py

### 常量

- `PLUGIN_NAME`：插件目录/逻辑名称。
- `GROUP_REMARKS_FILE`：群备注持久化文件名。
- `MAX_GROUP_REMARK_LENGTH`：备注最大长度，当前 64。
- `OVER_LIMIT_STOP`：停止调用 LLM 的策略值 `stop_llm`。
- `OVER_LIMIT_FALLBACK`：回退到其他模型的策略值 `fallback_provider`。
- `TOKEN_FIELDS_SUM`：AstrBot 原生 token 字段求和表达式。
- `CONFIG_SCHEMA`：后端配置 schema，供 Plugin Page 动态渲染和保存校验使用。

### 数据结构

- `UsageWindow`
  - `start_local` / `end_local`：本地时区窗口起止。
  - `start_utc` / `end_utc`：查询数据库使用的 UTC 起止。

### 模块级工具函数

- `_ok(data=None, message=None)`：生成成功 API 响应。
- `_error(message)`：生成失败 API 响应。
- `_split_group_values(value)`：把 list、字符串、数字输入拆成字符串列表，兼容逗号、分号、空格、中文标点和换行。
- `_normalize_group_id(value)`：标准化群号，去除空白并兼容 `123.0` 形式。
- `_escape_like(value)`：转义 SQL `LIKE` 通配符。
- `_format_tokens(value)`：将 token 数格式化为 `K` / `M` 展示文本。
- `_parse_refresh_time(value)`：解析 `HH:MM`，非法值回退 `00:00`。
- `_local_timezone()`：获取 AstrBot 运行机器本地时区。
- `_build_usage_window(refresh_time)`：根据刷新时间生成当前 24 小时统计窗口。

### Main 类初始化

- `__init__(context, config)`
  - 保存 AstrBot 注入的 `Context` 和配置对象。
  - 解析群备注文件路径。
  - 注册 Web API：
    - `GET /astrbot_plugin_token_limit/config`
    - `POST /astrbot_plugin_token_limit/config`
    - `GET /astrbot_plugin_token_limit/usage`
    - `GET /astrbot_plugin_token_limit/providers`
    - `GET /astrbot_plugin_token_limit/remarks`
    - `POST /astrbot_plugin_token_limit/remarks`

### 配置与备注函数

- `_resolve_group_remarks_path()`：优先使用 `StarTools.get_data_dir()`，失败时回退到插件目录。
- `_load_group_remarks()`：读取并清洗备注 JSON。
- `_save_group_remarks(remarks)`：保存备注 JSON。
- `_sanitize_group_remark(value)`：裁剪备注长度。
- `_config_value(key)`：读取已保存配置，缺省时使用 `CONFIG_SCHEMA.default`。
- `_serialize_config()`：返回完整配置快照。
- `_sanitize_config(raw_config)`：校验并标准化所有配置项。
- `_sanitize_over_limit_policy(raw_policy)`：校验超限策略，回退策略必须有可用供应商 ID。
- `_normalize_config_list(value)`：标准化列表型配置。

### 限流目标识别

- `_limited_groups()`：读取并去重限流 QQ 群号。
- `_qq_platform_names()`：读取 QQ 平台适配器名称集合。
- `_qq_platform_ids()`：从 AstrBot platform manager 解析已加载平台实例 ID；无法解析时回退到平台名称。
- `_is_enabled()`：判断插件是否启用。
- `_is_qq_group_event(event)`：判断当前事件是否为目标 QQ 平台群聊消息。
- `_umo_candidates_for_group(group_id)`：构造标准 `umo` 候选值。
- `_unique_session_like_patterns(group_id)`：构造兼容 `unique_session` 的 `LIKE` 匹配规则。

### 用量与回退策略函数

- `_daily_limit()`：读取每日原始模型 token 上限。
- `_over_limit_policy()`：读取并合并超限策略默认值。
- `_fallback_provider_id()`：当策略为回退时返回供应商 ID。
- `_fallback_token_limit()`：读取回退模型 token 上限。
- `_fallback_provider_exists(provider_id)`：校验供应商存在且支持 `text_chat`。
- `_provider_options()`：从 `Context.get_all_providers()` 生成回退供应商选项，字段为 `id`、`label`、`type`、`model`。
- `_config_schema_for_page()`：深拷贝 `CONFIG_SCHEMA`，并给 `over_limit_policy.fallback_provider_id` 注入运行时供应商 `options` 和 `option_labels`。
- `_query_usage_for_group(group_id, window, provider_id=None, exclude_provider_id=None)`：
  - 查询 `ProviderStat`。
  - 可指定只统计某供应商，也可排除某供应商。
  - 返回窗口总 token 和小时桶统计。
- `_build_usage_payload()`：
  - 生成 Plugin Page 用量响应。
  - 启用回退策略时拆分原始模型用量和回退模型用量。
  - 当原始模型用量达到每日上限且仍有回退额度时，标记 `using_fallback=true`。
  - 一旦进入回退窗口，页面总上限使用 `daily_token_limit + fallback_token_limit`。

### Web API 函数

- `api_get_config()`
  - 返回 `{config, schema}`。
  - `schema` 会包含 Plugin Page 可用的供应商下拉选项。
- `api_save_config()`
  - 接收 `{"config": {...}}` 或直接配置对象。
  - 调用 `_sanitize_config()` 后更新 AstrBot 插件配置。
  - 如配置对象支持 `save_config()`，立即持久化。
- `api_get_usage()`
  - 返回当前窗口内所有限流群的用量、备注、窗口和超限策略状态。
- `api_get_providers()`
  - 返回当前可用于回退的聊天模型供应商列表。
- `api_get_remarks()`
  - 返回全部群备注。
- `api_save_remark()`
  - 接收 `group_id` 和 `remark`。
  - 空备注会删除该群备注记录。

### LLM 请求钩子

- `on_llm_request(event, req)`
  - 非启用、非 QQ 群、非限流群、上限小于等于 0 时直接返回。
  - 查询当前群原始模型用量。
  - 原始模型用量未达到 `daily_token_limit` 时直接返回。
  - 策略为 `fallback_provider` 且回退供应商有效、回退额度未耗尽时：
    - 调用 `event.set_extra("selected_provider", fallback_provider_id)`。
    - 放行本次请求，由 AstrBot 使用回退供应商生成回复。
  - 策略为 `stop_llm`，或回退供应商无效，或回退额度已耗尽时：
    - 按配置发送 `block_message`。
    - 调用 `event.stop_event()` 阻止本次 LLM 请求。

## Web API

Plugin Page 通过 `window.AstrBotPluginPage` bridge 调用，实际路径由 AstrBot 映射到 `/api/plug/astrbot_plugin_token_limit/<endpoint>`。

| 方法 | endpoint | 作用 |
| --- | --- | --- |
| `GET` | `config` | 获取当前配置和动态 schema。 |
| `POST` | `config` | 保存插件配置。 |
| `GET` | `usage` | 获取当前统计窗口、群用量和回退状态。 |
| `GET` | `providers` | 获取可选回退供应商列表。 |
| `GET` | `remarks` | 获取群备注映射。 |
| `POST` | `remarks` | 保存或删除群备注。 |

统一响应结构：

```json
{
  "status": "ok",
  "message": null,
  "data": {}
}
```

失败时 `status` 为 `error`，`message` 为错误说明。

## pages/dashboard/index.html

### 页面结构

- `.app`：页面根容器。
- `.layout`：左右两栏布局。
- 左侧 `.panel`：用量统计面板。
  - `#windowText`：当前统计窗口。
  - `#refreshBtn`：手动刷新用量。
  - `#usageList`：群用量列表容器。
  - `.usage-row`：单个群聊用量行。
  - `.group-info`：群号、备注、编辑按钮组合。
  - `.group-id`：QQ 群号。
  - `.group-remark`：群备注，以浅灰色括号文本紧跟群号显示。
  - `.icon-button`：备注编辑铅笔按钮。
  - `.usage-side`：右侧用量值和回退标签容器。
  - `.fallback-tag`：回退阶段标签。
  - `.usage-value`：用量值。
  - `.progress-track` / `.progress-fill`：进度条。
- 右侧 `.panel`：插件功能面板。
  - `#openStrategyBtn`：打开“用量超限策略配置”弹窗。
  - `#openConfigBtn`：打开“插件配置”弹窗。
  - `#statusLine`：插件启用状态。

### 弹窗元素映射

- `#overlay`：插件配置弹窗遮罩。
  - `#configForm`：按 schema 动态渲染普通配置项，不渲染 `over_limit_policy`。
  - `#saveBtn`：保存普通配置。
  - `#cancelBtn`：关闭普通配置弹窗。
  - `#toast`：普通配置保存状态或错误。
- `#strategyOverlay`：用量超限策略弹窗遮罩。
  - `#strategyForm`：渲染 `over_limit_policy` 配置集合。
  - `#saveStrategyBtn`：保存超限策略。
  - `#cancelStrategyBtn`：关闭超限策略弹窗。
  - `#strategyToast`：超限策略保存状态或错误。
- `#remarkOverlay`：群备注弹窗遮罩。
  - `#remarkTarget`：显示正在编辑的 QQ 群号。
  - `#remarkInput`：备注输入框。
  - `#saveRemarkBtn`：保存备注。
  - `#cancelRemarkBtn`：关闭备注弹窗。
  - `#remarkToast`：备注保存状态或错误。

### 前端函数

- `setToast()` / `setStrategyToast()` / `setRemarkToast()`：写入对应弹窗状态文本。
- `createPencilIcon()`：创建铅笔图标。
- `formatDate(value)`：格式化窗口时间。
- `normalizeTextareaText(value)`：把字符串中的显式 `\n` 渲染为真实换行。
- `normalizeListText(value)`：列表配置转 textarea 内容。
- `parseListText(value)`：textarea 内容转列表。
- `inputTypeFor(meta)`：按 schema 类型决定输入框类型。
- `optionLabel(meta, option, index)`：读取选项显示名。
- `renderConfigControl(key, meta, draft, onChange)`：按 schema 渲染 select、switch、textarea 或 input。
- `appendConfigRow(container, key, meta, draft, onChange)`：渲染一行配置项。
- `renderConfigForm()`：渲染普通插件配置。
- `renderStrategyForm()`：渲染超限策略配置；只有选择 `fallback_provider` 时才显示回退供应商和回退上限。
- `renderUsage(payload)`：渲染群用量、备注、回退标签和进度条颜色。
- `loadConfig()`：读取配置和 schema。
- `loadUsage()`：读取用量统计。
- `openConfig()` / `closeConfig()`：打开或关闭普通配置弹窗。
- `openStrategy()` / `closeStrategy()`：打开或关闭超限策略弹窗。
- `openRemark()` / `closeRemark()`：打开或关闭备注弹窗。
- `saveConfig()`：保存普通配置。
- `saveStrategy()`：保存 `over_limit_policy`。
- `saveRemark()`：保存群备注。
- `init()`：等待 bridge ready 后加载配置和用量。

### 页面交互规则

- 所有按钮都有 `:hover` 和 `:active` 状态，鼠标悬停和点击会产生颜色或位移反馈。
- 备注显示在 QQ 群号右侧，以 `（备注）` 形式渲染；铅笔按钮跟在群号或备注右侧。
- 普通配置弹窗中的 textarea 会把保存值里的 `\n` 字符串转换为真实换行显示。
- 回退策略弹窗中，未选择“回退到其他模型”时隐藏回退供应商和回退上限。
- 群聊处于回退阶段时，进度条、用量字体和标签均使用黄色视觉状态。

## 配置同步逻辑

原生 WebUI 使用 `_conf_schema.json` 生成配置界面，AstrBot 将配置对象注入 `Main.__init__(..., config=plugin_config)`。Plugin Page 保存时通过 bridge 调用 `config` endpoint，后端更新同一个 `self.config` 并调用 `save_config()`。

- 原生 WebUI 保存后，Plugin Page 下一次读取 `config` endpoint 会看到新值。
- Plugin Page 保存后，原生 WebUI 刷新插件配置页会看到新值。
- Plugin Page 的供应商下拉来自运行时 `Context.get_all_providers()`；原生 WebUI 的静态 schema 使用供应商 ID 字段，由后端保存时校验供应商是否存在。
