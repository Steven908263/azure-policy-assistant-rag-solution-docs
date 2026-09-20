import pytest

from conftest import build_candidate


pytestmark = pytest.mark.integration


def test_real_cosmos_duplicate_prevention_through_persistence_gate(step45_case):
    app = step45_case["app"]
    user_id = step45_case["user_a"]
    source_id = step45_case["source_id"]

    candidate = build_candidate(
        memory_key="step45_duplicate",
        content=f"Step 45 duplicate prevention {source_id}",
    )

    first = app.persist_memory_candidate(
        user_id=user_id,
        candidate=candidate,
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    second = app.persist_memory_candidate(
        user_id=user_id,
        candidate=dict(candidate),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert first is not None
    assert second is None

    matching = [
        item
        for item in app.get_active_user_memories(user_id)
        if item.get("sourceConversationId") == source_id
        and item.get("type") == candidate["type"]
        and app.normalize_memory_content(item.get("content", ""))
        == app.normalize_memory_content(candidate["content"])
    ]

    assert len(matching) == 1


def test_real_cosmos_supersession_deactivates_old_value(step45_case):
    app = step45_case["app"]
    user_id = step45_case["user_a"]
    source_id = step45_case["source_id"]

    memory_key = "step45_supersession"

    old_memory = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key=memory_key,
            content=f"Step 45 supersession OLD {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert old_memory is not None

    new_memory = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key=memory_key,
            content=f"Step 45 supersession NEW {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert new_memory is not None

    old_after = app.get_authorized_memory(
        memory_id=old_memory["memoryId"],
        user_id=user_id,
    )
    new_after = app.get_authorized_memory(
        memory_id=new_memory["memoryId"],
        user_id=user_id,
    )

    assert old_after is not None
    assert old_after["active"] is False
    assert old_after["deleted"] is False
    assert old_after["supersededByMemoryId"] == new_memory["memoryId"]

    assert new_after is not None
    assert new_after["active"] is True
    assert old_memory["memoryId"] in new_after["supersedesMemoryIds"]

    active_same_key = [
        item
        for item in app.get_active_user_memories(user_id)
        if item.get("memoryKey") == memory_key
    ]

    assert [item["memoryId"] for item in active_same_key] == [
        new_memory["memoryId"]
    ]
