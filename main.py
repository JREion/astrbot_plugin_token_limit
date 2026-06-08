from __future__ import annotations

import json
import re
import asyncio
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any

from quart import request
from sqlmodel import col, func, select

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
try:
    from astrbot.api.star import Context, Star, StarTools
except ImportError:  # pragma: no cover - kept for older AstrBot builds.
    from astrbot.api.star import Context, Star

    StarTools = None  # type: ignore[assignment]
from astrbot.core.db.po import ProviderStat
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.platform.message_type import MessageType

try:
    from .backend.history_stats import HistoryStatsMixin
except ImportError:  # pragma: no cover - compatible with direct module loading.
    from backend.history_stats import HistoryStatsMixin


PLUGIN_NAME = "astrbot_plugin_token_limit"
GROUP_REMARKS_FILE = "group_remarks.json"
GROUP_LIMITS_FILE = "group_limits.json"
MAX_GROUP_REMARK_LENGTH = 64
OVER_LIMIT_STOP = "stop_llm"
OVER_LIMIT_FALLBACK = "fallback_provider"
TOKEN_FIELDS_SUM = (
    ProviderStat.token_input_other
    + ProviderStat.token_input_cached
    + ProviderStat.token_output
)


CONFIG_SCHEMA: dict[str, dict[str, Any]] = {
    "enabled": {
        "description": "启用插件",
        "type": "bool",
        "hint": "关闭后不统计限流状态，也不会拦截任何 LLM 请求。",
        "default": True,
    },
    "limited_groups": {
        "description": "需要限流的 QQ 群聊列表",
        "type": "list",
        "hint": "填写 QQ 群号。原生 WebUI 可逐项填写；也兼容逗号、空格或换行分隔的字符串。新加入的群号会从加入时刻开始写入历史 token 用量统计；之后即使从列表移除也会继续统计。",
        "default": [],
    },
    "daily_token_limit": {
        "description": "单个群聊每日用量上限",
        "type": "int",
        "hint": "单位为 token。当前统计窗口内群聊总用量到达上限后，根据“用量超限时的措施”停止调用 LLM 或切换到回退模型。",
        "default": 1000000,
    },
    "over_limit_policy": {
        "description": "用量超限时的措施",
        "type": "object",
        "hint": "配置群聊达到每日用量上限后的处理方式。",
        "default": {
            "action": OVER_LIMIT_STOP,
            "fallback_provider_id": "",
            "fallback_token_limit": 0,
        },
        "items": {
            "action": {
                "description": "处理方式",
                "type": "string",
                "hint": "选择“停止调用 LLM”时，原始模型用量超限后直接拦截；选择“回退到其他模型”时，会改用回退供应商继续生成回复。",
                "default": OVER_LIMIT_STOP,
                "options": [OVER_LIMIT_STOP, OVER_LIMIT_FALLBACK],
                "option_labels": ["停止调用 LLM", "回退到其他模型"],
            },
            "fallback_provider_id": {
                "description": "回退的模型供应商",
                "type": "string",
                "hint": "填写 AstrBot 模型供应商 ID。Plugin Page 会提供当前已加载的聊天模型供应商下拉选择。",
                "default": "",
            },
            "fallback_token_limit": {
                "description": "回退模型的用量上限",
                "type": "int",
                "hint": "单位为 token。选择回退时，硬上限为“每日用量上限 + 回退模型的用量上限”；当前统计窗口内群聊总用量到达硬上限后停止调用。",
                "default": 0,
            },
        },
    },
    "refresh_time": {
        "description": "用量刷新时间",
        "type": "string",
        "hint": "每天按本机时区在该时间切换统计窗口，格式 HH:MM，例如 00:00 或 04:30。",
        "default": "00:00",
    },
    "qq_platform_names": {
        "description": "QQ 平台适配器名称",
        "type": "list",
        "hint": "只有这些平台类型的群聊会被限流。默认覆盖 aiocqhttp、qq_official 和 qq_official_webhook。",
        "default": ["aiocqhttp", "qq_official", "qq_official_webhook"],
    },
    "match_unique_session": {
        "description": "兼容会话隔离统计",
        "type": "bool",
        "hint": "开启后统计当前窗口和历史用量时，会匹配常见 unique_session 形式，例如 用户ID_群号。",
        "default": True,
    },
    "block_message": {
        "description": "超限拦截提示",
        "type": "text",
        "hint": "达到停止调用条件时发送到群聊。可用变量：{group_id}、{used}、{limit}、{refresh_time}、{window_start}、{window_end}。",
        "default": "本群今日 LLM token 用量已达上限（{used}/{limit}），将在 {refresh_time} 后恢复。",
    },
    "send_block_message": {
        "description": "发送拦截提示",
        "type": "bool",
        "hint": "关闭后只拦截 LLM 请求，不向群内发送提示消息。",
        "default": True,
    },
}


