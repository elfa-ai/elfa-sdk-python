"""
Tests for V1 Compatibility Layer
"""

import time
import warnings
from unittest.mock import AsyncMock, Mock, patch

import pytest

from elfa import AsyncElfaClient, ElfaClient
from elfa.client.v1_compatibility import AsyncV1CompatibilityLayer, V1CompatibilityLayer


class TestV1CompatibilityLayer:
    """Test V1 compatibility layer for sync client"""

    @pytest.fixture
    def client(self):
        """Create test ElfaClient"""
        return ElfaClient(api_key="test-key")

    @pytest.fixture
    def v1_compat(self, client):
        """Create V1 compatibility layer"""
        return V1CompatibilityLayer(client, show_deprecation_warnings=False)

    @pytest.fixture
    def v1_compat_with_warnings(self, client):
        """Create V1 compatibility layer with warnings"""
        return V1CompatibilityLayer(client, show_deprecation_warnings=True)

    def test_v1_compat_initialization(self, client):
        """Test V1CompatibilityLayer initialization"""
        v1_compat = V1CompatibilityLayer(client, show_deprecation_warnings=False)

        assert v1_compat.client == client
        assert v1_compat.show_deprecation_warnings is False

    def test_v1_compat_deprecation_warnings(self, v1_compat_with_warnings):
        """Test deprecation warnings are shown"""
        with pytest.warns(DeprecationWarning, match="ping.*is deprecated"):
            with patch.object(v1_compat_with_warnings.client, "ping") as mock_ping:
                mock_ping.return_value = Mock(success=True)
                v1_compat_with_warnings.ping()

    def test_v1_compat_no_warnings(self, v1_compat):
        """Test no deprecation warnings when disabled"""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            with patch.object(v1_compat.client, "ping") as mock_ping:
                mock_ping.return_value = Mock(success=True)
                # Should not raise any warnings
                v1_compat.ping()

    def test_ping_compatibility(self, v1_compat):
        """Test V1-compatible ping method"""
        with patch.object(v1_compat.client, "ping") as mock_ping:
            mock_response = Mock(success=True, data={"message": "pong"})
            mock_ping.return_value = mock_response

            result = v1_compat.ping()

            assert result.success is True
            assert result.data["message"] == "pong"
            mock_ping.assert_called_once()

    def test_get_api_key_status_compatibility(self, v1_compat):
        """Test V1-compatible API key status method"""
        with patch.object(v1_compat.client, "get_api_key_status") as mock_status:
            mock_data = Mock()
            mock_data.name = "Test Key"
            mock_response = Mock(success=True, data=mock_data)
            mock_status.return_value = mock_response

            result = v1_compat.get_api_key_status()

            assert result.success is True
            assert result.data.name == "Test Key"
            mock_status.assert_called_once()

    def test_get_trending_tokens_v1_params(self, v1_compat):
        """Test V1-compatible trending tokens with camelCase parameters"""
        with patch.object(v1_compat.client, "get_trending_tokens") as mock_trending:
            mock_response = Mock(success=True, data=Mock(data=[]))
            mock_trending.return_value = mock_response

            result = v1_compat.get_trending_tokens(
                timeWindow="24h",  # V1 style: camelCase
                pageSize=20,  # V1 style: camelCase
                minMentions=5,  # V1 style: camelCase
            )

            assert result.success is True
            mock_trending.assert_called_once_with(
                time_window="24h",  # Converted to snake_case
                page=1,  # Default value
                page_size=20,  # Converted to snake_case
                min_mentions=5,  # Converted to snake_case
            )

    def test_get_mentions_by_keywords_short_timeframe(self, v1_compat):
        """Test V1 keyword mentions with short timeframe (uses V1 endpoint)"""
        with patch.object(v1_compat.client, "get_mentions_by_keywords_v1") as mock_v1:
            mock_response = Mock(success=True, data=[])
            mock_v1.return_value = mock_response

            # 24 hour timeframe (within 30 days)
            end_time = int(time.time())
            start_time = end_time - (24 * 60 * 60)

            result = v1_compat.get_mentions_by_keywords(
                keywords="bitcoin,ethereum",
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=30,
                searchType="or",  # V1 style: camelCase
            )

            assert result.success is True
            mock_v1.assert_called_once_with(
                keywords="bitcoin,ethereum",
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=30,
                search_type="or",  # Converted to snake_case
                cursor=None,
            )

    def test_get_mentions_by_keywords_long_timeframe(self, v1_compat):
        """Test V1 keyword mentions with long timeframe (uses V2 endpoint)"""
        with patch.object(v1_compat.client, "get_keyword_mentions") as mock_v2:
            mock_response = Mock(success=True, data=[])
            mock_v2.return_value = mock_response

            # 60 day timeframe (exceeds 30 days)
            end_time = int(time.time())
            start_time = end_time - (60 * 24 * 60 * 60)

            with pytest.warns(UserWarning, match="Timeframe exceeds 30 days"):
                result = v1_compat.get_mentions_by_keywords(
                    keywords="bitcoin,ethereum",
                    from_timestamp=start_time,
                    to_timestamp=end_time,
                    limit=30,
                    searchType="or",
                )

            assert result.success is True
            mock_v2.assert_called_once_with(
                keywords="bitcoin,ethereum",
                period="30d",  # Converted to period-based
                limit=30,
                search_type="or",
                cursor=None,
            )

    def test_get_mentions_with_smart_engagement_v1_params(self, v1_compat):
        """Test V1-compatible smart engagement with camelCase parameters"""
        with patch.object(
            v1_compat.client, "get_mentions_with_smart_engagement"
        ) as mock_smart:
            mock_response = Mock(success=True, data=[])
            mock_smart.return_value = mock_response

            end_time = int(time.time())
            start_time = end_time - (24 * 60 * 60)

            result = v1_compat.get_mentions_with_smart_engagement(
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=20,
                mentionedByType="smart",  # V1 style: camelCase
                sentiment="bullish",
                includeAccountInfo=True,  # V1 style: camelCase
                includeCoins=False,  # V1 style: camelCase
            )

            assert result.success is True
            mock_smart.assert_called_once_with(
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=20,
                mentioned_by_type="smart",  # Converted to snake_case
                sentiment="bullish",
                include_account_info=True,  # Converted to snake_case
                include_coins=False,  # Converted to snake_case
            )

    def test_get_account_smart_stats_compatibility(self, v1_compat):
        """Test V1-compatible account smart stats method"""
        with patch.object(v1_compat.client, "get_account_smart_stats") as mock_stats:
            mock_response = Mock(success=True, data=Mock(smart_following_count=100))
            mock_stats.return_value = mock_response

            result = v1_compat.get_account_smart_stats("testuser")

            assert result.success is True
            assert result.data.smart_following_count == 100
            mock_stats.assert_called_once_with("testuser")

    def test_get_migration_guide(self, v1_compat):
        """Test migration guide functionality"""
        guide = v1_compat.get_migration_guide()

        assert isinstance(guide, dict)
        assert len(guide) > 0

        # Check for expected migration mappings
        assert any("get_trending_tokens" in key for key in guide.keys())
        assert any("get_mentions_by_keywords" in key for key in guide.keys())
        assert any("Parameter naming" in key for key in guide.keys())

    def test_list_deprecated_methods(self, v1_compat):
        """Test listing deprecated methods"""
        deprecated = v1_compat.list_deprecated_methods()

        assert isinstance(deprecated, list)
        assert len(deprecated) > 0

        # Check for expected deprecated methods
        expected_methods = [
            "ping",
            "get_api_key_status",
            "get_trending_tokens",
            "get_mentions_by_keywords",
            "get_mentions_with_smart_engagement",
            "get_account_smart_stats",
        ]

        for method in expected_methods:
            assert method in deprecated


