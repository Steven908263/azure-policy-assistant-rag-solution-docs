# I-28 Step 45 — Cosmos Integration Tests

These tests intentionally use the real **development** Cosmos DB `memories`
container configured in `local.settings.json`.

## Coverage

- Create and read a memory through the real persistence path
- User `/userId` partition isolation
- Duplicate prevention through `persist_memory_candidate`
- Active/deleted filtering using real Cosmos records
- Supersession of an older memory value
- Hard-delete verification and automatic cleanup

## Safety

Every test uses:
- synthetic random user IDs;
- a unique `sourceConversationId`;
- compact synthetic content;
- automatic teardown that queries only those synthetic partitions/source IDs
  and deletes test-created records.

Do not point `local.settings.json` at production resources when running Step 45.

## Prerequisites

1. Activate the project `.venv`.
2. Install the normal project dependencies and pytest.
3. Authenticate locally:
   `az login`
4. The signed-in development identity must have Cosmos data-plane access to
   the development database/container.
5. `LONG_TERM_MEMORY_ENABLED` must be true.

## Run

From the Azure Functions project root:

```powershell
.\run_step45_integration_tests.ps1
```

Or directly:

```powershell
$env:RUN_COSMOS_INTEGRATION_TESTS="true"
python -m pytest -c pytest-integration.ini tests/integration -m integration -v
```

If the tests pass, Step 45 can be marked COMPLETED / PASS.
