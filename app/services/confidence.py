from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def calculate_vote_score(votes_worked: int, votes_failed: int) -> float:
    return (votes_worked + 1) / (votes_worked + votes_failed + 2)


def calculate_freshness(
    updated_at: datetime,
    expires_at: datetime | None = None,
) -> float:
    now = _now()
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            return 0.0
    days_since = (now - updated_at).total_seconds() / 86400
    return max(0.0, 1.0 - (days_since / 14.0))


def calculate_confidence(
    votes_worked: int,
    votes_failed: int,
    updated_at: datetime,
    source_reliability: float = 0.5,
    expires_at: datetime | None = None,
) -> float:
    vote_score = calculate_vote_score(votes_worked, votes_failed)
    freshness = calculate_freshness(updated_at, expires_at)
    return (vote_score * 0.4) + (freshness * 0.3) + (source_reliability * 0.3)


def recalculate_confidence(code, source_reliability: float = 0.5) -> float:
    return calculate_confidence(
        votes_worked=code.votes_worked,
        votes_failed=code.votes_failed,
        updated_at=code.updated_at,
        source_reliability=source_reliability,
        expires_at=code.expires_at,
    )
