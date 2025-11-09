"""
Sentiment Analysis Service
Multiple approaches: Claude API, Databricks AutoML, Vector Search
"""
import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    """Sentiment labels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class CategoryL1(str, Enum):
    """Level 1 categories"""
    GOVERNMENT = "Government"
    PRIVATE = "Private"
    PRODUCT = "Product"
    INFRASTRUCTURE = "Infrastructure"
    HEALTH = "Health"
    OTHER = "Other"


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result"""
    submission_id: str
    summary: str
    category_l1: str
    category_l2: Optional[str]
    category_l3: Optional[str]
    sentiment: SentimentLabel
    sentiment_score: float  # -1.0 to 1.0
    sentiment_reasoning: str
    urgency_score: int  # 1-5
    urgency_reasoning: str
    entities_extracted: Dict[str, List[str]]
    keywords: List[str]
    topics: List[str]
    model_used: str
    model_version: str
    processing_time_ms: int
    processing_cost_usd: float
    confidence_score: float
    metadata: Dict[str, Any]


class ClaudeSentimentAnalyzer:
    """Claude API for zero-shot sentiment analysis"""

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
                logger.info("Claude API client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Claude API: {e}")

    async def analyze(self, text: str, submission_id: str) -> SentimentAnalysis:
        """Analyze sentiment using Claude API"""
        if not self.client:
            raise Exception("Claude API client not initialized")

        start_time = time.time()

        try:
            prompt = self._build_prompt(text)

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for more consistent results
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text
            result = self._parse_response(response_text)

            duration_ms = int((time.time() - start_time) * 1000)

            # Calculate cost (Claude Sonnet 4: ~$3 per million input tokens, ~$15 per million output tokens)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_usd = (input_tokens * 0.000003) + (output_tokens * 0.000015)

            return SentimentAnalysis(
                submission_id=submission_id,
                summary=result.get('summary', ''),
                category_l1=result.get('category_l1', CategoryL1.OTHER),
                category_l2=result.get('category_l2'),
                category_l3=result.get('category_l3'),
                sentiment=SentimentLabel(result.get('sentiment', 'neutral')),
                sentiment_score=float(result.get('sentiment_score', 0.0)),
                sentiment_reasoning=result.get('sentiment_reasoning', ''),
                urgency_score=int(result.get('urgency', 3)),
                urgency_reasoning=result.get('urgency_reasoning', ''),
                entities_extracted=result.get('entities', {}),
                keywords=result.get('keywords', []),
                topics=result.get('topics', []),
                model_used=self.model,
                model_version='4.0',
                processing_time_ms=duration_ms,
                processing_cost_usd=cost_usd,
                confidence_score=float(result.get('confidence', 0.9)),
                metadata={
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens
                }
            )

        except Exception as e:
            logger.error(f"Claude sentiment analysis failed: {e}")
            raise

    def _build_prompt(self, text: str) -> str:
        """Build prompt for Claude"""
        return f"""Analyze the following customer feedback and provide a comprehensive assessment.

Feedback text:
"{text}"

Please provide a detailed analysis in JSON format with the following structure:

{{
    "summary": "2-3 sentence summary of the feedback",
    "sentiment": "positive|neutral|negative|mixed",
    "sentiment_score": -1.0 to 1.0 (negative to positive),
    "sentiment_reasoning": "Brief explanation of the sentiment assessment",
    "urgency": 1-5 (1=low urgency, 5=critical),
    "urgency_reasoning": "Why this urgency level was assigned",
    "category_l1": "Government|Private|Product|Infrastructure|Health|Other",
    "category_l2": "Subcategory (e.g., 'Public Transport', 'Customer Service')",
    "category_l3": "Specific issue (e.g., 'Bus Delays', 'Rude Staff')",
    "entities": {{
        "locations": ["list of mentioned locations"],
        "organizations": ["list of mentioned organizations"],
        "people": ["list of mentioned people"],
        "products": ["list of mentioned products/services"]
    }},
    "keywords": ["5-10 relevant keywords"],
    "topics": ["2-5 main topics discussed"],
    "confidence": 0.0 to 1.0 (confidence in this analysis)
}}

Provide only the JSON output, no additional text."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude response to extract JSON"""
        try:
            # Try to extract JSON from markdown code blocks
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Return default structure
            return {
                'summary': response_text[:200],
                'sentiment': 'neutral',
                'sentiment_score': 0.0,
                'sentiment_reasoning': 'Parse error',
                'urgency': 3,
                'urgency_reasoning': 'Default',
                'category_l1': CategoryL1.OTHER,
                'entities': {},
                'keywords': [],
                'topics': [],
                'confidence': 0.5
            }


