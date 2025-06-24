"""
Response enhancer for combining Elfa API data with Twitter API content
"""

import asyncio
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

from elfa.client.twitter_client import TwitterClient, TwitterTweet, TwitterUser
from elfa.models.base import BaseResponse
from elfa.models.mentions import Mention, SimpleMention, V2Mention

T = TypeVar("T")


class EnhancementConfig(BaseModel):
    """Configuration for response enhancement"""

    fetch_raw_tweets: bool = Field(
        default=False, description="Whether to fetch raw tweet content"
    )
    enhancement_timeout: float = Field(
        default=30.0, description="Timeout for enhancement requests"
    )
    max_batch_size: int = Field(
        default=50, description="Maximum tweets to enhance in one batch"
    )
    strict_mode: bool = Field(
        default=False, description="Fail if any enhancement fails"
    )
    cache_enhancements: bool = Field(
        default=True, description="Cache enhancement results"
    )
    include_user_data: bool = Field(
        default=True, description="Include enhanced user data"
    )


class DataSource(BaseModel):
    """Indicates the source of response data"""

    elfa_api: bool = Field(default=True, description="Data from Elfa API")
    twitter_api: bool = Field(default=False, description="Enhanced with Twitter API")
    enhancement_timestamp: Optional[str] = Field(
        None, description="When enhancement was performed"
    )
    enhancement_success: bool = Field(
        default=True, description="Whether enhancement was successful"
    )


class EnhancedV2Mention(V2Mention):
    """Enhanced V2 mention with Twitter API data"""

    raw_tweet_text: Optional[str] = Field(
        None, description="Full tweet text from Twitter API"
    )
    twitter_user: Optional[TwitterUser] = Field(
        None, description="Enhanced user data from Twitter API"
    )
    twitter_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Twitter API metrics"
    )
    context_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Twitter context annotations"
    )
    entities: Optional[Dict[str, Any]] = Field(
        None, description="Twitter entities (hashtags, mentions, etc.)"
    )
    referenced_tweets: Optional[List[Dict[str, Any]]] = Field(
        None, description="Referenced tweets"
    )
    data_source: DataSource = Field(
        default_factory=DataSource, description="Data source indicators"
    )


class EnhancedMention(Mention):
    """Enhanced V1 mention with Twitter API data"""

    raw_tweet_text: Optional[str] = Field(
        None, description="Full tweet text from Twitter API"
    )
    twitter_user: Optional[TwitterUser] = Field(
        None, description="Enhanced user data from Twitter API"
    )
    twitter_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Twitter API metrics"
    )
    context_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Twitter context annotations"
    )
    entities: Optional[Dict[str, Any]] = Field(None, description="Twitter entities")
    referenced_tweets: Optional[List[Dict[str, Any]]] = Field(
        None, description="Referenced tweets"
    )
    data_source: DataSource = Field(
        default_factory=DataSource, description="Data source indicators"
    )


class EnhancedSimpleMention(SimpleMention):
    """Enhanced simple mention with Twitter API data"""

    raw_tweet_text: Optional[str] = Field(
        None, description="Full tweet text from Twitter API"
    )
    twitter_user: Optional[TwitterUser] = Field(
        None, description="Enhanced user data from Twitter API"
    )
    twitter_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Twitter API metrics"
    )
    context_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Twitter context annotations"
    )
    entities: Optional[Dict[str, Any]] = Field(None, description="Twitter entities")
    referenced_tweets: Optional[List[Dict[str, Any]]] = Field(
        None, description="Referenced tweets"
    )
    data_source: DataSource = Field(
        default_factory=DataSource, description="Data source indicators"
    )


