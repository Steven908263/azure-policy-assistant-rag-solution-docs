\
def test_duplicate_detection_normalizes_case_and_whitespace(
    app_module,
    monkeypatch,
):
    existing = {
        "id": "memory-1",
        "memoryId": "memory-1",
        "userId": "user-a",
        "type": "project_context",
        "content": "User is building the Corporate Policy Assistant.",
        "active": True,
        "deleted": False,
    }

    monkeypatch.setattr(
        app_module,
        "get_active_user_memories",
        lambda user_id: [existing],
    )

    duplicate = app_module.find_duplicate_active_memory(
        user_id="user-a",
        memory_type="PROJECT_CONTEXT",
        content="  user   is building the corporate policy assistant.  ",
    )

    assert duplicate == existing


def test_same_content_for_different_memory_type_is_not_duplicate(
    app_module,
    monkeypatch,
):
    existing = {
        "id": "memory-1",
        "memoryId": "memory-1",
        "userId": "user-a",
        "type": "preference",
        "content": "Use Azure.",
        "active": True,
        "deleted": False,
    }

    monkeypatch.setattr(
        app_module,
        "get_active_user_memories",
        lambda user_id: [existing],
    )

    duplicate = app_module.find_duplicate_active_memory(
        user_id="user-a",
        memory_type="project_context",
        content="Use Azure.",
    )

    assert duplicate is None


def test_persistence_gate_skips_duplicate_without_creating_record(
    app_module,
    monkeypatch,
    valid_memory_candidate,
):
    existing = {
        "id": "memory-1",
        "memoryId": "memory-1",
        "userId": "user-a",
        "type": "project_context",
        "content": valid_memory_candidate["content"],
        "active": True,
        "deleted": False,
    }

    monkeypatch.setattr(app_module, "LONG_TERM_MEMORY_ENABLED", True)
    monkeypatch.setattr(
        app_module,
        "find_duplicate_active_memory",
        lambda **kwargs: existing,
    )

    def fail_if_created(**kwargs):
        raise AssertionError(
            "create_long_term_memory must not run for an exact duplicate"
        )

    monkeypatch.setattr(
        app_module,
        "create_long_term_memory",
        fail_if_created,
    )

    result = app_module.persist_memory_candidate(
        user_id="user-a",
        candidate=dict(valid_memory_candidate),
    )

    assert result is None