class DatabricksVectorSearchAnalyzer:
    """Databricks Vector Search for similarity-based sentiment"""

    def __init__(self):
        self.host = os.getenv('DATABRICKS_HOST')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'voice_feedback_prod')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'ml_models')
        self.client = None

        if self.host and self.token:
            try:
                from databricks.vector_search.client import VectorSearchClient
                self.client = VectorSearchClient(
                    workspace_url=self.host,
                    personal_access_token=self.token
                )
                logger.info("Databricks Vector Search client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Vector Search: {e}")

    async def analyze(self, text: str, submission_id: str) -> SentimentAnalysis:
        """Analyze sentiment using vector search"""
        if not self.client:
            raise Exception("Vector Search client not initialized")

        start_time = time.time()

        try:
            index_name = f"{self.catalog}.{self.schema}.sentiment_vectors"

            # Search for similar feedback
            results = self.client.get_index(
                index_name=index_name
            ).similarity_search(
                query_text=text,
                columns=["submission_id", "sentiment", "category_l1", "summary", "keywords"],
                num_results=10
            )

            # Aggregate results to determine sentiment
            sentiment_counts = {}
            category_counts = {}
            all_keywords = []

            for result in results.get('result', {}).get('data_array', []):
                sentiment = result[1]  # sentiment column
                category = result[2]   # category_l1 column
                keywords = result[4]   # keywords column

                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1

                if keywords:
                    all_keywords.extend(keywords)

            # Determine most common sentiment and category
            sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else 'neutral'
            category_l1 = max(category_counts, key=category_counts.get) if category_counts else CategoryL1.OTHER

            # Simple sentiment score based on distribution
            total = sum(sentiment_counts.values())
            positive_ratio = sentiment_counts.get('positive', 0) / total if total > 0 else 0
            negative_ratio = sentiment_counts.get('negative', 0) / total if total > 0 else 0
            sentiment_score = positive_ratio - negative_ratio

            # Extract top keywords
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            top_keywords = [k for k, _ in keyword_counts.most_common(10)]

            duration_ms = int((time.time() - start_time) * 1000)

            return SentimentAnalysis(
                submission_id=submission_id,
                summary=f"Similar feedback analysis based on {len(results.get('result', {}).get('data_array', []))} matches",
                category_l1=category_l1,
                category_l2=None,
                category_l3=None,
                sentiment=SentimentLabel(sentiment),
                sentiment_score=sentiment_score,
                sentiment_reasoning=f"Based on {total} similar feedback items",
                urgency_score=3,
                urgency_reasoning="Average urgency from similar items",
                entities_extracted={},
                keywords=top_keywords,
                topics=[],
                model_used="vector_search",
                model_version="1.0",
                processing_time_ms=duration_ms,
                processing_cost_usd=0.001,  # Minimal cost for vector search
                confidence_score=0.85,
                metadata={
                    'similar_items': len(results.get('result', {}).get('data_array', [])),
                    'sentiment_distribution': sentiment_counts
                }
            )

        except Exception as e:
            logger.error(f"Vector search analysis failed: {e}")
            raise


class DatabricksAutoMLAnalyzer:
    """Databricks AutoML model for sentiment classification"""

    def __init__(self):
        self.host = os.getenv('DATABRICKS_HOST')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.model_name = "sentiment_classifier_v1"
        self.client = None

        if self.host and self.token:
            try:
                from databricks.sdk import WorkspaceClient
                self.client = WorkspaceClient(
                    host=self.host,
                    token=self.token
                )
                logger.info("Databricks Workspace client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Databricks client: {e}")

    async def analyze(self, text: str, submission_id: str) -> SentimentAnalysis:
        """Analyze sentiment using AutoML model"""
        if not self.client:
            raise Exception("Databricks client not initialized")

        start_time = time.time()

        try:
            import mlflow
            mlflow.set_tracking_uri(f"{self.host}")

            # Load model
            model = mlflow.pyfunc.load_model(f"models:/{self.model_name}/Production")

            # Prepare input
            import pandas as pd
            input_df = pd.DataFrame({'text': [text]})

            # Predict
            predictions = model.predict(input_df)

            # Parse prediction (assuming it returns sentiment label and probability)
            if isinstance(predictions, pd.DataFrame):
                sentiment = predictions.iloc[0]['sentiment']
                confidence = predictions.iloc[0].get('confidence', 0.9)
            else:
                sentiment = str(predictions[0])
                confidence = 0.9

            # Map sentiment to score
            sentiment_map = {
                'positive': 0.8,
                'neutral': 0.0,
                'negative': -0.8,
                'mixed': 0.0
            }
            sentiment_score = sentiment_map.get(sentiment, 0.0)

            duration_ms = int((time.time() - start_time) * 1000)

            return SentimentAnalysis(
                submission_id=submission_id,
                summary="AutoML sentiment classification",
                category_l1=CategoryL1.OTHER,  # AutoML model doesn't predict category
                category_l2=None,
                category_l3=None,
                sentiment=SentimentLabel(sentiment),
                sentiment_score=sentiment_score,
                sentiment_reasoning=f"AutoML model prediction with {confidence:.2f} confidence",
                urgency_score=3,
                urgency_reasoning="Default urgency",
                entities_extracted={},
                keywords=[],
                topics=[],
                model_used="automl",
                model_version=self.model_name,
                processing_time_ms=duration_ms,
                processing_cost_usd=0.002,  # Minimal cost for model inference
                confidence_score=confidence,
                metadata={'model_name': self.model_name}
            )

        except Exception as e:
            logger.error(f"AutoML analysis failed: {e}")
            raise


