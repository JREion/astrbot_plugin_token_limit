from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any

from quart import request
from sqlmodel import col, func, select

from astrbot.api import logger
from astrbot.core.db.po import ProviderStat


USER_USAGE_STATS_FILE = "user_usage_48h.json"
USER_USAGE_STATS_VERSION = 1
USER_USAGE_ATTRIBUTION_VERSION = 2
USER_USAGE_RETENTION = timedelta(hours=48)
USER_USAGE_SYNC_OVERLAP = timedelta(hours=2)
USER_USAGE_SYNC_MIN_INTERVAL = timedelta(minutes=2)
USER_USAGE_BACKGROUND_SYNC_INTERVAL = 3600
USER_USAGE_DEFAULT_TOP_LIMIT = 10
USER_USAGE_REQUEST_RETENTION = timedelta(hours=48)
USER_USAGE_REQUEST_LOOKBACK = timedelta(minutes=10)
USER_USAGE_REQUEST_FUTURE_TOLERANCE = timedelta(seconds=5)
USER_TOKEN_FIELDS_SUM = (
    ProviderStat.token_input_other
    + ProviderStat.token_input_cached
    + ProviderStat.token_output
)


@dataclass(frozen=True)
class UserUsageWindow:
    start_local: datetime
    end_local: datetime
    start_utc: datetime
    end_utc: datetime


def _user_usage_ok(data: dict | list | None = None, message: str | None = None) -> dict:
    return {"status": "ok", "message": message, "data": data or {}}


def _user_usage_error(message: str) -> dict:
    return {"status": "error", "message": message, "data": {}}


def _normalize_user_group_id(value: Any) -> str:
    text = str(value or "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _sanitize_user_id(value: Any) -> str:
    text = str(value or "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text[:64]


def _sanitize_user_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())[:64]


def _format_user_tokens(value: int) -> str:
    normalized = max(0, int(value or 0))
    if normalized >= 1_000_000:
        return f"{normalized / 1_000_000:.2f} M"
    if normalized >= 1_000:
        return f"{normalized / 1_000:.2f} K"
    return str(normalized)


def _local_timezone() -> tzinfo:
    tz = datetime.now().astimezone().tzinfo
    return tz or timezone.utc


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _to_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _timestamp_to_utc(value: Any) -> datetime | None:
    try:
        timestamp = float(value or 0)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc)


