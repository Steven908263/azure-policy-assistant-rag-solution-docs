\
from conftest import FakeMemoriesContainer


def test_get_user_memories_scopes_query_to_authenticated_partition(
    app_module,
    monkeypatch,
):
    fake = FakeMemoriesContainer(query_results=[])
    monkeypatch.setattr(app_module, "memories_container", fake)

    result = app_module.get_user_memories("user-a")

    assert result == []
    assert len(fake.query_calls) == 1

    call = fake.query_calls[0]
    assert call["partition_key"] == "user-a"
    assert {"name": "@userId", "value": "user-a"} in call["parameters"]
    assert "m.userId = @userId" in call["query"]


def test_get_authorized_memory_returns_owned_record(
    app_module,
    monkeypatch,
):
    record = {
        "id": "memory-1",
        "memoryId": "memory-1",
        "userId": "user-a",
    }
    fake = FakeMemoriesContainer(read_item_result=record)
    monkeypatch.setattr(app_module, "memories_container", fake)

    result = app_module.get_authorized_memory("memory-1", "user-a")

    assert result == record
    assert fake.read_calls == [
        {"item": "memory-1", "partition_key": "user-a"}
    ]


def test_get_authorized_memory_rejects_owner_mismatch_defense_in_depth(
    app_module,
    monkeypatch,
):
    # Simulates a malformed/unexpected record being returned even though the
    # caller correctly used User A's partition. The defense-in-depth owner check
    # must still reject it.
    wrong_owner_record = {
        "id": "memory-1",
        "memoryId": "memory-1",
        "userId": "user-b",
    }
    fake = FakeMemoriesContainer(read_item_result=wrong_owner_record)
    monkeypatch.setattr(app_module, "memories_container", fake)

    result = app_module.get_authorized_memory("memory-1", "user-a")

    assert result is None