@dataclass(frozen=True)
class UsageWindow:
    start_local: datetime
    end_local: datetime
    start_utc: datetime
    end_utc: datetime


def _ok(data: dict | list | None = None, message: str | None = None) -> dict:
    return {"status": "ok", "message": message, "data": data or {}}


def _error(message: str) -> dict:
    return {"status": "error", "message": message, "data": {}}


def _split_group_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [str(int(value))]
    if isinstance(value, str):
        return [item for item in re.split(r"[\s,;，；]+", value.strip()) if item]
    if isinstance(value, list):
        groups: list[str] = []
        for item in value:
            groups.extend(_split_group_values(item))
        return groups
    return []


def _normalize_group_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def _format_tokens(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    if value >= 1_000:
        return f"{value / 1_000:.2f} K"
    return str(value)


def _parse_refresh_time(value: Any) -> time:
    raw = str(value or "00:00").strip()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", raw)
    if not match:
        return time(hour=0, minute=0)
    return time(hour=int(match.group(1)), minute=int(match.group(2)))


def _local_timezone() -> tzinfo:
    tz = datetime.now().astimezone().tzinfo
    return tz or timezone.utc


def _build_usage_window(refresh_time: Any) -> UsageWindow:
    local_tz = _local_timezone()
    now_local = datetime.now(local_tz)
    parsed_time = _parse_refresh_time(refresh_time)
    today_refresh = datetime.combine(now_local.date(), parsed_time, tzinfo=local_tz)
    if now_local >= today_refresh:
        start_local = today_refresh
    else:
        start_local = today_refresh - timedelta(days=1)
    end_local = start_local + timedelta(days=1)
    return UsageWindow(
        start_local=start_local,
        end_local=end_local,
        start_utc=start_local.astimezone(timezone.utc),
        end_utc=end_local.astimezone(timezone.utc),
    )


class Main(HistoryStatsMixin, Star):
    def __init__(self, context: Context, config: dict | None = None) -> None:
        super().__init__(context)
        self.context = context
        self.config = config if config is not None else {}
        self.group_remarks_path = self._resolve_group_remarks_path()
        self.group_limits_path = self._resolve_group_limits_path()
        self.history_stats_path = self._resolve_history_stats_path()
        self._history_last_sync_attempt: datetime | None = None
        self._history_sync_lock = asyncio.Lock()
        self._ensure_history_tracking_for_current_groups()
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/config",
            self.api_get_config,
            ["GET"],
            "获取 QQ 群 token 限流插件配置",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/config",
            self.api_save_config,
            ["POST"],
            "保存 QQ 群 token 限流插件配置",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/usage",
            self.api_get_usage,
            ["GET"],
            "获取 QQ 群 token 用量统计",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/history",
            self.api_get_history,
            ["GET"],
            "获取 QQ 群 token 历史用量统计",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/providers",
            self.api_get_providers,
            ["GET"],
            "获取可用于回退的 LLM 模型供应商列表",
        )

        self.context.register_web_api(
            f"/{PLUGIN_NAME}/remarks",
            self.api_get_remarks,
            ["GET"],
            "Get QQ group remarks",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/remarks",
            self.api_save_remark,
            ["POST"],
            "Save QQ group remark",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/group-settings",
            self.api_get_group_settings,
            ["GET"],
            "Get QQ group personalized settings",
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/group-settings",
            self.api_save_group_settings,
            ["POST"],
            "Save QQ group personalized settings",
        )

    async def initialize(self) -> None:
        self._start_history_background_sync()

    async def terminate(self) -> None:
        await self._stop_history_background_sync()

    def _resolve_group_remarks_path(self) -> Path:
        if StarTools is not None:
            try:
                return StarTools.get_data_dir(PLUGIN_NAME) / GROUP_REMARKS_FILE
            except Exception as exc:
                logger.warning("Failed to get plugin data dir; using plugin dir: %s", exc)
        return Path(__file__).resolve().with_name(GROUP_REMARKS_FILE)

    def _resolve_group_limits_path(self) -> Path:
        remarks_path = getattr(self, "group_remarks_path", None)
        if isinstance(remarks_path, Path):
            return remarks_path.with_name(GROUP_LIMITS_FILE)
        return Path(__file__).resolve().with_name(GROUP_LIMITS_FILE)

    def _load_group_remarks(self) -> dict[str, str]:
        if not self.group_remarks_path.exists():
            return {}
        try:
            raw_data = json.loads(self.group_remarks_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read QQ group remarks: %s", exc)
            return {}
        if not isinstance(raw_data, dict):
            return {}

        remarks: dict[str, str] = {}
        for group_id, remark in raw_data.items():
            normalized_group_id = _normalize_group_id(group_id)
            normalized_remark = self._sanitize_group_remark(remark)
            if normalized_group_id and normalized_remark:
                remarks[normalized_group_id] = normalized_remark
        return remarks

    def _save_group_remarks(self, remarks: dict[str, str]) -> None:
        try:
            self.group_remarks_path.parent.mkdir(parents=True, exist_ok=True)
            self.group_remarks_path.write_text(
                json.dumps(remarks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            raise ValueError(f"保存 QQ 群备注失败: {exc}") from exc

    @staticmethod
    def _sanitize_group_remark(value: Any) -> str:
        return str(value or "").strip()[:MAX_GROUP_REMARK_LENGTH]

    def _load_group_limits(self) -> dict[str, int]:
        if not self.group_limits_path.exists():
            return {}
        try:
            raw_data = json.loads(self.group_limits_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read QQ group personalized limits: %s", exc)
            return {}
        if not isinstance(raw_data, dict):
            return {}

        limits: dict[str, int] = {}
        for group_id, value in raw_data.items():
            normalized_group_id = _normalize_group_id(group_id)
            if not normalized_group_id:
                continue
            try:
                limits[normalized_group_id] = max(0, int(value or 0))
            except (TypeError, ValueError):
                continue
        return limits

    def _save_group_limits(self, limits: dict[str, int]) -> None:
        normalized_limits = {
            _normalize_group_id(group_id): max(0, int(limit or 0))
            for group_id, limit in limits.items()
            if _normalize_group_id(group_id)
        }
        try:
            self.group_limits_path.parent.mkdir(parents=True, exist_ok=True)
            self.group_limits_path.write_text(
                json.dumps(normalized_limits, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            raise ValueError(f"保存 QQ 群个性化配置失败: {exc}") from exc

    def _config_value(self, key: str) -> Any:
        if key in self.config:
            return self.config[key]
        return CONFIG_SCHEMA[key].get("default")

    def _limited_groups(self) -> list[str]:
        seen: set[str] = set()
        groups: list[str] = []
        for item in _split_group_values(self._config_value("limited_groups")):
            group_id = _normalize_group_id(item)
            if group_id and group_id not in seen:
                seen.add(group_id)
                groups.append(group_id)
        return groups

    def _qq_platform_names(self) -> set[str]:
        values = _split_group_values(self._config_value("qq_platform_names"))
        return {item.strip() for item in values if item.strip()}

    def _qq_platform_ids(self) -> set[str]:
        configured_names = self._qq_platform_names()
        platform_ids: set[str] = set()
        platform_manager = getattr(self.context, "platform_manager", None)
        platform_insts = getattr(platform_manager, "platform_insts", []) or []
        for platform in platform_insts:
            meta = platform.meta()
            meta_name = getattr(meta, "name", "")
            meta_id = getattr(meta, "id", "")
            if not configured_names or meta_name in configured_names:
                if meta_id:
                    platform_ids.add(str(meta_id))
                if meta_name:
                    platform_ids.add(str(meta_name))
        if not platform_ids:
            platform_ids.update(configured_names)
        return platform_ids

    def _daily_limit(self) -> int:
        try:
            return max(0, int(self._config_value("daily_token_limit") or 0))
        except (TypeError, ValueError):
            return 0

    def _daily_limit_for_group(
        self,
        group_id: str,
        group_limits: dict[str, int] | None = None,
    ) -> int:
        normalized_group_id = _normalize_group_id(group_id)
        limits = group_limits if group_limits is not None else self._load_group_limits()
        if normalized_group_id in limits:
            return max(0, int(limits[normalized_group_id] or 0))
        return self._daily_limit()

    def _over_limit_policy(self) -> dict[str, Any]:
        raw_policy = self._config_value("over_limit_policy")
        default_policy = CONFIG_SCHEMA["over_limit_policy"]["default"]
        policy = dict(default_policy)
        if isinstance(raw_policy, dict):
            policy.update(raw_policy)

        action = str(policy.get("action") or OVER_LIMIT_STOP).strip()
        if action not in {OVER_LIMIT_STOP, OVER_LIMIT_FALLBACK}:
            action = OVER_LIMIT_STOP

        try:
            fallback_token_limit = max(
                0,
                int(policy.get("fallback_token_limit") or 0),
            )
        except (TypeError, ValueError):
            fallback_token_limit = 0

        return {
            "action": action,
            "fallback_provider_id": str(policy.get("fallback_provider_id") or "").strip(),
            "fallback_token_limit": fallback_token_limit,
        }

    def _fallback_provider_id(self) -> str:
        policy = self._over_limit_policy()
        if policy["action"] != OVER_LIMIT_FALLBACK:
            return ""
        return str(policy["fallback_provider_id"] or "").strip()

    def _fallback_token_limit(self) -> int:
        return int(self._over_limit_policy()["fallback_token_limit"])

    def _fallback_provider_exists(self, provider_id: str) -> bool:
        if not provider_id:
            return False
        get_provider_by_id = getattr(self.context, "get_provider_by_id", None)
        if not callable(get_provider_by_id):
            return False
        provider = get_provider_by_id(provider_id)
        return provider is not None and hasattr(provider, "text_chat")

    def _is_enabled(self) -> bool:
        return bool(self._config_value("enabled"))

    def _is_qq_group_event(self, event: AstrMessageEvent) -> bool:
        if event.get_message_type() != MessageType.GROUP_MESSAGE:
            return False
        platform_names = self._qq_platform_names()
        return not platform_names or event.get_platform_name() in platform_names

    def _umo_candidates_for_group(self, group_id: str) -> list[str]:
        candidates = []
        for platform_id in self._qq_platform_ids():
            candidates.append(f"{platform_id}:{MessageType.GROUP_MESSAGE.value}:{group_id}")
        return candidates

    def _unique_session_like_patterns(self, group_id: str) -> list[str]:
        escaped_group_id = _escape_like(group_id)
        return [
            f"{_escape_like(platform_id)}:{MessageType.GROUP_MESSAGE.value}:%{escaped_group_id}%"
            for platform_id in self._qq_platform_ids()
        ]

    async def _query_usage_for_group(
        self,
        group_id: str,
        window: UsageWindow,
        provider_id: str | None = None,
        exclude_provider_id: str | None = None,
    ) -> tuple[int, dict[str, int]]:
        db = self.context.get_db()
        umo_candidates = self._umo_candidates_for_group(group_id)
        filters = [
            ProviderStat.agent_type == "internal",
            ProviderStat.created_at >= window.start_utc,
            ProviderStat.created_at < window.end_utc,
        ]
        if provider_id:
            filters.append(ProviderStat.provider_id == provider_id)
        if exclude_provider_id:
            filters.append(ProviderStat.provider_id != exclude_provider_id)

        if bool(self._config_value("match_unique_session")):
            umo_filter = ProviderStat.umo.in_(umo_candidates)
            for pattern in self._unique_session_like_patterns(group_id):
                umo_filter = umo_filter | ProviderStat.umo.like(
                    pattern,
                    escape="\\",
                )
            filters.append(umo_filter)
        else:
            filters.append(ProviderStat.umo.in_(umo_candidates))

        async with db.get_db() as session:
            hourly: dict[str, int] = {}
            total = 0
            database_url = str(getattr(db, "DATABASE_URL", "") or "").lower()
            if "sqlite" in database_url:
                bucket_expr = func.strftime(
                    "%Y-%m-%dT%H:00:00+00:00",
                    ProviderStat.created_at,
                )
                rows_result = await session.execute(
                    select(
                        bucket_expr.label("bucket"),
                        func.coalesce(func.sum(TOKEN_FIELDS_SUM), 0).label("tokens"),
                    )
                    .where(*filters)
                    .group_by(bucket_expr)
                    .order_by(bucket_expr.asc())
                )
                for bucket, tokens in rows_result.all():
                    if not bucket:
                        continue
                    bucket_utc = datetime.fromisoformat(str(bucket))
                    if bucket_utc.tzinfo is None:
                        bucket_utc = bucket_utc.replace(tzinfo=timezone.utc)
                    else:
                        bucket_utc = bucket_utc.astimezone(timezone.utc)
                    bucket_local = bucket_utc.astimezone(window.start_local.tzinfo)
                    normalized_tokens = int(tokens or 0)
                    hourly[bucket_local.isoformat()] = normalized_tokens
                    total += normalized_tokens
            else:
                total_result = await session.execute(
                    select(func.coalesce(func.sum(TOKEN_FIELDS_SUM), 0)).where(*filters)
                )
                total = int(total_result.scalar_one() or 0)

                rows_result = await session.execute(
                    select(ProviderStat.created_at, TOKEN_FIELDS_SUM.label("tokens"))
                    .where(*filters)
                    .order_by(col(ProviderStat.created_at).asc())
                )
                for created_at, tokens in rows_result.all():
                    created_at_utc = (
                        created_at.replace(tzinfo=timezone.utc)
                        if created_at.tzinfo is None
                        else created_at.astimezone(timezone.utc)
                    )
                    bucket = created_at_utc.astimezone(window.start_local.tzinfo).replace(
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                    key = bucket.isoformat()
                    hourly[key] = hourly.get(key, 0) + int(tokens or 0)
        return total, hourly

    async def _query_split_usage_for_group(
        self,
        group_id: str,
        window: UsageWindow,
        fallback_provider_id: str,
    ) -> tuple[int, int, dict[str, int]]:
        if not fallback_provider_id:
            primary_used, hourly = await self._query_usage_for_group(group_id, window)
            return primary_used, 0, hourly

        primary_used, hourly = await self._query_usage_for_group(
            group_id,
            window,
            exclude_provider_id=fallback_provider_id,
        )
        fallback_used, _ = await self._query_usage_for_group(
            group_id,
            window,
            provider_id=fallback_provider_id,
        )
        return primary_used, fallback_used, hourly

    @staticmethod
    def _build_limit_state(
        limit: int,
        policy: dict[str, Any],
        primary_used: int,
        fallback_used: int,
        fallback_configured: bool,
    ) -> dict[str, Any]:
        used = primary_used + fallback_used
        action = str(policy.get("action") or OVER_LIMIT_STOP)
        fallback_token_limit = max(0, int(policy.get("fallback_token_limit") or 0))
        hard_limit = limit
        effective_limit = limit
        using_fallback = False
        stopped = False
        status = "normal"

        if limit > 0:
            if action == OVER_LIMIT_FALLBACK and fallback_configured:
                hard_limit = limit + fallback_token_limit
                if used >= limit:
                    effective_limit = hard_limit
                    if used >= hard_limit:
                        stopped = True
                        status = "stopped"
                    else:
                        using_fallback = True
                        status = "fallback"
            elif used >= limit:
                stopped = True
                status = "stopped"

        percent = (
            0
            if effective_limit <= 0
            else min(100, round((used / effective_limit) * 100, 2))
        )
        return {
            "used": used,
            "hard_limit": hard_limit,
            "effective_limit": effective_limit,
            "percent": percent,
            "using_fallback": using_fallback,
            "stopped": stopped,
            "status": status,
        }

    async def _build_event_limit_context(
        self,
        event: AstrMessageEvent,
    ) -> dict[str, Any] | None:
        if not self._is_enabled():
            return None
        if not self._is_qq_group_event(event):
            return None

        group_id = _normalize_group_id(event.get_group_id())
        if not group_id or group_id not in self._limited_groups():
            return None

        limit = self._daily_limit_for_group(group_id)
        if limit <= 0:
            return None

        window = _build_usage_window(self._config_value("refresh_time"))
        policy = self._over_limit_policy()
        fallback_provider_id = (
            str(policy["fallback_provider_id"])
            if policy["action"] == OVER_LIMIT_FALLBACK
            else ""
        )
        fallback_token_limit = int(policy["fallback_token_limit"])
        fallback_configured = bool(
            policy["action"] == OVER_LIMIT_FALLBACK and fallback_token_limit > 0
        )
        fallback_provider_valid = bool(
            fallback_provider_id and self._fallback_provider_exists(fallback_provider_id)
        )
        primary_used, fallback_used, _ = await self._query_split_usage_for_group(
            group_id,
            window,
            fallback_provider_id,
        )
        limit_state = self._build_limit_state(
            limit,
            policy,
            primary_used,
            fallback_used,
            fallback_configured,
        )
        return {
            "group_id": group_id,
            "limit": limit,
            "window": window,
            "policy": policy,
            "fallback_provider_id": fallback_provider_id,
            "fallback_token_limit": fallback_token_limit,
            "fallback_configured": fallback_configured,
            "fallback_provider_valid": fallback_provider_valid,
            "primary_used": primary_used,
            "fallback_used": fallback_used,
            "limit_state": limit_state,
        }

    async def _build_usage_payload(self) -> dict[str, Any]:
        groups = self._limited_groups()
        global_limit = self._daily_limit()
        group_limits = self._load_group_limits()
        policy = self._over_limit_policy()
        fallback_provider_id = (
            str(policy["fallback_provider_id"])
            if policy["action"] == OVER_LIMIT_FALLBACK
            else ""
        )
        fallback_token_limit = int(policy["fallback_token_limit"])
        fallback_configured = bool(
            policy["action"] == OVER_LIMIT_FALLBACK and fallback_token_limit > 0
        )
        fallback_enabled = bool(
            fallback_provider_id and self._fallback_provider_exists(fallback_provider_id)
        )
        window = _build_usage_window(self._config_value("refresh_time"))
        remarks = self._load_group_remarks()
        items = []
        for group_id in groups:
            limit = self._daily_limit_for_group(group_id, group_limits)
            has_custom_limit = group_id in group_limits
            primary_used, fallback_used, hourly = await self._query_split_usage_for_group(
                group_id,
                window,
                fallback_provider_id,
            )
            limit_state = self._build_limit_state(
                limit,
                policy,
                primary_used,
                fallback_used,
                fallback_configured,
            )
            used = int(limit_state["used"])
            effective_limit = int(limit_state["effective_limit"])
            hard_limit = int(limit_state["hard_limit"])
            items.append(
                {
                    "group_id": group_id,
                    "remark": remarks.get(group_id, ""),
                    "used_tokens": used,
                    "primary_used_tokens": primary_used,
                    "fallback_used_tokens": fallback_used,
                    "limit_tokens": effective_limit,
                    "hard_limit_tokens": hard_limit,
                    "primary_limit_tokens": limit,
                    "global_limit_tokens": global_limit,
                    "custom_limit_tokens": group_limits.get(group_id),
                    "has_custom_limit": has_custom_limit,
                    "fallback_limit_tokens": fallback_token_limit,
                    "used_display": _format_tokens(used),
                    "limit_display": _format_tokens(effective_limit),
                    "hard_limit_display": _format_tokens(hard_limit),
                    "primary_limit_display": _format_tokens(limit),
                    "global_limit_display": _format_tokens(global_limit),
                    "custom_limit_display": (
                        _format_tokens(group_limits[group_id]) if has_custom_limit else ""
                    ),
                    "fallback_limit_display": _format_tokens(fallback_token_limit),
                    "percent": limit_state["percent"],
                    "limited": bool(limit_state["stopped"]),
                    "using_fallback": bool(
                        limit_state["using_fallback"] and fallback_enabled
                    ),
                    "fallback_unavailable": bool(
                        limit_state["using_fallback"] and not fallback_enabled
                    ),
                    "stopped": bool(limit_state["stopped"]),
                    "status": limit_state["status"],
                    "fallback_provider_id": fallback_provider_id,
                    "hourly": hourly,
                }
            )

        return {
            "enabled": self._is_enabled(),
            "groups": items,
            "remarks": remarks,
            "group_limits": group_limits,
            "global_daily_token_limit": global_limit,
            "global_daily_token_limit_display": _format_tokens(global_limit),
            "over_limit_policy": {
                **policy,
                "fallback_configured": fallback_configured,
                "fallback_enabled": fallback_enabled,
            },
            "window": {
                "start": window.start_local.isoformat(),
                "end": window.end_local.isoformat(),
                "refresh_time": str(self._config_value("refresh_time") or "00:00"),
            },
        }

    def _serialize_config(self) -> dict[str, Any]:
        return {key: self._config_value(key) for key in CONFIG_SCHEMA}

    def _provider_options(self) -> list[dict[str, str]]:
        providers = []
        seen_provider_ids: set[str] = set()
        get_all_providers = getattr(self.context, "get_all_providers", None)
        provider_insts = get_all_providers() if callable(get_all_providers) else []
        for provider in provider_insts or []:
            if not hasattr(provider, "text_chat"):
                continue
            try:
                meta = provider.meta()
            except Exception:
                continue
            provider_id = str(getattr(meta, "id", "") or "").strip()
            if not provider_id or provider_id in seen_provider_ids:
                continue
            seen_provider_ids.add(provider_id)
            get_model = getattr(provider, "get_model", None)
            model = str(
                getattr(meta, "model", "")
                or (get_model() if callable(get_model) else "")
                or ""
            ).strip()
            provider_type = str(getattr(meta, "type", "") or "").strip()
            label_parts = [provider_id]
            detail = " / ".join(item for item in (provider_type, model) if item)
            if detail:
                label_parts.append(detail)
            providers.append(
                {
                    "id": provider_id,
                    "label": " - ".join(label_parts),
                    "type": provider_type,
                    "model": model,
                }
            )
        return providers

    def _config_schema_for_page(self) -> dict[str, dict[str, Any]]:
        schema = json.loads(json.dumps(CONFIG_SCHEMA, ensure_ascii=False))
        provider_options = self._provider_options()
        fallback_meta = schema["over_limit_policy"]["items"]["fallback_provider_id"]
        fallback_meta["options"] = [item["id"] for item in provider_options]
        fallback_meta["option_labels"] = [item["label"] for item in provider_options]
        return schema

    def _sanitize_config(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        next_config = self._serialize_config()
        if "enabled" in raw_config:
            next_config["enabled"] = bool(raw_config["enabled"])
        if "limited_groups" in raw_config:
            next_config["limited_groups"] = self._normalize_config_list(
                raw_config["limited_groups"]
            )
        if "daily_token_limit" in raw_config:
            try:
                next_config["daily_token_limit"] = max(
                    0, int(raw_config["daily_token_limit"])
                )
            except (TypeError, ValueError):
                raise ValueError("单个群聊每日用量上限必须是整数。") from None
        if "over_limit_policy" in raw_config:
            next_config["over_limit_policy"] = self._sanitize_over_limit_policy(
                raw_config["over_limit_policy"]
            )
        if "refresh_time" in raw_config:
            raw_time = str(raw_config["refresh_time"] or "").strip()
            if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", raw_time):
                raise ValueError("用量刷新时间格式必须是 HH:MM。")
            parsed = _parse_refresh_time(raw_time)
            next_config["refresh_time"] = f"{parsed.hour:02d}:{parsed.minute:02d}"
        if "qq_platform_names" in raw_config:
            next_config["qq_platform_names"] = self._normalize_config_list(
                raw_config["qq_platform_names"]
            )
        if "match_unique_session" in raw_config:
            next_config["match_unique_session"] = bool(
                raw_config["match_unique_session"]
            )
        if "block_message" in raw_config:
            next_config["block_message"] = str(raw_config["block_message"] or "")
        if "send_block_message" in raw_config:
            next_config["send_block_message"] = bool(raw_config["send_block_message"])
        return next_config

    def _sanitize_over_limit_policy(self, raw_policy: Any) -> dict[str, Any]:
        if not isinstance(raw_policy, dict):
            raw_policy = {}

        action = str(raw_policy.get("action") or OVER_LIMIT_STOP).strip()
        if action not in {OVER_LIMIT_STOP, OVER_LIMIT_FALLBACK}:
            raise ValueError("用量超限时的措施必须是“停止调用 LLM”或“回退到其他模型”。")

        fallback_provider_id = str(raw_policy.get("fallback_provider_id") or "").strip()
        try:
            fallback_token_limit = max(
                0,
                int(raw_policy.get("fallback_token_limit") or 0),
            )
        except (TypeError, ValueError):
            raise ValueError("回退模型的用量上限必须是整数。") from None

        if action == OVER_LIMIT_FALLBACK:
            if not fallback_provider_id:
                raise ValueError("选择“回退到其他模型”时必须配置回退的模型供应商。")
            if not self._fallback_provider_exists(fallback_provider_id):
                raise ValueError(f"未找到回退模型供应商：{fallback_provider_id}")

        return {
            "action": action,
            "fallback_provider_id": fallback_provider_id,
            "fallback_token_limit": fallback_token_limit,
        }

    @staticmethod
    def _normalize_config_list(value: Any) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in _split_group_values(value):
            text = _normalize_group_id(item)
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result

    async def api_get_config(self) -> dict:
        return _ok(
            {
                "config": self._serialize_config(),
                "schema": self._config_schema_for_page(),
            }
        )

    async def api_save_config(self) -> dict:
        payload = await request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _error("请求体必须是 JSON 对象。")
        raw_config = payload.get("config", payload)
        if not isinstance(raw_config, dict):
            return _error("config 必须是 JSON 对象。")
        try:
            next_config = self._sanitize_config(raw_config)
        except ValueError as exc:
            return _error(str(exc))
        self.config.clear()
        self.config.update(next_config)
        save_config = getattr(self.config, "save_config", None)
        if callable(save_config):
            save_config()
        await self._maybe_sync_history_stats(force=True)
        return _ok(
            {
                "config": self._serialize_config(),
                "schema": self._config_schema_for_page(),
            }
        )

    async def api_get_usage(self) -> dict:
        try:
            await self._maybe_sync_history_stats()
            return _ok(await self._build_usage_payload())
        except Exception as exc:
            logger.error("获取 QQ 群 token 用量失败: %s", exc, exc_info=True)
            return _error(f"获取用量失败: {exc}")

    async def api_get_providers(self) -> dict:
        return _ok({"providers": self._provider_options()})

    async def api_get_remarks(self) -> dict:
        return _ok({"remarks": self._load_group_remarks()})

    async def api_save_remark(self) -> dict:
        payload = await request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _error("Request body must be a JSON object.")

        group_id = _normalize_group_id(payload.get("group_id"))
        if not group_id:
            return _error("group_id is required.")

        remarks = self._load_group_remarks()
        remark = self._sanitize_group_remark(payload.get("remark"))
        if remark:
            remarks[group_id] = remark
        else:
            remarks.pop(group_id, None)

        try:
            self._save_group_remarks(remarks)
        except ValueError as exc:
            return _error(str(exc))

        return _ok({"group_id": group_id, "remark": remark, "remarks": remarks})

    async def api_get_group_settings(self) -> dict:
        group_id = _normalize_group_id(request.args.get("group_id"))
        if not group_id:
            return _error("group_id is required.")

        global_limit = self._daily_limit()
        group_limits = self._load_group_limits()
        has_custom_limit = group_id in group_limits
        effective_limit = self._daily_limit_for_group(group_id, group_limits)
        return _ok(
            {
                "group_id": group_id,
                "daily_token_limit": effective_limit,
                "daily_token_limit_display": _format_tokens(effective_limit),
                "global_daily_token_limit": global_limit,
                "global_daily_token_limit_display": _format_tokens(global_limit),
                "has_custom_limit": has_custom_limit,
                "custom_daily_token_limit": (
                    group_limits[group_id] if has_custom_limit else None
                ),
                "custom_daily_token_limit_display": (
                    _format_tokens(group_limits[group_id]) if has_custom_limit else ""
                ),
            }
        )

    async def api_save_group_settings(self) -> dict:
        payload = await request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _error("Request body must be a JSON object.")

        group_id = _normalize_group_id(payload.get("group_id"))
        if not group_id:
            return _error("group_id is required.")

        try:
            daily_token_limit = max(0, int(payload.get("daily_token_limit") or 0))
        except (TypeError, ValueError):
            return _error("单个群聊每日用量上限必须是整数。")

        group_limits = self._load_group_limits()
        group_limits[group_id] = daily_token_limit
        try:
            self._save_group_limits(group_limits)
        except ValueError as exc:
            return _error(str(exc))

        global_limit = self._daily_limit()
        return _ok(
            {
                "group_id": group_id,
                "daily_token_limit": daily_token_limit,
                "daily_token_limit_display": _format_tokens(daily_token_limit),
                "global_daily_token_limit": global_limit,
                "global_daily_token_limit_display": _format_tokens(global_limit),
                "has_custom_limit": True,
                "group_limits": group_limits,
            }
        )

    @filter.on_waiting_llm_request(priority=1000)
    async def on_waiting_llm_request(self, event: AstrMessageEvent) -> None:
        await self._maybe_sync_history_stats()
        limit_context = await self._build_event_limit_context(event)
        if not limit_context:
            return

        limit_state = limit_context["limit_state"]
        if limit_state["status"] != "fallback":
            return

        fallback_provider_id = str(limit_context["fallback_provider_id"] or "")
        if not limit_context["fallback_provider_valid"]:
            logger.warning(
                "群 %s 当前窗口 token=%s 已进入回退区间，但回退模型供应商 %s 不可用；本次将交由 AstrBot 使用当前可用供应商。",
                limit_context["group_id"],
                limit_state["used"],
                fallback_provider_id or "<empty>",
            )
            return

        event.set_extra("selected_provider", fallback_provider_id)
        event.set_extra("token_limit_selected_provider", fallback_provider_id)
        logger.info(
            "群 %s 当前窗口 token=%s 已达每日上限 %s，未达硬上限 %s，本次预先切换到回退模型供应商 %s。",
            limit_context["group_id"],
            limit_state["used"],
            limit_context["limit"],
            limit_state["hard_limit"],
            fallback_provider_id,
        )

    @filter.on_llm_request(priority=1000)
    async def on_llm_request(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        limit_context = await self._build_event_limit_context(event)
        if not limit_context:
            return

        group_id = limit_context["group_id"]
        limit = int(limit_context["limit"])
        window = limit_context["window"]
        limit_state = limit_context["limit_state"]
        used = int(limit_state["used"])
        stop_limit = int(limit_state["hard_limit"])

        if limit_state["status"] == "normal":
            return

        if limit_state["status"] == "fallback":
            fallback_provider_id = str(limit_context["fallback_provider_id"] or "")
            if limit_context["fallback_provider_valid"]:
                event.set_extra("selected_provider", fallback_provider_id)

            selected_provider = event.get_extra("token_limit_selected_provider")
            if selected_provider:
                logger.debug(
                    "群 %s 已预先切换到回退模型供应商 %s。",
                    group_id,
                    selected_provider,
                )
            elif limit_context["fallback_provider_valid"]:
                logger.warning(
                    "群 %s 已进入回退区间，但 provider 已在 LLM 请求钩子前完成选择；请确认 on_waiting_llm_request 钩子已启用。",
                    group_id,
                )
            else:
                logger.warning(
                    "群 %s 已进入回退区间，但回退模型供应商 %s 不可用；本次交由 AstrBot 当前可用供应商处理。",
                    group_id,
                    limit_context["fallback_provider_id"] or "<empty>",
                )
            return

        if bool(self._config_value("send_block_message")):
            message_template = str(self._config_value("block_message") or "")
            message = message_template.format(
                group_id=group_id,
                used=_format_tokens(used),
                limit=_format_tokens(stop_limit),
                refresh_time=self._config_value("refresh_time"),
                window_start=window.start_local.strftime("%Y-%m-%d %H:%M"),
                window_end=window.end_local.strftime("%Y-%m-%d %H:%M"),
            )
            if message:
                await event.send(MessageChain().message(message))

        event.stop_event()
        logger.info(
            "已拦截群 %s 的 LLM 请求：当前窗口 token=%s，上限=%s",
            group_id,
            used,
            stop_limit,
        )