class TestAsyncV1CompatibilityLayer:
    """Test async V1 compatibility layer"""

    @pytest.fixture
    def async_client(self):
        """Create test AsyncElfaClient"""
        return AsyncElfaClient(api_key="test-key")

    @pytest.fixture
    def async_v1_compat(self, async_client):
        """Create async V1 compatibility layer"""
        return AsyncV1CompatibilityLayer(async_client, show_deprecation_warnings=False)

    @pytest.fixture
    def async_v1_compat_with_warnings(self, async_client):
        """Create async V1 compatibility layer with warnings"""
        return AsyncV1CompatibilityLayer(async_client, show_deprecation_warnings=True)

    def test_async_v1_compat_initialization(self, async_client):
        """Test AsyncV1CompatibilityLayer initialization"""
        v1_compat = AsyncV1CompatibilityLayer(
            async_client, show_deprecation_warnings=False
        )

        assert v1_compat.client == async_client
        assert v1_compat.show_deprecation_warnings is False

    @pytest.mark.asyncio
    async def test_async_ping_compatibility(self, async_v1_compat):
        """Test async V1-compatible ping method"""
        with patch.object(
            async_v1_compat.client, "ping", new_callable=AsyncMock
        ) as mock_ping:
            mock_response = Mock(success=True, data={"message": "pong"})
            mock_ping.return_value = mock_response

            result = await async_v1_compat.ping()

            assert result.success is True
            assert result.data["message"] == "pong"
            mock_ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_get_api_key_status_compatibility(self, async_v1_compat):
        """Test async V1-compatible API key status method"""
        with patch.object(
            async_v1_compat.client, "get_api_key_status", new_callable=AsyncMock
        ) as mock_status:
            mock_data = Mock()
            mock_data.name = "Test Key"
            mock_response = Mock(success=True, data=mock_data)
            mock_status.return_value = mock_response

            result = await async_v1_compat.get_api_key_status()

            assert result.success is True
            assert result.data.name == "Test Key"
            mock_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_get_trending_tokens_v1_params(self, async_v1_compat):
        """Test async V1-compatible trending tokens with camelCase parameters"""
        with patch.object(
            async_v1_compat.client, "get_trending_tokens", new_callable=AsyncMock
        ) as mock_trending:
            mock_response = Mock(success=True, data=Mock(data=[]))
            mock_trending.return_value = mock_response

            result = await async_v1_compat.get_trending_tokens(
                timeWindow="24h",  # V1 style: camelCase
                pageSize=20,  # V1 style: camelCase
                minMentions=5,  # V1 style: camelCase
            )

            assert result.success is True
            mock_trending.assert_called_once_with(
                time_window="24h",  # Converted to snake_case
                page=1,  # Default value
                page_size=20,  # Converted to snake_case
                min_mentions=5,  # Converted to snake_case
            )

    @pytest.mark.asyncio
    async def test_async_get_mentions_by_keywords_short_timeframe(
        self, async_v1_compat
    ):
        """Test async V1 keyword mentions with short timeframe"""
        with patch.object(
            async_v1_compat.client,
            "get_mentions_by_keywords_v1",
            new_callable=AsyncMock,
        ) as mock_v1:
            mock_response = Mock(success=True, data=[])
            mock_v1.return_value = mock_response

            # 24 hour timeframe
            end_time = int(time.time())
            start_time = end_time - (24 * 60 * 60)

            result = await async_v1_compat.get_mentions_by_keywords(
                keywords="bitcoin,ethereum",
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=30,
                searchType="or",  # V1 style: camelCase
            )

            assert result.success is True
            mock_v1.assert_called_once_with(
                keywords="bitcoin,ethereum",
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=30,
                search_type="or",  # Converted to snake_case
                cursor=None,
            )

    @pytest.mark.asyncio
    async def test_async_get_mentions_by_keywords_long_timeframe(self, async_v1_compat):
        """Test async V1 keyword mentions with long timeframe"""
        with patch.object(
            async_v1_compat.client, "get_keyword_mentions", new_callable=AsyncMock
        ) as mock_v2:
            mock_response = Mock(success=True, data=[])
            mock_v2.return_value = mock_response

            # 60 day timeframe
            end_time = int(time.time())
            start_time = end_time - (60 * 24 * 60 * 60)

            with pytest.warns(UserWarning, match="Timeframe exceeds 30 days"):
                result = await async_v1_compat.get_mentions_by_keywords(
                    keywords="bitcoin,ethereum",
                    from_timestamp=start_time,
                    to_timestamp=end_time,
                    limit=30,
                    searchType="or",
                )

            assert result.success is True
            mock_v2.assert_called_once_with(
                keywords="bitcoin,ethereum",
                period="30d",  # Converted to period-based
                limit=30,
                search_type="or",
                cursor=None,
            )

    @pytest.mark.asyncio
    async def test_async_get_mentions_with_smart_engagement_v1_params(
        self, async_v1_compat
    ):
        """Test async V1-compatible smart engagement with camelCase parameters"""
        with patch.object(
            async_v1_compat.client,
            "get_mentions_with_smart_engagement",
            new_callable=AsyncMock,
        ) as mock_smart:
            mock_response = Mock(success=True, data=[])
            mock_smart.return_value = mock_response

            end_time = int(time.time())
            start_time = end_time - (24 * 60 * 60)

            result = await async_v1_compat.get_mentions_with_smart_engagement(
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=20,
                mentionedByType="smart",  # V1 style: camelCase
                sentiment="bullish",
                includeAccountInfo=True,  # V1 style: camelCase
                includeCoins=False,  # V1 style: camelCase
            )

            assert result.success is True
            mock_smart.assert_called_once_with(
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=20,
                mentioned_by_type="smart",  # Converted to snake_case
                sentiment="bullish",
                include_account_info=True,  # Converted to snake_case
                include_coins=False,  # Converted to snake_case
            )

    @pytest.mark.asyncio
    async def test_async_get_account_smart_stats_compatibility(self, async_v1_compat):
        """Test async V1-compatible account smart stats method"""
        with patch.object(
            async_v1_compat.client, "get_account_smart_stats", new_callable=AsyncMock
        ) as mock_stats:
            mock_response = Mock(success=True, data=Mock(smart_following_count=100))
            mock_stats.return_value = mock_response

            result = await async_v1_compat.get_account_smart_stats("testuser")

            assert result.success is True
            assert result.data.smart_following_count == 100
            mock_stats.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_async_deprecation_warnings(self, async_v1_compat_with_warnings):
        """Test async deprecation warnings are shown"""
        with pytest.warns(DeprecationWarning, match="ping.*is deprecated"):
            with patch.object(
                async_v1_compat_with_warnings.client, "ping", new_callable=AsyncMock
            ) as mock_ping:
                mock_ping.return_value = Mock(success=True)
                await async_v1_compat_with_warnings.ping()


