\
def test_persisted_memory_schema_contains_required_i28_fields(app_module):
    expected = {
        "id",
        "memoryId",
        "userId",
        "type",
        "memoryKey",
        "content",
        "supersedesMemoryIds",
        "supersededByMemoryId",
        "sourceConversationId",
        "sourceMessageIds",
        "createdAt",
        "updatedAt",
        "confidence",
        "importance",
        "expiresAt",
        "active",
        "deleted",
    }

    assert expected.issubset(set(app_module.LONG_TERM_MEMORY_SCHEMA))


def test_extraction_schema_uses_configured_step39_limits(app_module):
    item_schema = (
        app_module.MEMORY_EXTRACTION_RESPONSE_SCHEMA["properties"]
        ["memories"]["items"]
    )

    assert (
        item_schema["properties"]["content"]["maxLength"]
        == app_module.LONG_TERM_MEMORY_MAX_ITEM_CHARS
    )
    assert (
        item_schema["properties"]["confidence"]["minimum"]
        == app_module.LONG_TERM_MEMORY_MIN_CONFIDENCE
    )
    assert (
        item_schema["properties"]["importance"]["minimum"]
        == app_module.LONG_TERM_MEMORY_MIN_IMPORTANCE
    )
    assert item_schema["additionalProperties"] is False


def test_valid_candidate_is_normalized_and_accepted(
    app_module,
    valid_memory_candidate,
):
    candidate = dict(valid_memory_candidate)
    candidate["memoryKey"] = "  Current_AI_Project  "
    candidate["content"] = "  User is building the Corporate Policy Assistant.  "

    is_valid, reason, validated = app_module.validate_memory_candidate(candidate)

    assert is_valid is True
    assert reason == "eligible"
    assert validated is not None
    assert validated["memoryKey"] == "current_ai_project"
    assert validated["content"] == "User is building the Corporate Policy Assistant."
