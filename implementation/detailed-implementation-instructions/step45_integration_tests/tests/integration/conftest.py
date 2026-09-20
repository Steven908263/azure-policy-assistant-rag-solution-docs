import importlib
import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from azure.cosmos.exceptions import CosmosResourceNotFoundError


REQUIRED_SETTINGS = {
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_INDEX_NAME",
    "AZURE_SEARCH_CONTENT_FIELD",
    "AZURE_SEARCH_VECTOR_FIELD",
    "AZURE_SEARCH_SOURCE_FIELD",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT",
    "COSMOS_ENDPOINT",
    "COSMOS_DATABASE",
    "COSMOS_CONVERSATIONS_CONTAINER",
    "COSMOS_MESSAGES_CONTAINER",
    "COSMOS_MEMORIES_CONTAINER",
    "ENTRA_TENANT_ID",
    "ENTRA_API_CLIENT_ID",
    "OBO_TENANT_ID",
    "OBO_CLIENT_ID",
    "OBO_CLIENT_SECRET",
    "POLICY_SYSTEM_PROMPT_VERSION",
    "POLICY_SYSTEM_PROMPT_FILE",
}


def _project_root() -> Path:
    # tests/integration/conftest.py -> project root
    return Path(__file__).resolve().parents[2]


def _load_local_settings() -> dict:
    settings_path = _project_root() / "local.settings.json"

    if not settings_path.exists():
        pytest.fail(
            f"Step 45 requires {settings_path}. "
            "Run the integration tests from the Azure Functions project."
        )

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    values = data.get("Values", {})

    missing = sorted(
        name for name in REQUIRED_SETTINGS
        if not values.get(name)
    )

    if missing:
        pytest.fail(
            "local.settings.json is missing required Step 45 settings: "
            + ", ".join(missing)
        )

    # Override the synthetic values established by the parent unit-test
    # conftest.py. Step 45 intentionally uses the development resources.
    for name, value in values.items():
        os.environ[name] = str(value)

    # Step 45 must exercise the persistence/retrieval path.
    os.environ["LONG_TERM_MEMORY_ENABLED"] = "true"

    return values


@pytest.fixture(scope="session")
def integration_app():
    """
    Import the real function_app against development Azure resources.

    Unlike Step 44, no Cosmos/Search/identity clients are mocked here.
    """
    if os.getenv("RUN_COSMOS_INTEGRATION_TESTS", "").strip().lower() not in {
        "1", "true", "yes", "on"
    }:
        pytest.skip(
            "Set RUN_COSMOS_INTEGRATION_TESTS=true to run Step 45."
        )

    _load_local_settings()

    # Step 44 may already have imported a mocked function_app in the same
    # pytest process. Force a fresh import after restoring real settings.
    sys.modules.pop("function_app", None)
    module = importlib.import_module("function_app")

    if not module.LONG_TERM_MEMORY_ENABLED:
        pytest.fail(
            "Step 45 requires LONG_TERM_MEMORY_ENABLED=true."
        )

    return module


@pytest.fixture
def step45_case(integration_app):
    """
    Provide isolated synthetic users and a unique sourceConversationId.

    Teardown deletes every record created under the unique source ID, even if
    the test itself fails partway through.
    """
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    source_id = f"i28-step45-{uuid.uuid4()}"

    context = {
        "app": integration_app,
        "user_a": user_a,
        "user_b": user_b,
        "source_id": source_id,
    }

    yield context

    # Cleanup is partition-scoped and limited to this test's unique source ID.
    for user_id in (user_a, user_b):
        try:
            records = list(
                integration_app.memories_container.query_items(
                    query=(
                        "SELECT c.id FROM c "
                        "WHERE c.userId = @userId "
                        "AND c.sourceConversationId = @sourceConversationId"
                    ),
                    parameters=[
                        {"name": "@userId", "value": user_id},
                        {
                            "name": "@sourceConversationId",
                            "value": source_id,
                        },
                    ],
                    partition_key=user_id,
                )
            )

            for record in records:
                try:
                    integration_app.memories_container.delete_item(
                        item=record["id"],
                        partition_key=user_id,
                    )
                except CosmosResourceNotFoundError:
                    pass
        except Exception as exc:
            # Cleanup failure should be visible and fail the test rather than
            # silently leaving Step 45 data behind.
            pytest.fail(
                f"Step 45 cleanup failed for user {user_id}: {exc}"
            )


def build_candidate(
    *,
    memory_key: str,
    content: str,
    memory_type: str = "project_context",
    confidence: float = 0.95,
    importance: float = 0.80,
) -> dict:
    return {
        "type": memory_type,
        "memoryKey": memory_key,
        "content": content,
        "confidence": confidence,
        "importance": importance,
        "isDurable": True,
        "usefulAcrossConversations": True,
        "isOneTime": False,
        "isTransient": False,
        "containsCurrentPolicyEvidence": False,
        "isTransientQuestion": False,
        "containsSecretOrToken": False,
        "containsAuthorizationId": False,
        "containsRestrictedPolicyContent": False,
        "containsRawPolicyText": False,
        "isFullConversationTranscript": False,
    }
