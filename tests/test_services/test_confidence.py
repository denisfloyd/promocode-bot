from datetime import datetime, timedelta, timezone

import pytest

from app.services.confidence import (
    calculate_confidence,
    calculate_freshness,
    calculate_vote_score,
)


def _now():
    return datetime.now(timezone.utc)


class TestVoteScore:
    def test_no_votes_returns_0_5(self):
        assert calculate_vote_score(0, 0) == pytest.approx(0.5)

    def test_all_positive_votes(self):
        assert calculate_vote_score(10, 0) == pytest.approx(11 / 12)

    def test_all_negative_votes(self):
        assert calculate_vote_score(0, 10) == pytest.approx(1 / 12)

    def test_equal_votes(self):
        assert calculate_vote_score(5, 5) == pytest.approx(0.5)

    def test_bayesian_smoothing(self):
        # (3+1)/(3+2+2) = 4/7
        assert calculate_vote_score(3, 2) == pytest.approx(4 / 7)


class TestFreshness:
    def test_just_scraped(self):
        now = _now()
        assert calculate_freshness(now) == pytest.approx(1.0, abs=0.01)

    def test_7_days_old(self):
        seven_days_ago = _now() - timedelta(days=7)
        assert calculate_freshness(seven_days_ago) == pytest.approx(0.5, abs=0.01)

    def test_14_days_old(self):
        fourteen_days_ago = _now() - timedelta(days=14)
        assert calculate_freshness(fourteen_days_ago) == pytest.approx(0.0, abs=0.01)

    def test_older_than_14_days(self):
        old = _now() - timedelta(days=30)
        assert calculate_freshness(old) == pytest.approx(0.0)

    def test_expired_code(self):
        yesterday = _now() - timedelta(days=1)
        last_seen = _now()
        assert calculate_freshness(last_seen, expires_at=yesterday) == pytest.approx(0.0)

    def test_not_yet_expired(self):
        tomorrow = _now() + timedelta(days=1)
        last_seen = _now()
        result = calculate_freshness(last_seen, expires_at=tomorrow)
        assert result == pytest.approx(1.0, abs=0.01)


class TestConfidence:
    def test_new_code_default(self):
        # vote_score=0.5, freshness=1.0, source_reliability=0.5
        # 0.5*0.4 + 1.0*0.3 + 0.5*0.3 = 0.2 + 0.3 + 0.15 = 0.65
        score = calculate_confidence(
            votes_worked=0, votes_failed=0,
            updated_at=_now(), source_reliability=0.5,
        )
        assert score == pytest.approx(0.65, abs=0.01)

    def test_high_confidence_code(self):
        score = calculate_confidence(
            votes_worked=20, votes_failed=2,
            updated_at=_now(), source_reliability=0.9,
        )
        assert score > 0.8

    def test_low_confidence_old_code(self):
        score = calculate_confidence(
            votes_worked=1, votes_failed=10,
            updated_at=_now() - timedelta(days=14),
            source_reliability=0.3,
        )
        assert score < 0.2
