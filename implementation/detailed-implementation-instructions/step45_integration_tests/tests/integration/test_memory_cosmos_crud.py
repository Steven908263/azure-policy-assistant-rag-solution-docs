import pytest

from conftest import build_candidate


pytestmark = pytest.mark.integration


def test_real_cosmos_create_read_and_hard_delete(step45_case):
    app = step45_case["app"]
    user_id = step45_case["user_a"]
    source_id = step45_case["source_id"]

    created = app.persist_memory_candidate(
        user_id=user_id,
        candidate=build_candidate(
            memory_key="step45_crud",
            content=f"Step 45 CRUD integration test {source_id}",
        ),
        source_conversation_id=source_id,
        source_message_ids=[],
    )

    assert created is not None
    memory_id = created["memoryId"]
    assert created["userId"] == user_id
    assert created["active"] is True
    assert created["deleted"] is False

    read_back = app.get_authorized_memory(
        memory_id=memory_id,
        user_id=user_id,
    )

    assert read_back is not None
    assert read_back["memoryId"] == memory_id
    assert read_back["sourceConversationId"] == source_id

    deleted = app.delete_long_term_memory(
        memory_id=memory_id,
        user_id=user_id,
    )

    assert deleted is True
    assert (
        app.get_authorized_memory(
            memory_id=memory_id,
            user_id=user_id,
        )
        is None
    )
