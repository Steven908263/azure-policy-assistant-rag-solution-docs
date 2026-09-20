# I-28 Step 44 — Unit Tests (fixed import isolation)

The original test bootstrap allowed `function_app.py` to construct a real
`CosmosClient` during module import. The Azure Cosmos SDK immediately performs
account discovery, so the synthetic endpoint was contacted before the tests
could replace the container.

This revised `tests/conftest.py` patches these external constructors **before**
`function_app` is imported:

- `azure.cosmos.CosmosClient`
- `azure.identity.DefaultAzureCredential`
- `azure.identity.get_bearer_token_provider`
- `azure.search.documents.SearchClient`
- `openai.OpenAI`
- `jwt.PyJWKClient`

The Step 44 tests therefore remain unit tests and make no external Azure calls.

Run:

```powershell
python -m pytest
```