def _hour_start(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _parse_refresh_time(value: Any) -> time:
    raw = str(value or "00:00").strip()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", raw)
    if not match:
        return time(hour=0, minute=0)
    return time(hour=int(match.group(1)), minute=int(match.group(2)))


def _build_user_usage_window(refresh_time: Any) -> UserUsageWindow:
    local_tz = _local_timezone()
    now_local = datetime.now(local_tz)
    parsed_time = _parse_refresh_time(refresh_time)
    today_refresh = datetime.combine(now_local.date(), parsed_time, tzinfo=local_tz)
    if now_local >= today_refresh:
        start_local = today_refresh
    else:
        start_local = today_refresh - timedelta(days=1)
    end_local = start_local + timedelta(days=1)
    return UserUsageWindow(
        start_local=start_local,
        end_local=end_local,
        start_utc=start_local.astimezone(timezone.utc),
        end_utc=end_local.astimezone(timezone.utc),
    )


def _extract_user_id_from_umo(umo: Any, group_id: str) -> str:
    text = str(umo or "").strip()
    normalized_group_id = _normalize_user_group_id(group_id)
    if not text or not normalized_group_id:
        return ""

    parts = text.split(":")
    session = ":".join(parts[2:]) if len(parts) >= 3 else text
    if session == normalized_group_id:
        return ""

    chunks = [chunk for chunk in re.split(r"[^0-9A-Za-z]+", session) if chunk]
    for index, chunk in enumerate(chunks):
        if chunk != normalized_group_id:
            continue
        if index > 0 and chunks[index - 1].isdigit():
            return _sanitize_user_id(chunks[index - 1])
        if index + 1 < len(chunks) and chunks[index + 1].isdigit():
            return _sanitize_user_id(chunks[index + 1])

    if session.endswith(normalized_group_id):
        prefix = session[: -len(normalized_group_id)].strip("_:- ")
        digits = re.findall(r"\d+", prefix)
        if digits:
            return _sanitize_user_id(digits[-1])
    if session.startswith(normalized_group_id):
        suffix = session[len(normalized_group_id) :].strip("_:- ")
        digits = re.findall(r"\d+", suffix)
        if digits:
            return _sanitize_user_id(digits[0])

    for digit in re.findall(r"\d+", session):
        if digit != normalized_group_id:
            return _sanitize_user_id(digit)
    return ""


class UserStatsMixin:
    """Persistent near-48-hour per-user token usage stats."""

    def _resolve_user_stats_path(self) -> Path:
        remarks_path = getattr(self, "group_remarks_path", None)
        if isinstance(remarks_path, Path):
            return remarks_path.with_name(USER_USAGE_STATS_FILE)
        return Path(__file__).resolve().parents[1] / USER_USAGE_STATS_FILE

    def _empty_user_stats(self) -> dict[str, Any]:
        return {
            "version": USER_USAGE_STATS_VERSION,
            "attribution_version": USER_USAGE_ATTRIBUTION_VERSION,
            "groups": {},
        }

    def _load_user_stats(self) -> dict[str, Any]:
        path = getattr(self, "user_stats_path", None)
        if not isinstance(path, Path) or not path.exists():
            return self._empty_user_stats()
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read user token stats: %s", exc)
            return self._empty_user_stats()
        return self._sanitize_user_stats(raw_data)

    def _save_user_stats(self, data: dict[str, Any]) -> None:
        path = getattr(self, "user_stats_path", None)
        if not isinstance(path, Path):
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to save user token stats: %s", exc)

    def _sanitize_user_stats(self, raw_data: Any) -> dict[str, Any]:
        if not isinstance(raw_data, dict):
            return self._empty_user_stats()
        raw_groups = raw_data.get("groups")
        if not isinstance(raw_groups, dict):
            raw_groups = {}

        cutoff = _hour_start(_now_utc() - USER_USAGE_RETENTION)
        groups: dict[str, dict[str, Any]] = {}
        for raw_group_id, raw_group in raw_groups.items():
            group_id = _normalize_user_group_id(raw_group_id)
            if not group_id or not isinstance(raw_group, dict):
                continue

            raw_users = raw_group.get("users")
            if not isinstance(raw_users, dict):
                raw_users = {}

            users: dict[str, dict[str, Any]] = {}
            for raw_user_id, raw_user in raw_users.items():
                user_id = _sanitize_user_id(raw_user_id)
                if not user_id or not isinstance(raw_user, dict):
                    continue
                raw_hours = raw_user.get("hours")
                hours: dict[str, int] = {}
                if isinstance(raw_hours, dict):
                    for raw_bucket, raw_tokens in raw_hours.items():
                        bucket = _parse_datetime(raw_bucket)
                        if bucket is None:
                            continue
                        normalized_bucket = _hour_start(bucket)
                        if normalized_bucket < cutoff:
                            continue
                        try:
                            tokens = max(0, int(raw_tokens or 0))
                        except (TypeError, ValueError):
                            continue
                        if tokens > 0:
                            hours[_iso_utc(normalized_bucket)] = tokens

                nickname = _sanitize_user_name(raw_user.get("nickname"))
                if hours or nickname:
                    users[user_id] = {
                        "nickname": nickname,
                        "total_tokens": sum(hours.values()),
                        "hours": hours,
                    }

            raw_requests = raw_group.get("requests")
            requests: list[dict[str, Any]] = []
            if isinstance(raw_requests, list):
                request_cutoff = _now_utc() - USER_USAGE_REQUEST_RETENTION
                for raw_request in raw_requests:
                    if not isinstance(raw_request, dict):
                        continue
                    started_at = _parse_datetime(raw_request.get("started_at"))
                    if started_at is None or started_at < request_cutoff:
                        continue
                    user_id = _sanitize_user_id(raw_request.get("user_id"))
                    if not user_id:
                        continue
                    request_umo = str(raw_request.get("umo") or "").strip()[:256]
                    if not request_umo:
                        continue
                    requests.append(
                        {
                            "started_at": _iso_utc(started_at),
                            "umo": request_umo,
                            "user_id": user_id,
                            "nickname": _sanitize_user_name(
                                raw_request.get("nickname")
                            ),
                            "conversation_id": str(
                                raw_request.get("conversation_id") or ""
                            ).strip()[:128],
                            "assigned_stat_ids": [
                                int(stat_id)
                                for stat_id in raw_request.get(
                                    "assigned_stat_ids",
                                    [],
                                )
                                if str(stat_id).isdigit()
                            ][:64],
                        }
                    )

            last_synced_at = _parse_datetime(raw_group.get("last_synced_at"))
            groups[group_id] = {
                "last_synced_at": _iso_utc(last_synced_at) if last_synced_at else "",
                "users": users,
                "requests": requests,
            }
        attribution_version = raw_data.get("attribution_version")
        try:
            normalized_attribution_version = int(attribution_version or 0)
        except (TypeError, ValueError):
            normalized_attribution_version = 0
        return {
            "version": USER_USAGE_STATS_VERSION,
            "attribution_version": normalized_attribution_version,
            "groups": groups,
        }

    def _ensure_user_tracking_for_current_groups(
        self,
        data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        stats = data if data is not None else self._load_user_stats()
        groups = stats.setdefault("groups", {})
        changed = False
        limited_groups = self._limited_groups()
        self._user_group_signature = tuple(limited_groups)
        for group_id in limited_groups:
            if group_id in groups and isinstance(groups[group_id], dict):
                groups[group_id].setdefault("users", {})
                groups[group_id].setdefault("requests", [])
                continue
            groups[group_id] = {"last_synced_at": "", "users": {}, "requests": []}
            changed = True
        if data is None and changed:
            self._save_user_stats(stats)
        self._user_cached_stats = stats
        return stats, changed

    async def _user_background_sync_loop(self) -> None:
        while True:
            try:
                await self._maybe_sync_user_stats(force=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("User token usage background sync failed: %s", exc)
            await asyncio.sleep(USER_USAGE_BACKGROUND_SYNC_INTERVAL)

    def _start_user_background_sync(self) -> None:
        existing_task = getattr(self, "_user_background_task", None)
        if existing_task is not None and not existing_task.done():
            return
        try:
            self._user_background_task = asyncio.create_task(
                self._user_background_sync_loop(),
                name="token_limit_user_usage_sync",
            )
        except RuntimeError as exc:
            logger.debug("User token usage background sync is not started: %s", exc)

    async def _stop_user_background_sync(self) -> None:
        task = getattr(self, "_user_background_task", None)
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._user_background_task = None

    async def _maybe_sync_user_stats(
        self,
        force: bool = False,
        group_id: str | None = None,
    ) -> dict[str, Any]:
        sync_lock = getattr(self, "_user_sync_lock", None)
        if sync_lock is None:
            sync_lock = asyncio.Lock()
            self._user_sync_lock = sync_lock
        async with sync_lock:
            return await self._sync_user_stats_locked(force, group_id)

    async def _sync_user_stats_locked(
        self,
        force: bool,
        group_id: str | None,
    ) -> dict[str, Any]:
        now = _now_utc()
        normalized_group_id = _normalize_user_group_id(group_id) if group_id else ""
        current_signature = tuple(self._limited_groups())
        sync_key = normalized_group_id or "*"
        last_attempts = getattr(self, "_user_last_sync_attempts", None)
        if not isinstance(last_attempts, dict):
            last_attempts = {}
            self._user_last_sync_attempts = last_attempts
        last_attempt = last_attempts.get(sync_key)
        last_signature = getattr(self, "_user_group_signature", None)
        if (
            not force
            and isinstance(last_attempt, datetime)
            and now - last_attempt < USER_USAGE_SYNC_MIN_INTERVAL
            and current_signature == last_signature
        ):
            cached_stats = getattr(self, "_user_cached_stats", None)
            if isinstance(cached_stats, dict):
                return cached_stats

        stats, changed = self._ensure_user_tracking_for_current_groups()
        attribution_version_changed = (
            int(stats.get("attribution_version") or 0) < USER_USAGE_ATTRIBUTION_VERSION
        )
        limited_groups = set(self._limited_groups())
        target_groups = (
            [normalized_group_id]
            if normalized_group_id and normalized_group_id in limited_groups
            else list(limited_groups)
        )

        last_attempts[sync_key] = now
        synced = False
        for target_group_id in target_groups:
            group_data = stats.setdefault("groups", {}).setdefault(
                target_group_id,
                {"last_synced_at": "", "users": {}, "requests": []},
            )
            if not isinstance(group_data, dict):
                continue
            try:
                group_synced = await self._sync_user_group(
                    target_group_id,
                    group_data,
                    now,
                    rebuild=attribution_version_changed,
                )
                synced = synced or group_synced
            except Exception as exc:
                logger.warning(
                    "Failed to sync user token usage for group %s: %s",
                    target_group_id,
                    exc,
                    exc_info=True,
                )

        if attribution_version_changed:
            stats["attribution_version"] = USER_USAGE_ATTRIBUTION_VERSION
            changed = True

        if changed or synced:
            self._save_user_stats(stats)
        self._user_cached_stats = stats
        return stats

    async def _sync_user_group(
        self,
        group_id: str,
        group_data: dict[str, Any],
        now: datetime,
        rebuild: bool = False,
    ) -> bool:
        retention_start = now - USER_USAGE_RETENTION
        last_synced = _parse_datetime(group_data.get("last_synced_at")) or retention_start
        query_start = (
            retention_start
            if rebuild
            else max(retention_start, last_synced - USER_USAGE_SYNC_OVERLAP)
        )
        query_end = now
        if query_end <= query_start:
            self._prune_user_group_data(group_data, retention_start, query_end, query_end)
            return False

        hourly, unassigned_records = await self._query_hourly_user_usage_for_group(
            group_id,
            query_start,
            query_end,
        )
        assigned_hourly, request_changed = self._assign_user_usage_records(
            group_data,
            unassigned_records,
            now,
        )
        hourly = self._merge_user_hours(hourly, assigned_hourly)
        changed = self._prune_user_group_data(
            group_data,
            retention_start,
            query_start,
            query_end,
        )
        changed = self._prune_user_usage_requests(group_data, now) or changed
        changed = request_changed or changed

        users = group_data.setdefault("users", {})
        if not isinstance(users, dict):
            users = {}
            group_data["users"] = users

        for user_id, user_hours in hourly.items():
            if not user_hours:
                continue
            user_data = users.setdefault(user_id, {"nickname": "", "hours": {}})
            if not isinstance(user_data, dict):
                user_data = {"nickname": "", "hours": {}}
                users[user_id] = user_data
            hours = user_data.setdefault("hours", {})
            if not isinstance(hours, dict):
                hours = {}
                user_data["hours"] = hours
            for bucket_key, tokens in user_hours.items():
                normalized_tokens = max(0, int(tokens or 0))
                if normalized_tokens > 0:
                    hours[bucket_key] = normalized_tokens
                    changed = True

        for user_id in list(users.keys()):
            user_data = users[user_id]
            if not isinstance(user_data, dict):
                users.pop(user_id, None)
                changed = True
                continue
            hours = user_data.get("hours")
            if not isinstance(hours, dict):
                hours = {}
                user_data["hours"] = hours
            user_data["total_tokens"] = sum(max(0, int(value or 0)) for value in hours.values())
            if not hours and not _sanitize_user_name(user_data.get("nickname")):
                users.pop(user_id, None)
                changed = True

        next_synced_at = _iso_utc(query_end)
        if group_data.get("last_synced_at") != next_synced_at:
            group_data["last_synced_at"] = next_synced_at
            changed = True
        return changed

    @staticmethod
    def _merge_user_hours(
        base: dict[str, dict[str, int]],
        extra: dict[str, dict[str, int]],
    ) -> dict[str, dict[str, int]]:
        if not extra:
            return base
        for user_id, user_hours in extra.items():
            if not user_id or not user_hours:
                continue
            target = base.setdefault(user_id, {})
            for bucket_key, tokens in user_hours.items():
                target[bucket_key] = target.get(bucket_key, 0) + max(0, int(tokens or 0))
        return base

    def _assign_user_usage_records(
        self,
        group_data: dict[str, Any],
        records: list[dict[str, Any]],
        now: datetime,
    ) -> tuple[dict[str, dict[str, int]], bool]:
        requests = group_data.setdefault("requests", [])
        if not isinstance(requests, list):
            group_data["requests"] = []
            return {}, True

        candidates: list[dict[str, Any]] = []
        changed = False
        cutoff = now - USER_USAGE_REQUEST_RETENTION
        for request_item in requests:
            if not isinstance(request_item, dict):
                changed = True
                continue
            started_at = _parse_datetime(request_item.get("started_at"))
            if started_at is None or started_at < cutoff:
                changed = True
                continue
            user_id = _sanitize_user_id(request_item.get("user_id"))
            request_umo = str(request_item.get("umo") or "").strip()
            if not user_id or not request_umo:
                changed = True
                continue
            request_item["started_at"] = _iso_utc(started_at)
            request_item["user_id"] = user_id
            request_item["umo"] = request_umo[:256]
            request_item["nickname"] = _sanitize_user_name(request_item.get("nickname"))
            request_item["conversation_id"] = str(
                request_item.get("conversation_id") or ""
            ).strip()[:128]
            assigned_stat_ids = {
                int(stat_id)
                for stat_id in request_item.get("assigned_stat_ids", [])
                if str(stat_id).isdigit()
            }
            request_item["assigned_stat_ids"] = sorted(assigned_stat_ids)[-64:]
            request_item["_started_at_dt"] = started_at
            request_item["_assigned_set"] = assigned_stat_ids
            candidates.append(request_item)

        assigned_hourly: dict[str, dict[str, int]] = {}
        for record in records:
            stat_id = int(record.get("id") or 0)
            tokens = max(0, int(record.get("tokens") or 0))
            created_at = _to_utc_datetime(record.get("created_at"))
            started_at = _to_utc_datetime(record.get("started_at")) or created_at
            record_umo = str(record.get("umo") or "").strip()
            conversation_id = str(record.get("conversation_id") or "").strip()
            if (
                not stat_id
                or tokens <= 0
                or created_at is None
                or started_at is None
                or not record_umo
            ):
                continue

            matched = self._match_user_usage_request(
                candidates,
                stat_id,
                record_umo,
                started_at,
                conversation_id,
            )
            if not matched:
                continue

            user_id = _sanitize_user_id(matched.get("user_id"))
            if not user_id:
                continue
            bucket_key = _iso_utc(_hour_start(created_at))
            assigned_hourly.setdefault(user_id, {})[bucket_key] = (
                assigned_hourly.setdefault(user_id, {}).get(bucket_key, 0) + tokens
            )
            assigned_set = matched.setdefault("_assigned_set", set())
            assigned_set.add(stat_id)
            matched["assigned_stat_ids"] = sorted(assigned_set)[-64:]
            changed = True

        for request_item in candidates:
            request_item.pop("_started_at_dt", None)
            request_item.pop("_assigned_set", None)
        if len(candidates) != len(requests):
            changed = True
        group_data["requests"] = candidates
        return assigned_hourly, changed

    @staticmethod
    def _match_user_usage_request(
        requests: list[dict[str, Any]],
        stat_id: int,
        umo: str,
        created_at: datetime,
        conversation_id: str = "",
    ) -> dict[str, Any] | None:
        best_request = None
        best_started_at = None
        lower_bound = created_at - USER_USAGE_REQUEST_LOOKBACK
        upper_bound = created_at + USER_USAGE_REQUEST_FUTURE_TOLERANCE
        for request_item in requests:
            if request_item.get("umo") != umo:
                continue
            started_at = request_item.get("_started_at_dt")
            if not isinstance(started_at, datetime):
                continue
            if started_at < lower_bound or started_at > upper_bound:
                continue
            if (
                conversation_id
                and request_item.get("conversation_id")
                and request_item.get("conversation_id") != conversation_id
            ):
                continue
            if best_started_at is None or started_at > best_started_at:
                best_request = request_item
                best_started_at = started_at
        return best_request

    def _prune_user_usage_requests(
        self,
        group_data: dict[str, Any],
        now: datetime,
    ) -> bool:
        requests = group_data.setdefault("requests", [])
        if not isinstance(requests, list):
            group_data["requests"] = []
            return True

        cutoff = now - USER_USAGE_REQUEST_RETENTION
        next_requests = []
        changed = False
        for request_item in requests:
            if not isinstance(request_item, dict):
                changed = True
                continue
            started_at = _parse_datetime(request_item.get("started_at"))
            if started_at is None or started_at < cutoff:
                changed = True
                continue
            request_item["started_at"] = _iso_utc(started_at)
            next_requests.append(request_item)
        if len(next_requests) != len(requests):
            changed = True
        group_data["requests"] = next_requests
        return changed

    def _prune_user_group_data(
        self,
        group_data: dict[str, Any],
        retention_start: datetime,
        replace_start: datetime,
        replace_end: datetime,
    ) -> bool:
        changed = False
        users = group_data.setdefault("users", {})
        if not isinstance(users, dict):
            group_data["users"] = {}
            return True

        retention_bucket = _hour_start(retention_start)
        replace_bucket = _hour_start(replace_start)
        for user_id in list(users.keys()):
            user_data = users[user_id]
            if not isinstance(user_data, dict):
                users.pop(user_id, None)
                changed = True
                continue
            hours = user_data.setdefault("hours", {})
            if not isinstance(hours, dict):
                user_data["hours"] = {}
                changed = True
                continue
            for bucket_key in list(hours.keys()):
                bucket = _parse_datetime(bucket_key)
                if bucket is None or bucket < retention_bucket or (
                    replace_bucket <= bucket < replace_end
                ):
                    hours.pop(bucket_key, None)
                    changed = True
            if not hours and not _sanitize_user_name(user_data.get("nickname")):
                users.pop(user_id, None)
                changed = True
                continue
            user_data["total_tokens"] = sum(
                max(0, int(value or 0)) for value in hours.values()
            )
        return changed

    def _user_usage_umo_filter(self, group_id: str):
        umo_candidates = self._umo_candidates_for_group(group_id)
        umo_filter = ProviderStat.umo.in_(umo_candidates)
        for pattern in self._unique_session_like_patterns(group_id):
            umo_filter = umo_filter | ProviderStat.umo.like(pattern, escape="\\")
        return umo_filter

    async def _query_hourly_user_usage_for_group(
        self,
        group_id: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]]]:
        db = self.context.get_db()
        filters = [
            ProviderStat.agent_type == "internal",
            ProviderStat.created_at >= start_utc.astimezone(timezone.utc),
            ProviderStat.created_at < end_utc.astimezone(timezone.utc),
            self._user_usage_umo_filter(group_id),
        ]
        user_hours: dict[str, dict[str, int]] = {}
        unassigned_records: list[dict[str, Any]] = []
        async with db.get_db() as session:
            rows_result = await session.execute(
                select(
                    ProviderStat.id,
                    ProviderStat.created_at,
                    ProviderStat.umo,
                    ProviderStat.conversation_id,
                    ProviderStat.start_time,
                    USER_TOKEN_FIELDS_SUM.label("tokens"),
                )
                .where(*filters)
                .order_by(col(ProviderStat.created_at).asc())
            )
            for (
                stat_id,
                created_at,
                umo,
                conversation_id,
                start_time,
                tokens,
            ) in rows_result.all():
                normalized_tokens = max(0, int(tokens or 0))
                if normalized_tokens <= 0:
                    continue
                created_at_utc = _to_utc_datetime(created_at)
                if created_at_utc is None:
                    continue
                user_id = _extract_user_id_from_umo(umo, group_id)
                if user_id:
                    key = _iso_utc(_hour_start(created_at_utc))
                    user_hours.setdefault(user_id, {})[key] = (
                        user_hours.setdefault(user_id, {}).get(key, 0)
                        + normalized_tokens
                    )
                    continue
                unassigned_records.append(
                    {
                        "id": int(stat_id or 0),
                        "created_at": created_at_utc,
                        "started_at": _timestamp_to_utc(start_time),
                        "umo": str(umo or ""),
                        "conversation_id": str(conversation_id or ""),
                        "tokens": normalized_tokens,
                    }
                )
        return user_hours, unassigned_records

    async def _query_user_totals_for_group(
        self,
        group_id: str,
        window: UserUsageWindow,
    ) -> dict[str, int]:
        db = self.context.get_db()
        filters = [
            ProviderStat.agent_type == "internal",
            ProviderStat.created_at >= window.start_utc,
            ProviderStat.created_at < min(window.end_utc, _now_utc()),
            self._user_usage_umo_filter(group_id),
        ]
        totals: dict[str, int] = {}
        async with db.get_db() as session:
            rows_result = await session.execute(
                select(
                    ProviderStat.umo,
                    func.coalesce(func.sum(USER_TOKEN_FIELDS_SUM), 0).label("tokens"),
                )
                .where(*filters)
                .group_by(ProviderStat.umo)
            )
            for umo, tokens in rows_result.all():
                user_id = _extract_user_id_from_umo(umo, group_id)
                if not user_id:
                    continue
                totals[user_id] = totals.get(user_id, 0) + int(tokens or 0)
        return totals

    def _stored_user_totals_for_group(
        self,
        stats: dict[str, Any],
        group_id: str,
        window: UserUsageWindow,
    ) -> dict[str, int]:
        users = (
            stats.get("groups", {})
            .get(group_id, {})
            .get("users", {})
        )
        if not isinstance(users, dict):
            return {}

        totals: dict[str, int] = {}
        for user_id, user_data in users.items():
            sanitized_user_id = _sanitize_user_id(user_id)
            if not sanitized_user_id or not isinstance(user_data, dict):
                continue
            hours = user_data.get("hours")
            if not isinstance(hours, dict):
                continue
            total = 0
            for bucket_key, tokens in hours.items():
                bucket = _parse_datetime(bucket_key)
                if bucket is None:
                    continue
                if window.start_utc <= bucket < window.end_utc:
                    total += max(0, int(tokens or 0))
            if total > 0:
                totals[sanitized_user_id] = total
        return totals

    @staticmethod
    def _combine_user_totals(
        realtime_totals: dict[str, int],
        stored_totals: dict[str, int],
    ) -> dict[str, int]:
        totals = {
            _sanitize_user_id(user_id): max(0, int(tokens or 0))
            for user_id, tokens in realtime_totals.items()
            if _sanitize_user_id(user_id) and max(0, int(tokens or 0)) > 0
        }
        for user_id, tokens in stored_totals.items():
            sanitized_user_id = _sanitize_user_id(user_id)
            if not sanitized_user_id:
                continue
            totals[sanitized_user_id] = max(
                totals.get(sanitized_user_id, 0),
                max(0, int(tokens or 0)),
            )
        return totals

    def _remember_user_usage_event(
        self,
        event: Any,
        conversation_id: str | None = None,
    ) -> None:
        try:
            if not self._is_qq_group_event(event):
                return
            group_id = _normalize_user_group_id(event.get_group_id())
        except Exception:
            return
        if not group_id or group_id not in self._limited_groups():
            return

        user_id = self._event_user_id(event)
        if not user_id:
            return
        nickname = self._event_user_name(event)

        stats = self._load_user_stats()
        groups = stats.setdefault("groups", {})
        group_data = groups.setdefault(
            group_id,
            {"last_synced_at": "", "users": {}, "requests": []},
        )
        users = group_data.setdefault("users", {})
        user_data = users.setdefault(user_id, {"nickname": "", "hours": {}})
        changed = False
        if nickname and user_data.get("nickname") != nickname:
            user_data["nickname"] = nickname
            changed = True

        umo = str(getattr(event, "unified_msg_origin", "") or "").strip()
        if umo:
            requests = group_data.setdefault("requests", [])
            if not isinstance(requests, list):
                requests = []
                group_data["requests"] = requests
                changed = True
            started_at = datetime.fromtimestamp(
                float(getattr(event, "created_at", 0) or 0),
                timezone.utc,
            ) if getattr(event, "created_at", None) else _now_utc()
            request_item = {
                "started_at": _iso_utc(started_at),
                "umo": umo[:256],
                "user_id": user_id,
                "nickname": nickname,
                "conversation_id": str(conversation_id or "").strip()[:128],
                "assigned_stat_ids": [],
            }
            requests.append(request_item)
            changed = True
            self._prune_user_usage_requests(group_data, _now_utc())

        if not changed:
            return
        self._user_cached_stats = stats
        self._save_user_stats(stats)

    @staticmethod
    def _event_user_id(event: Any) -> str:
        for name in ("get_sender_id", "get_user_id"):
            getter = getattr(event, name, None)
            if not callable(getter):
                continue
            try:
                user_id = _sanitize_user_id(getter())
                if user_id:
                    return user_id
            except Exception:
                continue

        message_obj = getattr(event, "message_obj", None)
        sources = (
            (event, ("user_id", "sender_id", "qq")),
            (message_obj, ("user_id", "sender_id", "qq")),
            (getattr(message_obj, "sender", None), ("user_id", "sender_id", "id", "qq")),
            (getattr(event, "sender", None), ("user_id", "sender_id", "id", "qq")),
        )
        for source, names in sources:
            if source is None:
                continue
            for name in names:
                user_id = _sanitize_user_id(getattr(source, name, None))
                if user_id:
                    return user_id
        return ""

    @staticmethod
    def _event_user_name(event: Any) -> str:
        for name in ("get_sender_name", "get_user_name"):
            getter = getattr(event, name, None)
            if not callable(getter):
                continue
            try:
                nickname = _sanitize_user_name(getter())
                if nickname:
                    return nickname
            except Exception:
                continue

        for source in (
            event,
            getattr(event, "message_obj", None),
            getattr(getattr(event, "message_obj", None), "sender", None),
            getattr(event, "sender", None),
        ):
            if source is None:
                continue
            for name in ("card", "nickname", "nick", "name", "sender_name", "user_name"):
                nickname = _sanitize_user_name(getattr(source, name, None))
                if nickname:
                    return nickname
        return ""

    async def api_get_user_usage(self) -> dict:
        try:
            group_id = _normalize_user_group_id(request.args.get("group_id"))
            try:
                top_limit = max(
                    1,
                    min(30, int(request.args.get("limit") or USER_USAGE_DEFAULT_TOP_LIMIT)),
                )
            except (TypeError, ValueError):
                top_limit = USER_USAGE_DEFAULT_TOP_LIMIT

            usage_payload = await self._build_usage_payload()
            groups = self._user_usage_dropdown_groups(usage_payload)
            known_groups = {item["group_id"] for item in groups}
            selected_group_id = group_id if group_id in known_groups else ""
            stats = await self._maybe_sync_user_stats(
                force=bool(selected_group_id),
                group_id=selected_group_id or None,
            )
            users = []
            window = _build_user_usage_window(self._config_value("refresh_time"))
            if selected_group_id:
                realtime_totals = await self._query_user_totals_for_group(
                    selected_group_id,
                    window,
                )
                stored_totals = self._stored_user_totals_for_group(
                    stats,
                    selected_group_id,
                    window,
                )
                totals = self._combine_user_totals(realtime_totals, stored_totals)
                users = self._user_usage_rows(
                    stats,
                    selected_group_id,
                    totals,
                    top_limit,
                )

            return _user_usage_ok(
                {
                    "groups": groups,
                    "selected_group_id": selected_group_id,
                    "users": users,
                    "window": {
                        "start": window.start_local.isoformat(),
                        "end": window.end_local.isoformat(),
                        "refresh_time": str(self._config_value("refresh_time") or "00:00"),
                    },
                    "synced_at": _iso_utc(_now_utc()),
                    "top_limit": top_limit,
                }
            )
        except Exception as exc:
            logger.error("Failed to build user token usage response: %s", exc, exc_info=True)
            return _user_usage_error(f"获取今日用户用量失败: {exc}")

    def _user_usage_dropdown_groups(
        self,
        usage_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        groups = []
        for item in usage_payload.get("groups", []) or []:
            group_id = _normalize_user_group_id(item.get("group_id"))
            if not group_id:
                continue
            status = "normal"
            if item.get("stopped"):
                status = "stopped"
            elif item.get("using_fallback"):
                status = "fallback"
            groups.append(
                {
                    "group_id": group_id,
                    "remark": str(item.get("remark") or ""),
                    "daily_tokens": int(item.get("used_tokens") or 0),
                    "daily_display": str(item.get("used_display") or "0"),
                    "status": status,
                }
            )
        return groups

    def _user_usage_rows(
        self,
        stats: dict[str, Any],
        group_id: str,
        totals: dict[str, int],
        top_limit: int,
    ) -> list[dict[str, Any]]:
        users = (
            stats.get("groups", {})
            .get(group_id, {})
            .get("users", {})
        )
        if not isinstance(users, dict):
            users = {}
        rows = []
        for user_id, tokens in totals.items():
            normalized_tokens = max(0, int(tokens or 0))
            if normalized_tokens <= 0:
                continue
            user_data = users.get(user_id) if isinstance(users.get(user_id), dict) else {}
            nickname = _sanitize_user_name(user_data.get("nickname"))
            rows.append(
                {
                    "user_id": user_id,
                    "nickname": nickname,
                    "label": nickname or user_id,
                    "tokens": normalized_tokens,
                    "display": _format_user_tokens(normalized_tokens),
                }
            )
        rows.sort(key=lambda item: item["tokens"], reverse=True)
        return rows[:top_limit]
