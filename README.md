</div>

<div align="center">

# astrbot_plugin_token_limit

*_✨ [**AstrBot**](*https://github.com/AstrBotDevs/AstrBot*) 群聊 LLM token 用量限流插件 ✨_*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
![AstrBot >=4.24.2](https://img.shields.io/badge/AstrBot-4.24.2%2B-green.svg)
![Plugin Page](https://img.shields.io/badge/适配-最新_Plugin_Page-orange.svg)
[![GitHub](https://img.shields.io/badge/作者-青尘工作室-cyan)](https://space.bilibili.com/385556208/)

</div>

用于 AstrBot 的 QQ 群聊 LLM token 用量限流插件。

当某个已配置群聊达到单群每日 token 上限后，可以**停止**该群后续 LLM 调用，也可以**切换到一个回退模型**继续回复，并在回退额度耗尽后停止调用。

## 功能

- 按 QQ 群号设置限流列表。
- 按 `用量刷新时间` 切分每日统计窗口，到下一个刷新时间自动重新统计。
- 支持超限策略：
  - `停止调用 LLM`：群聊原始模型用量达到每日上限后，直接拦截后续 LLM 请求。
  - `回退到其他模型`：群聊原始模型用量达到每日上限后，改用配置的回退模型供应商；回退模型消耗达到“回退模型的用量上限”后，再停止该群所有 LLM 调用。
- 提供 Plugin Page 可视化页面，可查看每个群聊 token 用量进度和限流状态。

## 配置项

| 配置项 | 说明 |
| --- | --- |
| `enabled` | 是否启用插件。关闭后不拦截 LLM 请求。 |
| `limited_groups` | 需要限流的 QQ 群号列表。 |
| `daily_token_limit` | 单个群聊每日原始模型 token 上限，单位为 token。 |
| `over_limit_policy.action` | 用量超限后的措施，可选 `stop_llm` 或 `fallback_provider`。 |
| `over_limit_policy.fallback_provider_id` | 回退模型供应商 ID。Plugin Page 会使用当前已加载供应商渲染下拉选择；原生 WebUI 中填写供应商 ID。 |
| `over_limit_policy.fallback_token_limit` | 回退模型额外 token 上限，单位为 token。 |
| `refresh_time` | 用量刷新时间，格式 `HH:MM`，按 AstrBot 所在机器本地时区计算。 |
| `qq_platform_names` | 需要识别为 QQ 平台的适配器名称，默认 `aiocqhttp`、`qq_official`、`qq_official_webhook`。 |
| `match_unique_session` | 是否兼容 AstrBot `unique_session` 会话隔离下的历史统计。 |
| `block_message` | 达到停止调用条件后发送到群里的提示文本。 |
| `send_block_message` | 是否发送超限提示；关闭后只静默拦截 LLM 请求。 |

`block_message` 支持变量：`{group_id}`、`{used}`、`{limit}`、`{refresh_time}`、`{window_start}`、`{window_end}`。

## 超限策略示例

假设：

- `daily_token_limit = 10000000`
- `over_limit_policy.action = fallback_provider`
- `over_limit_policy.fallback_token_limit = 5000000`

某群当日原始模型用量达到 10M token 后，后续 LLM 请求会切换到配置的回退供应商。该群通过回退供应商继续消耗 5M token 后，当日总用量达到 15M，插件会停止该群继续调用任何 LLM 模型。

其他未超限群聊不会被切换，仍使用 AstrBot 默认模型供应商。

## 使用方式

1. 将本目录作为插件目录放入 AstrBot 的 `data/plugins/astrbot_plugin_token_limit`。
2. 在 AstrBot WebUI 的插件管理中加载或重载插件。
3. 在原生 WebUI 插件配置页或 Plugin Page 的弹窗中填写群号、每日上限、刷新时间和超限策略。
4. 打开 Plugin Page 查看限流群当前窗口内的用量进度。