class TestV1CompatibilityIntegration:
    """Integration tests for V1 compatibility"""

    def test_parameter_conversion_edge_cases(self):
        """Test edge cases in parameter conversion"""
        client = ElfaClient(api_key="test-key")
        v1_compat = V1CompatibilityLayer(client, show_deprecation_warnings=False)

        with patch.object(client, "get_trending_tokens") as mock_trending:
            mock_trending.return_value = Mock(success=True)

            # Test with minimal parameters
            v1_compat.get_trending_tokens()

            # Should use defaults
            mock_trending.assert_called_with(
                time_window="24h", page=1, page_size=50, min_mentions=5
            )

    def test_timeframe_calculation_accuracy(self):
        """Test timeframe calculation for V1/V2 endpoint selection"""
        client = ElfaClient(api_key="test-key")
        v1_compat = V1CompatibilityLayer(client, show_deprecation_warnings=False)

        # Test exactly 30 days (should use V1)
        with patch.object(client, "get_mentions_by_keywords_v1") as mock_v1:
            mock_v1.return_value = Mock(success=True)

            end_time = int(time.time())
            start_time = end_time - (30 * 24 * 60 * 60)  # Exactly 30 days

            v1_compat.get_mentions_by_keywords(
                keywords="bitcoin", from_timestamp=start_time, to_timestamp=end_time
            )

            mock_v1.assert_called_once()

        # Test 30 days + 1 second (should use V2)
        with patch.object(client, "get_keyword_mentions") as mock_v2:
            mock_v2.return_value = Mock(success=True)

            end_time = int(time.time())
            start_time = end_time - (30 * 24 * 60 * 60) - 1  # 30 days + 1 second

            with pytest.warns(UserWarning):
                v1_compat.get_mentions_by_keywords(
                    keywords="bitcoin", from_timestamp=start_time, to_timestamp=end_time
                )

            mock_v2.assert_called_once()