class ResponseEnhancer:
    """
    Enhances Elfa API responses with Twitter API data

    This class takes Elfa API responses and enriches them with additional
    data from the Twitter API, including full tweet text, enhanced metrics,
    and user information.

    Args:
        twitter_client: Configured Twitter API client
        config: Enhancement configuration

    Example:
        ```python
        from elfa.client.twitter_client import TwitterClient, TwitterConfig
        from elfa.client.response_enhancer import ResponseEnhancer, EnhancementConfig

        # Setup Twitter client
        twitter_config = TwitterConfig(bearer_token="your-token")
        twitter_client = TwitterClient(twitter_config)

        # Setup enhancer
        enhancement_config = EnhancementConfig(
            fetch_raw_tweets=True,
            max_batch_size=50
        )
        enhancer = ResponseEnhancer(twitter_client, enhancement_config)

        # Enhance Elfa response
        elfa_response = client.get_keyword_mentions(keywords="bitcoin")
        enhanced_response = await enhancer.enhance_mentions_response(elfa_response)

        # Access enhanced data
        for mention in enhanced_response.data:
            if mention.raw_tweet_text:
                print(f"Full tweet: {mention.raw_tweet_text}")
        ```
    """

    def __init__(
        self,
        twitter_client: TwitterClient,
        config: EnhancementConfig = None,
    ):
        self.twitter_client = twitter_client
        self.config = config or EnhancementConfig()
        self._cache: Dict[str, TwitterTweet] = (
            {} if self.config.cache_enhancements else None
        )

    def _extract_tweet_id(
        self, mention: Union[V2Mention, Mention, SimpleMention]
    ) -> Optional[str]:
        """Extract tweet ID from mention object"""
        if hasattr(mention, "tweet_id"):
            return mention.tweet_id
        elif hasattr(mention, "twitter_id"):
            return mention.twitter_id
        elif hasattr(mention, "id"):
            return str(mention.id)
        return None

    def _extract_username(
        self, mention: Union[V2Mention, Mention, SimpleMention]
    ) -> Optional[str]:
        """Extract username from mention object"""
        if hasattr(mention, "account") and mention.account:
            if hasattr(mention.account, "username"):
                return mention.account.username
        elif hasattr(mention, "twitter_account_info") and mention.twitter_account_info:
            if hasattr(mention.twitter_account_info, "username"):
                return mention.twitter_account_info.username
        return None

    async def _enhance_mentions_batch(
        self,
        mentions: List[Union[V2Mention, Mention, SimpleMention]],
    ) -> List[Union[EnhancedV2Mention, EnhancedMention, EnhancedSimpleMention]]:
        """Enhance a batch of mentions with Twitter data"""
        if not self.config.fetch_raw_tweets:
            # Return original mentions with data source indicators
            enhanced = []
            for mention in mentions:
                if isinstance(mention, V2Mention):
                    enhanced_mention = EnhancedV2Mention(
                        **mention.model_dump(by_alias=True)
                    )
                elif isinstance(mention, Mention):
                    enhanced_mention = EnhancedMention(
                        **mention.model_dump(by_alias=True)
                    )
                elif isinstance(mention, SimpleMention):
                    enhanced_mention = EnhancedSimpleMention(
                        **mention.model_dump(by_alias=True)
                    )
                else:
                    continue

                enhanced_mention.data_source.twitter_api = False
                enhanced.append(enhanced_mention)
            return enhanced

        # Extract tweet IDs
        tweet_ids = []
        tweet_id_map = {}
        usernames = set()

        for i, mention in enumerate(mentions):
            tweet_id = self._extract_tweet_id(mention)
            if tweet_id:
                tweet_ids.append(tweet_id)
                tweet_id_map[tweet_id] = i

            username = self._extract_username(mention)
            if username:
                usernames.add(username)

        # Fetch tweets in batches
        tweets_data = {}
        users_data = {}

        try:
            # Fetch tweet data
            if tweet_ids:
                # Split into batches of max_batch_size
                for i in range(0, len(tweet_ids), self.config.max_batch_size):
                    batch = tweet_ids[i : i + self.config.max_batch_size]

                    # Check cache first
                    if self._cache:
                        batch_to_fetch = []
                        for tweet_id in batch:
                            if tweet_id in self._cache:
                                tweets_data[tweet_id] = self._cache[tweet_id]
                            else:
                                batch_to_fetch.append(tweet_id)
                        batch = batch_to_fetch

                    if batch:
                        try:
                            tweets = await asyncio.wait_for(
                                self.twitter_client.get_tweets(batch),
                                timeout=self.config.enhancement_timeout,
                            )

                            for tweet in tweets:
                                tweets_data[tweet.id] = tweet
                                if self._cache:
                                    self._cache[tweet.id] = tweet

                        except asyncio.TimeoutError:
                            if self.config.strict_mode:
                                raise
                            # Continue without enhancement for this batch
                        except Exception:
                            if self.config.strict_mode:
                                raise
                            # Continue without enhancement for this batch

            # Fetch user data if needed
            if self.config.include_user_data and usernames:
                for username in usernames:
                    try:
                        user = await asyncio.wait_for(
                            self.twitter_client.get_user_by_username(username),
                            timeout=self.config.enhancement_timeout,
                        )
                        if user:
                            users_data[username] = user
                    except:
                        if self.config.strict_mode:
                            raise
                        # Continue without user enhancement

        except Exception:
            if self.config.strict_mode:
                raise
            # Continue with original data

        # Create enhanced mentions
        enhanced = []
        for i, mention in enumerate(mentions):
            tweet_id = self._extract_tweet_id(mention)
            username = self._extract_username(mention)

            # Create enhanced mention based on type
            if isinstance(mention, V2Mention):
                enhanced_mention = EnhancedV2Mention(
                    **mention.model_dump(by_alias=True)
                )
            elif isinstance(mention, Mention):
                enhanced_mention = EnhancedMention(**mention.model_dump(by_alias=True))
            elif isinstance(mention, SimpleMention):
                enhanced_mention = EnhancedSimpleMention(
                    **mention.model_dump(by_alias=True)
                )
            else:
                continue

            # Add Twitter data if available
            if tweet_id and tweet_id in tweets_data:
                twitter_tweet = tweets_data[tweet_id]
                enhanced_mention.raw_tweet_text = twitter_tweet.text
                enhanced_mention.twitter_metrics = twitter_tweet.public_metrics
                enhanced_mention.context_annotations = twitter_tweet.context_annotations
                enhanced_mention.entities = twitter_tweet.entities
                enhanced_mention.referenced_tweets = twitter_tweet.referenced_tweets
                enhanced_mention.data_source.twitter_api = True

            # Add user data if available
            if username and username in users_data:
                enhanced_mention.twitter_user = users_data[username]

            enhanced_mention.data_source.enhancement_timestamp = str(
                asyncio.get_event_loop().time()
            )
            enhanced.append(enhanced_mention)

        return enhanced

    async def enhance_mentions_response(
        self,
        response: BaseResponse,
    ) -> BaseResponse:
        """
        Enhance a mentions response with Twitter API data

        Args:
            response: Original Elfa API response

        Returns:
            Enhanced response with Twitter data
        """
        if not hasattr(response, "data") or not response.data:
            return response

        # Process mentions in batches
        enhanced_data = []
        mentions = response.data if isinstance(response.data, list) else [response.data]

        for i in range(0, len(mentions), self.config.max_batch_size):
            batch = mentions[i : i + self.config.max_batch_size]
            enhanced_batch = await self._enhance_mentions_batch(batch)
            enhanced_data.extend(enhanced_batch)

        # Create new response with enhanced data
        response_dict = response.model_dump()
        response_dict["data"] = enhanced_data

        # Return enhanced response of the same type
        return type(response)(**response_dict)

    async def close(self):
        """Close the enhancer and underlying Twitter client"""
        await self.twitter_client.close()
