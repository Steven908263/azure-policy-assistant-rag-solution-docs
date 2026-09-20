\
import pytest


@pytest.mark.parametrize(
    ("changes", "expected_reason"),
    [
        ({"type": "unsupported_type"}, "unsupported_memory_type"),
        ({"memoryKey": "bad key!"}, "invalid_memory_key"),
        ({"content": ""}, "empty_content"),
        ({"isDurable": False}, "not_durable"),
        (
            {"usefulAcrossConversations": False},
            "not_useful_across_conversations",
        ),
        ({"isOneTime": True}, "one_time_detail"),
        ({"isTransient": True}, "transient_detail"),
        ({"isTransientQuestion": True}, "transient_question"),
        ({"containsSecretOrToken": True}, "secret_or_token"),
        ({"containsAuthorizationId": True}, "authorization_id"),
        (
            {"containsRestrictedPolicyContent": True},
            "restricted_policy_content",
        ),
        ({"containsRawPolicyText": True}, "raw_policy_text"),
        (
            {"containsCurrentPolicyEvidence": True},
            "current_policy_evidence_not_memory",
        ),
        (
            {"isFullConversationTranscript": True},
            "full_conversation_transcript",
        ),
        ({"confidence": 0.74}, "confidence_below_minimum"),
        ({"importance": 0.49}, "importance_below_minimum"),
    ],
)
def test_candidate_rejection_matrix(
    app_module,
    valid_memory_candidate,
    changes,
    expected_reason,
):
    candidate = dict(valid_memory_candidate)
    candidate.update(changes)

    is_valid, reason, validated = app_module.validate_memory_candidate(candidate)

    assert is_valid is False
    assert reason == expected_reason
    assert validated is None


def test_candidate_larger_than_configured_max_is_rejected(
    app_module,
    valid_memory_candidate,
):
    candidate = dict(valid_memory_candidate)
    candidate["content"] = "x" * (
        app_module.LONG_TERM_MEMORY_MAX_ITEM_CHARS + 1
    )

    is_valid, reason, validated = app_module.validate_memory_candidate(candidate)

    assert is_valid is False
    assert reason == "content_too_long"
    assert validated is None


def test_server_side_secret_scanner_rejects_bearer_token(
    app_module,
    valid_memory_candidate,
):
    candidate = dict(valid_memory_candidate)
    candidate["content"] = (
        "Bearer abcdefghijklmnopqrstuvwxyz1234567890"
    )

    is_valid, reason, validated = app_module.validate_memory_candidate(candidate)

    assert is_valid is False
    assert reason == "prohibited_bearer_token"
    assert validated is None


def test_server_side_authorization_identifier_scanner_rejects_tenant_id(
    app_module,
    valid_memory_candidate,
):
    candidate = dict(valid_memory_candidate)
    candidate["content"] = (
        "tenant id: 11111111-1111-4111-8111-111111111111"
    )

    is_valid, reason, validated = app_module.validate_memory_candidate(candidate)

    assert is_valid is False
    assert reason == "prohibited_security_identifier"
    assert validated is None
