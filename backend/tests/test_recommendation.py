"""
test_recommendation.py
Unit tests for the AarogyaAid recommendation engine.

Run from backend/ directory:
    pytest tests/ -v

These tests mock all external dependencies (OpenAI, ChromaDB) so they
run offline without any API keys or a running database.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile():
    """A realistic user profile matching the RecommendationRequest schema."""
    from app.schemas.recommend import RecommendationRequest
    return RecommendationRequest(
        full_name="Priya Sharma",
        age=34,
        city_tier="metro",
        lifestyle="sedentary",
        pre_existing_conditions=["diabetes"],
        income_band="3to8l",
    )


@pytest.fixture
def mock_chunks():
    """Simulated ChromaDB retrieval results for two fictional policies."""
    return [
        {
            "document": (
                "MedProtect Plus covers pre-existing diabetes after a 2-year waiting period. "
                "Annual premium: ₹12,000. Cover: ₹5 lakh. Co-pay: 10% for Tier-2 cities."
            ),
            "metadata": {
                "policy_id": "1",
                "policy_name": "MedProtect Plus",
                "insurer": "HealthFirst Insurance",
                "page_number": 1,
                "chunk_index": 0,
            },
            "distance": 0.12,
        },
        {
            "document": (
                "CareShield Basic offers ₹3 lakh cover at ₹6,500 annual premium. "
                "Pre-existing conditions covered after 4-year waiting period. No OPD cover."
            ),
            "metadata": {
                "policy_id": "2",
                "policy_name": "CareShield Basic",
                "insurer": "SafeGuard General",
                "page_number": 1,
                "chunk_index": 0,
            },
            "distance": 0.28,
        },
    ]


@pytest.fixture
def mock_openai_recommendation_response():
    """A well-formed JSON response matching the RecommendationResponse schema."""
    return json.dumps({
        "best_fit": {
            "policy_name": "MedProtect Plus",
            "insurer": "HealthFirst Insurance",
            "premium": "₹12,000/year",
            "cover_amount": "₹5 lakh",
        },
        "peer_comparison": [
            {
                "policy_name": "CareShield Basic",
                "insurer": "SafeGuard General",
                "premium": "₹6,500/year",
                "cover_amount": "₹3 lakh",
                "waiting_period": "4 years",
                "key_benefit": "Low premium entry plan",
                "suitability_score": 62,
            }
        ],
        "coverage_detail": {
            "inclusions": ["Hospitalisation", "Day-care procedures", "Ambulance cover"],
            "exclusions": ["Cosmetic surgery", "Self-inflicted injuries"],
            "sub_limits": "Room rent capped at ₹3,000/day",
            "co_pay": "10% for metro hospitals",
            "claim_type": "Cashless and reimbursement",
        },
        "why_this_policy": (
            "Priya, as a 34-year-old metro resident managing diabetes on a mid-range income, "
            "MedProtect Plus is your strongest match. It covers diabetes-related hospitalisation "
            "after a 2-year waiting period — shorter than most alternatives — and its ₹5 lakh "
            "cover is adequate for metro hospital costs. The ₹12,000 annual premium fits "
            "comfortably within a ₹3–8 lakh income band. CareShield Basic is cheaper but its "
            "4-year waiting period for pre-existing conditions makes it a poor fit given your "
            "current health profile."
        ),
        "citations": ["MedProtect Plus (Page 1)", "CareShield Basic (Page 1)"],
    })


# ---------------------------------------------------------------------------
# Query generation tests (pure logic, no mocking needed)
# ---------------------------------------------------------------------------

class TestQueryGeneration:
    """Tests for generate_query_from_profile — pure string logic, no I/O."""

    def test_query_contains_age_and_city(self, sample_profile):
        from app.ai.recommend_engine import generate_query_from_profile
        query = generate_query_from_profile(sample_profile)
        assert "34" in query
        assert "metro" in query

    def test_query_contains_conditions(self, sample_profile):
        from app.ai.recommend_engine import generate_query_from_profile
        query = generate_query_from_profile(sample_profile)
        assert "diabetes" in query

    def test_query_appends_waiting_period_hint_for_conditions(self, sample_profile):
        from app.ai.recommend_engine import generate_query_from_profile
        query = generate_query_from_profile(sample_profile)
        assert "waiting period" in query.lower()

    def test_query_no_conditions_uses_healthy_fallback(self):
        from app.schemas.recommend import RecommendationRequest
        from app.ai.recommend_engine import generate_query_from_profile
        profile = RecommendationRequest(
            full_name="Rahul Verma",
            age=28,
            city_tier="tier2",
            lifestyle="active",
            pre_existing_conditions=[],
            income_band="8to15l",
        )
        query = generate_query_from_profile(profile)
        assert "healthy" in query.lower()

    def test_query_appends_opd_hint_for_active_lifestyle(self):
        from app.schemas.recommend import RecommendationRequest
        from app.ai.recommend_engine import generate_query_from_profile
        profile = RecommendationRequest(
            full_name="Ankit Joshi",
            age=25,
            city_tier="metro",
            lifestyle="Active",
            pre_existing_conditions=[],
            income_band="8to15l",
        )
        query = generate_query_from_profile(profile)
        assert "OPD" in query or "wellness" in query.lower()


# ---------------------------------------------------------------------------
# Recommendation engine integration tests (mocked I/O)
# ---------------------------------------------------------------------------

class TestGenerateRecommendation:
    """Tests for generate_recommendation — mocks ChromaDB and OpenAI."""

    def _make_openai_mock(self, content: str):
        """Helper: build a mock that looks like an openai ChatCompletion response."""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_response_has_required_top_level_keys(
        self, mock_client, mock_search, sample_profile,
        mock_chunks, mock_openai_recommendation_response
    ):
        """The response dict must contain all keys defined in RecommendationResponse."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.return_value = self._make_openai_mock(
            mock_openai_recommendation_response
        )

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        required_keys = {"best_fit", "peer_comparison", "coverage_detail",
                         "why_this_policy", "citations"}
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_why_this_policy_is_non_empty_string(
        self, mock_client, mock_search, sample_profile,
        mock_chunks, mock_openai_recommendation_response
    ):
        """why_this_policy must be a non-empty string."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.return_value = self._make_openai_mock(
            mock_openai_recommendation_response
        )

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        assert isinstance(result["why_this_policy"], str)
        assert len(result["why_this_policy"].strip()) > 0

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_peer_comparison_is_list(
        self, mock_client, mock_search, sample_profile,
        mock_chunks, mock_openai_recommendation_response
    ):
        """peer_comparison must be a list (can be empty)."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.return_value = self._make_openai_mock(
            mock_openai_recommendation_response
        )

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        assert isinstance(result["peer_comparison"], list)

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_best_fit_has_required_fields(
        self, mock_client, mock_search, sample_profile,
        mock_chunks, mock_openai_recommendation_response
    ):
        """best_fit must contain policy_name, insurer, premium, cover_amount."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.return_value = self._make_openai_mock(
            mock_openai_recommendation_response
        )

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        best_fit = result.get("best_fit")
        assert best_fit is not None
        for field in ("policy_name", "insurer", "premium", "cover_amount"):
            assert field in best_fit, f"best_fit missing field: {field}"

    @patch("app.ai.recommend_engine.search_policy_chunks")
    def test_empty_chroma_returns_graceful_fallback(self, mock_search, sample_profile):
        """When ChromaDB returns no chunks, the engine must return a graceful fallback
        with why_this_policy set and best_fit as None — no exception raised."""
        mock_search.return_value = []  # empty vector store

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        assert result["best_fit"] is None
        assert isinstance(result["why_this_policy"], str)
        assert len(result["why_this_policy"]) > 0
        assert result["peer_comparison"] == []
        assert result["citations"] == []

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_citations_is_list(
        self, mock_client, mock_search, sample_profile,
        mock_chunks, mock_openai_recommendation_response
    ):
        """citations must be a list."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.return_value = self._make_openai_mock(
            mock_openai_recommendation_response
        )

        from app.ai.recommend_engine import generate_recommendation
        result = generate_recommendation(sample_profile)

        assert isinstance(result["citations"], list)

    @patch("app.ai.recommend_engine.search_policy_chunks")
    @patch("app.ai.recommend_engine.openai_client")
    def test_openai_failure_raises_value_error(
        self, mock_client, mock_search, sample_profile, mock_chunks
    ):
        """If OpenAI throws, generate_recommendation must raise ValueError."""
        mock_search.return_value = mock_chunks
        mock_client.chat.completions.create.side_effect = Exception("API timeout")

        from app.ai.recommend_engine import generate_recommendation
        with pytest.raises(ValueError, match="OpenAI Generation Failed"):
            generate_recommendation(sample_profile)


