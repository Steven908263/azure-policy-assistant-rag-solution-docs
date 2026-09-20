import pytest

from conftest import build_candidate


pytestmark = pytest.mark.integration


def test_real_cosmos_partition_isolation(step45_case):
    app = step45_case["app"]
    user_a = step45_case["user_a"]
    user_b = step45_case["user_b"]
    source_id = step45_case["source_id"]

    created = app.persist_memory_candidate(
        user_id=user_a,
        candidate=build_candidate(
            memory_key="step45_isolation",
            content=f"Step 45 isolation memory {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert created is not None
    memory_id = created["memoryId"]

    assert (
        app.get_authorized_memory(
            memory_id=memory_id,
            user_id=user_a,
        )
        is not None
    )

    # Same item ID through a different /userId partition must not be readable.
    assert (
        app.get_authorized_memory(
            memory_id=memory_id,
            user_id=user_b,
        )
        is None
    )

    user_b_memories = app.get_user_memories(
        user_id=user_b,
        include_inactive=True,
        include_deleted=True,
    )

    assert all(
        item.get("memoryId") != memory_id
        for item in user_b_memories
    )
