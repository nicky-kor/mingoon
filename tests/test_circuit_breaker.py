from research_os.models import circuit_breaker


def test_is_unrecoverable_failure_matches_known_billing_errors():
    assert circuit_breaker.is_unrecoverable_failure("Your credit balance is too low to access the Claude API")
    assert circuit_breaker.is_unrecoverable_failure("Error code: 429 - insufficient_quota")
    assert circuit_breaker.is_unrecoverable_failure("You exceeded your current quota")
    assert circuit_breaker.is_unrecoverable_failure("invalid_api_key: Incorrect API key provided")
    assert circuit_breaker.is_unrecoverable_failure("authentication_error")


def test_is_unrecoverable_failure_does_not_match_transient_errors():
    # Timeouts, connection resets, and plain rate limits should NOT trip
    # the breaker — a retry (or the next call) often just works.
    assert not circuit_breaker.is_unrecoverable_failure("Connection timed out")
    assert not circuit_breaker.is_unrecoverable_failure("Connection reset by peer")
    assert not circuit_breaker.is_unrecoverable_failure("rate limited, please retry")
    assert not circuit_breaker.is_unrecoverable_failure("")
    assert not circuit_breaker.is_unrecoverable_failure(None)


def test_trip_then_is_tripped_returns_active_row(isolated_db):
    with isolated_db.session_scope() as session:
        assert circuit_breaker.is_tripped(session, "anthropic") is None
        circuit_breaker.trip(session, "anthropic", reason="credit balance is too low", cooldown_seconds=3600)

    with isolated_db.session_scope() as session:
        row = circuit_breaker.is_tripped(session, "anthropic")
        assert row is not None
        assert row.provider == "anthropic"
        assert row.reason == "credit balance is too low"


def test_is_tripped_returns_none_after_cooldown_expires(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.trip(session, "anthropic", reason="invalid_api_key", cooldown_seconds=-1)

    with isolated_db.session_scope() as session:
        assert circuit_breaker.is_tripped(session, "anthropic") is None


def test_clear_removes_the_breaker(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.trip(session, "anthropic", reason="insufficient_quota")

    with isolated_db.session_scope() as session:
        circuit_breaker.clear(session, "anthropic")

    with isolated_db.session_scope() as session:
        assert circuit_breaker.is_tripped(session, "anthropic") is None


def test_clear_on_untripped_provider_is_a_noop(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.clear(session, "anthropic")  # should not raise


def test_list_active_only_includes_currently_tripped_providers(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.trip(session, "anthropic", reason="credit balance is too low", cooldown_seconds=3600)
        circuit_breaker.trip(session, "openai", reason="invalid_api_key", cooldown_seconds=-1)

    with isolated_db.session_scope() as session:
        active = circuit_breaker.list_active(session)
        assert [row.provider for row in active] == ["anthropic"]


def test_trip_overwrites_an_existing_breaker_for_the_same_provider(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.trip(session, "anthropic", reason="first failure", cooldown_seconds=3600)
        circuit_breaker.trip(session, "anthropic", reason="second failure", cooldown_seconds=3600)

    with isolated_db.session_scope() as session:
        active = circuit_breaker.list_active(session)
        assert len(active) == 1
        assert active[0].reason == "second failure"