class SentimentAnalyzer:
    """
    Main sentiment analyzer with multiple approaches
    """

    def __init__(self, primary_method: str = 'claude'):
        """
        Initialize sentiment analyzer

        Args:
            primary_method: 'claude', 'vector_search', or 'automl'
        """
        self.primary_method = primary_method

        # Initialize analyzers
        self.analyzers = {
            'claude': ClaudeSentimentAnalyzer(),
            'vector_search': DatabricksVectorSearchAnalyzer(),
            'automl': DatabricksAutoMLAnalyzer()
        }

        logger.info(f"SentimentAnalyzer initialized with primary method: {primary_method}")

    async def analyze(
        self,
        text: str,
        submission_id: str,
        fallback: bool = True
    ) -> SentimentAnalysis:
        """
        Analyze sentiment with optional fallback

        Args:
            text: Text to analyze
            submission_id: Submission ID
            fallback: Whether to try fallback methods if primary fails

        Returns:
            SentimentAnalysis
        """
        # Try primary method
        try:
            analyzer = self.analyzers[self.primary_method]
            result = await analyzer.analyze(text, submission_id)
            logger.info(f"Sentiment analysis successful with {self.primary_method}")
            return result

        except Exception as e:
            logger.error(f"Primary method {self.primary_method} failed: {e}")

            if not fallback:
                raise

            # Try fallback methods
            for method_name, analyzer in self.analyzers.items():
                if method_name == self.primary_method:
                    continue

                try:
                    logger.info(f"Trying fallback method: {method_name}")
                    result = await analyzer.analyze(text, submission_id)
                    logger.info(f"Sentiment analysis successful with fallback {method_name}")
                    return result

                except Exception as e2:
                    logger.error(f"Fallback method {method_name} failed: {e2}")
                    continue

            # All methods failed
            raise Exception("All sentiment analysis methods failed")

    async def batch_analyze(
        self,
        texts: List[tuple],  # List of (text, submission_id) tuples
        max_concurrent: int = 5
    ) -> List[SentimentAnalysis]:
        """
        Analyze multiple texts concurrently

        Args:
            texts: List of (text, submission_id) tuples
            max_concurrent: Maximum concurrent analyses

        Returns:
            List of SentimentAnalysis
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(text, sub_id):
            async with semaphore:
                return await self.analyze(text, sub_id)

        tasks = [analyze_with_semaphore(text, sub_id) for text, sub_id in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful = [r for r in results if isinstance(r, SentimentAnalysis)]
        failed = [r for r in results if isinstance(r, Exception)]

        logger.info(f"Batch analysis: {len(successful)} successful, {len(failed)} failed")

        return successful

    async def compare_methods(
        self,
        text: str,
        submission_id: str
    ) -> Dict[str, SentimentAnalysis]:
        """
        Run all available methods and compare results

        Useful for A/B testing and model evaluation

        Args:
            text: Text to analyze
            submission_id: Submission ID

        Returns:
            Dict mapping method name to SentimentAnalysis
        """
        results = {}

        for method_name, analyzer in self.analyzers.items():
            try:
                result = await analyzer.analyze(text, submission_id)
                results[method_name] = result
            except Exception as e:
                logger.error(f"Method {method_name} failed in comparison: {e}")
                results[method_name] = None

        return results