# ---------------------------------------------------------------------------
# Chunking service tests (pure logic)
# ---------------------------------------------------------------------------

class TestChunkService:
    """Tests for chunk_document — no external dependencies."""

    def test_basic_chunking_produces_chunks(self):
        from app.services.chunk_service import chunk_document
        pages = [{"page": 1, "text": " ".join([f"word{i}" for i in range(500)])}]
        chunks = chunk_document(pages)
        assert len(chunks) > 1

    def test_chunk_has_required_keys(self):
        from app.services.chunk_service import chunk_document
        pages = [{"page": 1, "text": "This is a test document with enough words to chunk."}]
        chunks = chunk_document(pages)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert "text" in chunk
            assert "page_number" in chunk
            assert "chunk_index" in chunk

    def test_empty_page_produces_no_chunks(self):
        from app.services.chunk_service import chunk_document
        pages = [{"page": 1, "text": ""}]
        chunks = chunk_document(pages)
        assert chunks == []

    def test_overlap_creates_more_chunks_than_no_overlap(self):
        from app.services.chunk_service import chunk_document
        text = " ".join([f"word{i}" for i in range(600)])
        pages = [{"page": 1, "text": text}]
        chunks_with_overlap    = chunk_document(pages, chunk_size=300, overlap=50)
        chunks_without_overlap = chunk_document(pages, chunk_size=300, overlap=0)
        assert len(chunks_with_overlap) >= len(chunks_without_overlap)

    def test_page_number_preserved_in_chunks(self):
        from app.services.chunk_service import chunk_document
        pages = [
            {"page": 3, "text": " ".join([f"word{i}" for i in range(100)])},
        ]
        chunks = chunk_document(pages)
        for chunk in chunks:
            assert chunk["page_number"] == 3


# ---------------------------------------------------------------------------
# Security / auth utility tests (pure logic)
# ---------------------------------------------------------------------------

class TestSecurity:
    """Tests for password hashing and JWT utilities."""

    def test_hash_and_verify_password(self):
        from app.core.security import get_password_hash, verify_password
        plain = "SecurePass123!"
        hashed = get_password_hash(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails_verification(self):
        from app.core.security import get_password_hash, verify_password
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_create_and_decode_access_token(self):
        from app.core.security import create_access_token, decode_access_token
        payload = {"sub": "testuser", "role": "user"}
        token = create_access_token(data=payload)
        assert isinstance(token, str)
        decoded = decode_access_token(token)
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "user"

    def test_different_passwords_produce_different_hashes(self):
        from app.core.security import get_password_hash
        h1 = get_password_hash("password_one")
        h2 = get_password_hash("password_two")
        assert h1 != h2
