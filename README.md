</div>

<div align="center">

# astrbot_plugin_token_limit

> v0.6.3：今日用户 token 用量统计新增对话明细。插件会在近 48 小时用户统计 JSON 中记录有效 LLM 请求的时间、用户输入前 20 个字和当次 token 用量；Plugin Page 中点击某个用户柱子可查看“对话数据”表格，并按用量或时间排序。

*_✨ [**AstrBot**](*https://github.com/AstrBotDevs/AstrBot*) 群聊 LLM token 用量限流插件 ✨_*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
![AstrBot >=4.24.2](https://img.shields.io/badge/AstrBot-4.24.2%2B-green.svg)
![Plugin Page](https://img.shields.io/badge/适配-最新_Plugin_Page-orange.svg)
[![GitHub](https://img.shields.io/badge/作者-青尘工作室-cyan)](https://space.bilibili.com/385556208/)

</div>

用于 AstrBot 的 QQ 群聊 LLM token 用量限流插件。

当某个已配置群聊达到单群每日 token 上限后，可以**停止**该群后续 LLM 调用，也可以**切换到一个回退模型**继续回复，并在回退额度耗尽后停止调用。也可以为群内单个用户设置每日 token 上限，超过后静默阻断该用户继续发起 LLM 请求。

支持**可视化查看**当日 token 用量、限流状态、历史统计数据、今日用户用量排行等。

## 💡 功能

- 按 QQ 群号设置限流列表，支持为每个群聊单独配置 `备注名` 和 `用量限额`。
- 按 `用量刷新时间` 切分每日统计窗口，到下一个刷新时间自动重新统计。
- 支持自定义 token 超限策略：
  - `停止调用 LLM`：群聊原始模型用量达到每日上限后，直接拦截后续 LLM 请求。
  - `回退到其他模型`：群聊原始模型用量达到每日上限后，改用配置的回退模型供应商；回退模型消耗达到“回退模型的用量上限”后，再停止该群所有 LLM 调用。
- 提供 Plugin Page 可视化 WebUI 页面，可查看每个群聊 token 用量进度和限流状态。
- 支持群聊历史 token 用量统计，可自由选择时间跨度，以 `柱状图` 形式可视化展示每个群聊的用量统计数据。
- 支持当日群聊内用户 token 用量统计，可选择单个群聊，查看刷新周期内 token 消耗最高的用户排行；点击用户柱状图可查看该用户当前统计窗口内每次有效 LLM 请求的对话摘要、token 用量和时间。
- 支持单个群聊内单个用户每日用量上限；达到上限后只静默阻断该用户的 LLM 请求，不切换回退模型，不发送群聊提示。
- 支持为单个群聊开启“仅通过 @bot 触发 LLM 回复”，开启后该群的唤醒词触发会被静默阻断；同一句消息同时包含 `@bot` 和唤醒词时仍可触发。

## ⚙️ 配置项

#### 基础配置

| 配置项 | 说明 |
| --- | --- |
| `enabled` | 是否启用插件。关闭后不拦截 LLM 请求。 |
| `limited_groups` | 需要限流的 QQ 群号列表。 |
| `daily_token_limit` | 单个群聊每日原始模型 token 上限，单位为 token。 |
| `user_daily_token_limit` | 单个群聊内单个用户每日 token 上限，默认 `-1` 表示不限制。 |
| `refresh_time` | 用量刷新时间，格式 `HH:MM`，按 AstrBot 所在机器本地时区计算。 |
| `qq_platform_names` | 需要识别为 QQ 平台的适配器名称，默认 `aiocqhttp`、`qq_official`、`qq_official_webhook`。 |
| `match_unique_session` | 是否兼容 AstrBot `unique_session` 会话隔离下的历史统计。 |
| `block_message` | 达到停止调用条件后发送到群里的提示文本。 |
| `send_block_message` | 是否发送超限提示；关闭后只静默拦截 LLM 请求。 |

`block_message` 支持变量：`{group_id}`、`{used}`、`{limit}`、`{refresh_time}`、`{window_start}`、`{window_end}`。

#### 用量超限策略配置

| 配置项 | 说明 |
| --- | --- |
| `处理方式` | 用量超限后的措施，可选 `stop_llm` (停止调用 LLM) 或 `fallback_provider` (回退到其他模型)。 |
| `回退的模型供应商` | 回退模型供应商 ID。Plugin Page 可直接选择已加载供应商；原生 WebUI 中需要手动填写供应商 ID。 |
| `回退模型的用量上限` | 原始模型用量超限、切换到回退模型以后，额外还可以再使用的回退模型 token 用量。 |
| `超限后不再响应唤醒词` | 用量超限后，使用唤醒词不会再触发 bot，以节省回退模型的 token，并避免频繁发送超限提示。 |

## 📓 超限策略示例

假设：

- `daily_token_limit = 10000000`
- `over_limit_policy.action = fallback_provider`
- `over_limit_policy.fallback_token_limit = 5000000`

某群当日总用量小于 10M token 时使用原始模型；当日总用量大于等于 10M 且小于 15M token 时，后续 LLM 请求会切换到配置的回退供应商；当日总用量达到 15M token 后，插件会停止该群继续调用任何 LLM 模型。

其他未超限群聊不会被切换，仍使用 AstrBot 默认模型供应商。


## 🔑 使用方式

1. 将本目录作为插件目录放入 AstrBot 的 `data/plugins/astrbot_plugin_token_limit`。
2. 在 AstrBot WebUI 的插件管理中加载或重载插件。
3. 在原生 WebUI 插件配置页或 Plugin Page 的弹窗中填写群号、每日上限、刷新时间和超限策略。
4. 打开 Plugin Page 查看限流群当前窗口内的用量进度，也可以点击“历史 token 用量统计”查看趋势图，或点击“今日用户 token 用量统计”查看单群用户排行。
5. 在用量统计中点击群聊右侧齿轮，可设置该群每日上限，并在“本群 token 节约策略”中勾选“仅通过 @bot 触发 LLM 回复”。

## 📊 统计说明

- 当前用量和历史用量均来自 AstrBot 原生 `ProviderStat`。
- 今日用户用量统计按当前 `refresh_time` 切分的统计周期展示，并在后台持久化保存近 48 小时的用户小时桶、请求归因数据和对话明细；超过 48 小时的数据会被清理，JSON 使用缩进格式便于管理员直接查看。
- 对话明细只保存每次有效请求的时间、用户输入前 20 个字和当次 token 用量，不保存 AstrBot 附加的系统提示词。
- 用户 token 用量只在单个群聊内统计，同一 QQ 用户在不同群里的用量不会合并。
- 对于 AstrBot `ProviderStat.umo` 无法直接解析出用户 QQ 号的群聊记录，插件会使用 LLM 请求事件中记录的用户号、请求时间和会话 ID 进行轻量级归因；无法获取昵称时显示 QQ 号。
- `user_daily_token_limit >= 0` 时启用单用户限流；用户达到上限后，仅该用户在该群里的 LLM 请求会被静默阻断，非 LLM 请求不受影响。Plugin Page 的今日用户柱状图会将超限用户标红。
