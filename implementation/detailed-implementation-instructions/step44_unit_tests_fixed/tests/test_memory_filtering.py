\
from conftest import FakeMemoriesContainer


def test_default_memory_query_filters_inactive_and_deleted(
    app_module,
    monkeypatch,
):
    fake = FakeMemoriesContainer(query_results=[])
    monkeypatch.setattr(app_module, "memories_container", fake)

    app_module.get_user_memories("user-a")

    query = fake.query_calls[0]["query"]

    assert "m.userId = @userId" in query
    assert "m.active = true" in query
    assert "m.deleted = false" in query


def test_include_inactive_removes_active_filter_only(
    app_module,
    monkeypatch,
):
    fake = FakeMemoriesContainer(query_results=[])
    monkeypatch.setattr(app_module, "memories_container", fake)

    app_module.get_user_memories(
        "user-a",
        include_inactive=True,
        include_deleted=False,
    )

    query = fake.query_calls[0]["query"]

    assert "m.userId = @userId" in query
    assert "m.active = true" not in query
    assert "m.deleted = false" in query


def test_include_deleted_removes_deleted_filter_only(
    app_module,
    monkeypatch,
):
    fake = FakeMemoriesContainer(query_results=[])
    monkeypatch.setattr(app_module, "memories_container", fake)

    app_module.get_user_memories(
        "user-a",
        include_inactive=False,
        include_deleted=True,
    )

    query = fake.query_calls[0]["query"]

    assert "m.userId = @userId" in query
    assert "m.active = true" in query
    assert "m.deleted = false" not in query


def test_get_active_user_memories_requests_active_non_deleted_only(
    app_module,
    monkeypatch,
):
    captured = {}

    def fake_get_user_memories(
        user_id,
        include_inactive=False,
        include_deleted=False,
    ):
        captured.update(
            {
                "user_id": user_id,
                "include_inactive": include_inactive,
                "include_deleted": include_deleted,
            }
        )
        return [{"id": "active-memory"}]

    monkeypatch.setattr(app_module, "LONG_TERM_MEMORY_ENABLED", True)
    monkeypatch.setattr(
        app_module,
        "get_user_memories",
        fake_get_user_memories,
    )

    result = app_module.get_active_user_memories("user-a")

    assert result == [{"id": "active-memory"}]
    assert captured == {
        "user_id": "user-a",
        "include_inactive": False,
        "include_deleted": False,
    }


def test_feature_flag_disabled_returns_no_active_memories(
    app_module,
    monkeypatch,
):
    monkeypatch.setattr(app_module, "LONG_TERM_MEMORY_ENABLED", False)

    result = app_module.get_active_user_memories("user-a")

    assert result == []
