import pytest

from conftest import build_candidate


pytestmark = pytest.mark.integration


def test_real_cosmos_active_deleted_filtering(step45_case):
    app = step45_case["app"]
    user_id = step45_case["user_a"]
    source_id = step45_case["source_id"]

    active = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key="step45_filter_active",
            content=f"Step 45 active record {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    inactive = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key="step45_filter_inactive",
            content=f"Step 45 inactive record {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    deleted = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key="step45_filter_deleted",
            content=f"Step 45 deleted record {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert active and inactive and deleted

    app.memories_container.patch_item(
        item=inactive["memoryId"],
        partition_key=user_id,
        patch_operations=[
            {"op": "set", "path": "/active", "value": False},
        ],
    )

    soft_deleted = app.soft_delete_long_term_memory(
        memory_id=deleted["memoryId"],
        user_id=user_id,
    )

    assert soft_deleted is not None
    assert soft_deleted["deleted"] is True
    assert soft_deleted["active"] is False

    default_results = [
        item
        for item in app.get_user_memories(user_id)
        if item.get("sourceConversationId") == source_id
    ]

    assert {item["memoryId"] for item in default_results} == {
        active["memoryId"]
    }

    include_inactive = [
        item
        for item in app.get_user_memories(
            user_id,
            include_inactive=True,
            include_deleted=False,
        )
        if item.get("sourceConversationId") == source_id
    ]

    assert {item["memoryId"] for item in include_inactive} == {
        active["memoryId"],
        inactive["memoryId"],
    }

    include_all = [
        item
        for item in app.get_user_memories(
            user_id,
            include_inactive=True,
            include_deleted=True,
        )
        if item.get("sourceConversationId") == source_id
    ]

    assert {item["memoryId"] for item in include_all} == {
        active["memoryId"],
        inactive["memoryId"],
        deleted["memoryId"],
    }
