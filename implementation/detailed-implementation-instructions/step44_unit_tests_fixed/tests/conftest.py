\
import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# Safe synthetic settings used only while importing function_app for unit tests.
_UNIT_TEST_ENV = {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SEARCH_ENDPOINT": "https://unit-test.search.windows.net",
    "AZURE_SEARCH_INDEX_NAME": "unit-test-index",
    "AZURE_SEARCH_CONTENT_FIELD": "chunk",
    "AZURE_SEARCH_VECTOR_FIELD": "text_vector",
    "AZURE_SEARCH_SOURCE_FIELD": "title",
    "AZURE_OPENAI_ENDPOINT": "https://unit-test.openai.azure.com",
    "AZURE_OPENAI_DEPLOYMENT": "unit-test-deployment",
    "COSMOS_ENDPOINT": "https://unit-test.documents.azure.com:443/",
    "COSMOS_DATABASE": "unit-test-db",
    "COSMOS_DATABASE_NAME": "unit-test-db",
    "COSMOS_CONVERSATIONS_CONTAINER": "conversations",
    "COSMOS_MESSAGES_CONTAINER": "messages",
    "COSMOS_MEMORIES_CONTAINER": "memories",
    "ENTRA_TENANT_ID": "00000000-0000-4000-8000-000000000001",
    "ENTRA_API_CLIENT_ID": "00000000-0000-4000-8000-000000000002",
    "OBO_TENANT_ID": "00000000-0000-4000-8000-000000000001",
    "OBO_CLIENT_ID": "00000000-0000-4000-8000-000000000002",
    "OBO_CLIENT_SECRET": "unit-test-secret-not-real",
    "POLICY_SYSTEM_PROMPT_VERSION": "3.0",
    "POLICY_SYSTEM_PROMPT_FILE": "prompts/policy_assistant_system_v3.txt",
    "LONG_TERM_MEMORY_MAX_ITEM_CHARS": "1000",
    "LONG_TERM_MEMORY_MIN_CONFIDENCE": "0.75",
    "LONG_TERM_MEMORY_MIN_IMPORTANCE": "0.50",
    "LONG_TERM_MEMORY_ENABLED": "true",
    "MEMORY_DEV_VALIDATION_ENABLED": "false",
}

for _name, _value in _UNIT_TEST_ENV.items():
    os.environ.setdefault(_name, _value)


class FakeMemoriesContainer:
    """
    Minimal Cosmos-container fake used by Step 44 unit tests.
    """

    def __init__(self, *, read_item_result=None, query_results=None):
        self.read_item_result = read_item_result
        self.query_results = list(query_results or [])
        self.read_calls = []
        self.query_calls = []
        self.create_calls = []
        self.patch_calls = []
        self.delete_calls = []

    def read_item(self, *, item, partition_key):
        self.read_calls.append(
            {"item": item, "partition_key": partition_key}
        )
        if isinstance(self.read_item_result, Exception):
            raise self.read_item_result
        return self.read_item_result

    def query_items(self, *, query, parameters, partition_key, **kwargs):
        self.query_calls.append(
            {
                "query": query,
                "parameters": parameters,
                "partition_key": partition_key,
                **kwargs,
            }
        )
        return list(self.query_results)

    def create_item(self, *, body):
        self.create_calls.append({"body": body})
        return dict(body)

    def patch_item(self, *, item, partition_key, patch_operations):
        self.patch_calls.append(
            {
                "item": item,
                "partition_key": partition_key,
                "patch_operations": patch_operations,
            }
        )
        return {
            "id": item,
            "memoryId": item,
            "userId": partition_key,
        }

    def delete_item(self, *, item, partition_key):
        self.delete_calls.append(
            {"item": item, "partition_key": partition_key}
        )


@pytest.fixture(scope="session")
def app_module():
    """
    Import the real orchestration module with external Azure/OpenAI clients
    replaced before import.

    This is critical: function_app creates Cosmos/Search/OpenAI clients at module
    import time. If they are not patched before import, the Cosmos SDK attempts a
    real network request even when a fake endpoint is configured.
    """

    if "function_app" in sys.modules:
        del sys.modules["function_app"]

    fake_database = MagicMock(name="fake_database")
    fake_database.get_container_client.side_effect = [
        MagicMock(name="conversations_container"),
        MagicMock(name="messages_container"),
        MagicMock(name="memories_container"),
    ]

    fake_cosmos_client = MagicMock(name="fake_cosmos_client")
    fake_cosmos_client.get_database_client.return_value = fake_database

    fake_credential = MagicMock(name="fake_credential")
    fake_search_client = MagicMock(name="fake_search_client")
    fake_openai_client = MagicMock(name="fake_openai_client")
    fake_token_provider = MagicMock(name="fake_token_provider")

    # Patch the symbols at their SOURCE modules before importing function_app.
    # Because function_app uses "from ... import X", pre-import patching is needed.
    with (
        patch(
            "azure.cosmos.CosmosClient",
            return_value=fake_cosmos_client,
        ),
        patch(
            "azure.identity.DefaultAzureCredential",
            return_value=fake_credential,
        ),
        patch(
            "azure.identity.get_bearer_token_provider",
            return_value=fake_token_provider,
        ),
        patch(
            "azure.search.documents.SearchClient",
            return_value=fake_search_client,
        ),
        patch(
            "openai.OpenAI",
            return_value=fake_openai_client,
        ),
        patch(
            "jwt.PyJWKClient",
            return_value=MagicMock(name="fake_jwks_client"),
        ),
    ):
        module = importlib.import_module("function_app")

    return module


@pytest.fixture
def valid_memory_candidate():
    return {
        "type": "project_context",
        "memoryKey": "current_ai_project",
        "content": "User is building the Corporate Policy Assistant.",
        "confidence": 0.95,
        "importance": 0.80,
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
