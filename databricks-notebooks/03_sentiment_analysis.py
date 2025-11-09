# Databricks notebook source
# MAGIC %md
# MAGIC # Sentiment Analysis and ML Pipeline
# MAGIC
# MAGIC This notebook handles:
# MAGIC - Sentiment analysis using Claude API
# MAGIC - AutoML for sentiment classification
# MAGIC - Vector embeddings for semantic search
# MAGIC - Topic extraction and key phrase detection
# MAGIC - Batch inference optimization

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Required Libraries

# COMMAND ----------

# MAGIC %pip install anthropic openai sentence-transformers

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration and Imports

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable
import json
from datetime import datetime
import uuid
import os

# ML libraries
import anthropic
import openai
from sentence_transformers import SentenceTransformer

# COMMAND ----------

# Configuration
CATALOG_NAME = "voice_feedback_prod"
RAW_DATA_SCHEMA = "raw_data"
PROCESSED_SCHEMA = "processed_data"
ML_SCHEMA = "ml_models"

# API Keys (use Databricks secrets)
ANTHROPIC_API_KEY = dbutils.secrets.get(scope="voice-feedback", key="anthropic-api-key")
OPENAI_API_KEY = dbutils.secrets.get(scope="voice-feedback", key="openai-api-key")

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
openai.api_key = OPENAI_API_KEY

# Batch processing
BATCH_SIZE = 50

print(f"Catalog: {CATALOG_NAME}")
print("✓ API clients initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Embedding Model

# COMMAND ----------

# Load sentence transformer for embeddings
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Embedding model loaded")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sentiment Analysis Functions

# COMMAND ----------

def analyze_sentiment_claude(text):
    """Analyze sentiment using Claude API"""

    try:
        start_time = datetime.now()

        prompt = f"""Analyze the sentiment of the following customer feedback.

Provide your analysis in JSON format with these fields:
- sentiment_label: "positive", "negative", or "neutral"
- sentiment_score: a number between -1 (very negative) and 1 (very positive)
- confidence: a number between 0 and 1
- emotions: list of detected emotions (e.g., ["happy", "satisfied", "frustrated"])
- key_phrases: list of important phrases (up to 5)
- topics: list of main topics discussed (up to 5)
- summary: brief 1-sentence summary

Feedback text:
{text}

Respond with only valid JSON, no additional text."""

        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        response_text = response.content[0].text
        result = json.loads(response_text)

        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        return {
            "sentiment_label": result.get("sentiment_label", "neutral"),
            "sentiment_score": float(result.get("sentiment_score", 0.0)),
            "confidence": float(result.get("confidence", 0.0)),
            "emotions": result.get("emotions", []),
            "key_phrases": result.get("key_phrases", []),
            "topics": result.get("topics", []),
            "summary": result.get("summary", ""),
            "processing_time_ms": processing_time,
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "sentiment_label": None,
            "sentiment_score": None,
            "confidence": None,
            "emotions": None,
            "key_phrases": None,
            "topics": None,
            "summary": None,
            "processing_time_ms": None,
            "success": False,
            "error": str(e)
        }

# COMMAND ----------

def generate_embeddings(text):
    """Generate text embeddings using sentence-transformers"""

    try:
        # Generate embedding
        embedding = embedding_model.encode(text, convert_to_numpy=True)

        return {
            "embedding": embedding.tolist(),
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "embedding": None,
            "success": False,
            "error": str(e)
        }

# COMMAND ----------

def analyze_sentiment_openai(text):
    """Alternative: Analyze sentiment using OpenAI"""

    try:
        start_time = datetime.now()

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analysis expert. Analyze customer feedback and return JSON with sentiment_label (positive/negative/neutral), sentiment_score (-1 to 1), confidence (0-1), emotions, key_phrases, and topics."
                },
                {
                    "role": "user",
                    "content": f"Analyze this feedback:\n\n{text}"
                }
            ],
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)

        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        return {
            "sentiment_label": result.get("sentiment_label", "neutral"),
            "sentiment_score": float(result.get("sentiment_score", 0.0)),
            "confidence": float(result.get("confidence", 0.0)),
            "emotions": result.get("emotions", []),
            "key_phrases": result.get("key_phrases", []),
            "topics": result.get("topics", []),
            "processing_time_ms": processing_time,
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "sentiment_label": None,
            "sentiment_score": None,
            "confidence": None,
            "emotions": None,
            "key_phrases": None,
            "topics": None,
            "processing_time_ms": None,
            "success": False,
            "error": str(e)
        }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Transcriptions Pending Sentiment Analysis

# COMMAND ----------

# Get transcriptions without sentiment analysis
pending_transcriptions_df = spark.sql(f"""
    SELECT
        t.id as transcription_id,
        t.voice_feedback_id,
        vf.organization_id,
        t.transcription_text,
        t.created_at
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions t
    JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.voice_feedback vf
        ON t.voice_feedback_id = vf.id
    LEFT JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis sa
        ON t.id = sa.transcription_id
    WHERE t.transcription_text IS NOT NULL
        AND sa.id IS NULL
    LIMIT {BATCH_SIZE}
""")

pending_count = pending_transcriptions_df.count()
print(f"Found {pending_count} transcriptions pending sentiment analysis")

# Display sample
display(pending_transcriptions_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process Sentiment Analysis (Batch)

# COMMAND ----------

def process_sentiment_batch(transcription_records, use_claude=True):
    """Process sentiment analysis for a batch of transcriptions"""

    results = []
    processing_start = datetime.now()

    for idx, record in enumerate(transcription_records, 1):
        try:
            transcription_id = record["transcription_id"]
            voice_feedback_id = record["voice_feedback_id"]
            organization_id = record["organization_id"]
            text = record["transcription_text"]

            print(f"\n[{idx}/{len(transcription_records)}] Analyzing: {transcription_id}")
            print(f"  Text preview: {text[:100]}...")

            # 1. Sentiment analysis
            print(f"  - Running sentiment analysis...")
            if use_claude:
                sentiment = analyze_sentiment_claude(text)
            else:
                sentiment = analyze_sentiment_openai(text)

            if not sentiment["success"]:
                print(f"  ✗ Sentiment analysis failed: {sentiment['error']}")
                results.append({
                    "transcription_id": transcription_id,
                    "success": False,
                    "error": f"Sentiment analysis failed: {sentiment['error']}"
                })
                continue

            # 2. Generate embeddings
            print(f"  - Generating embeddings...")
            embeddings = generate_embeddings(text)

            if not embeddings["success"]:
                print(f"  ⚠ Embedding generation failed: {embeddings['error']}")
                embedding_vector = None
            else:
                embedding_vector = embeddings["embedding"]

            # 3. Save results
            results.append({
                "transcription_id": transcription_id,
                "voice_feedback_id": voice_feedback_id,
                "organization_id": organization_id,
                "sentiment": sentiment,
                "embedding": embedding_vector,
                "success": True,
                "error": None
            })

            print(f"  ✓ Analysis complete")
            print(f"    Sentiment: {sentiment['sentiment_label']} ({sentiment['sentiment_score']:.2f})")
            print(f"    Confidence: {sentiment['confidence']:.2f}")
            print(f"    Topics: {', '.join(sentiment['topics'][:3]) if sentiment['topics'] else 'None'}")

        except Exception as e:
            print(f"  ✗ Error analyzing {transcription_id}: {str(e)}")
            results.append({
                "transcription_id": transcription_id,
                "success": False,
                "error": str(e)
            })

    processing_end = datetime.now()
    processing_duration = (processing_end - processing_start).total_seconds()

    print(f"\n{'='*60}")
    print(f"Batch sentiment analysis complete!")
    print(f"Total time: {processing_duration:.2f} seconds")
    print(f"Success: {sum(1 for r in results if r['success'])}/{len(results)}")
    print(f"{'='*60}")

    return results, processing_duration

# COMMAND ----------

# Process the batch
if pending_count > 0:
    # Convert to list for processing
    transcription_records = pending_transcriptions_df.collect()

    # Process batch (use Claude by default)
    sentiment_results, processing_duration = process_sentiment_batch(
        transcription_records,
        use_claude=True
    )
else:
    sentiment_results = []
    processing_duration = 0
    print("No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Results to Delta Tables

# COMMAND ----------

if sentiment_results:
    # Prepare sentiment analysis data
    sentiment_data = []
    enhanced_transcription_updates = []

    for result in sentiment_results:
        if result["success"]:
            sentiment = result["sentiment"]

            # Sentiment analysis record
            sentiment_data.append({
                "id": str(uuid.uuid4()),
                "transcription_id": result["transcription_id"],
                "voice_feedback_id": result["voice_feedback_id"],
                "sentiment_label": sentiment["sentiment_label"],
                "sentiment_score": sentiment["sentiment_score"],
                "sentiment_confidence": sentiment["confidence"],
                "emotions": json.dumps(sentiment["emotions"]) if sentiment["emotions"] else None,
                "key_phrases": json.dumps(sentiment["key_phrases"]) if sentiment["key_phrases"] else None,
                "topics": json.dumps(sentiment["topics"]) if sentiment["topics"] else None,
                "model_used": "claude-3-5-sonnet",
                "model_version": "20241022",
                "processing_time_ms": sentiment["processing_time_ms"],
                "created_at": datetime.now()
            })

            # Enhanced transcription update
            enhanced_transcription_updates.append({
                "id": result["transcription_id"],
                "sentiment_label": sentiment["sentiment_label"],
                "sentiment_score": sentiment["sentiment_score"],
                "key_phrases": sentiment["key_phrases"],
                "topics": sentiment["topics"],
                "text_embedding": result["embedding"]
            })

    # Save sentiment analysis
    if sentiment_data:
        sentiment_df = spark.createDataFrame(sentiment_data)
        sentiment_df.write \
            .format("delta") \
            .mode("append") \
            .saveAsTable(f"{CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis")

        print(f"✓ Saved {len(sentiment_data)} sentiment analysis records")

    # Update enhanced transcriptions
    if enhanced_transcription_updates:
        for update in enhanced_transcription_updates:
            spark.sql(f"""
                UPDATE {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions
                SET
                    sentiment_label = '{update['sentiment_label']}',
                    sentiment_score = {update['sentiment_score']},
                    key_phrases = array({', '.join([f"'{phrase}'" for phrase in update['key_phrases']]) if update['key_phrases'] else ''}),
                    topics = array({', '.join([f"'{topic}'" for topic in update['topics']]) if update['topics'] else ''}),
                    text_embedding = array({', '.join([str(x) for x in update['text_embedding']]) if update['text_embedding'] else ''})
                WHERE id = '{update['id']}'
            """)

        print(f"✓ Updated {len(enhanced_transcription_updates)} enhanced transcription records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Auto-Tag Feedback Based on Topics

# COMMAND ----------

# Extract unique topics and create tags
if sentiment_results:
    # Get all topics from results
    all_topics = []
    for result in sentiment_results:
        if result["success"] and result["sentiment"]["topics"]:
            all_topics.extend(result["sentiment"]["topics"])

    # Get unique topics
    unique_topics = list(set(all_topics))

    print(f"Found {len(unique_topics)} unique topics")

    # Create tags for new topics
    for topic in unique_topics:
        # Check if tag exists
        existing_tag = spark.sql(f"""
            SELECT id FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.tags
            WHERE LOWER(name) = LOWER('{topic}')
        """).collect()

        if not existing_tag:
            # Create new tag
            tag_record = spark.createDataFrame([{
                "id": str(uuid.uuid4()),
                "name": topic,
                "category": "auto_generated",
                "description": f"Auto-generated tag from sentiment analysis: {topic}",
                "created_at": datetime.now()
            }])

            tag_record.write \
                .format("delta") \
                .mode("append") \
                .saveAsTable(f"{CATALOG_NAME}.{RAW_DATA_SCHEMA}.tags")

            print(f"  ✓ Created tag: {topic}")

    # Assign tags to feedback
    for result in sentiment_results:
        if result["success"] and result["sentiment"]["topics"]:
            voice_feedback_id = result["voice_feedback_id"]

            for topic in result["sentiment"]["topics"]:
                # Get tag ID
                tag_id_result = spark.sql(f"""
                    SELECT id FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.tags
                    WHERE LOWER(name) = LOWER('{topic}')
                """).collect()

                if tag_id_result:
                    tag_id = tag_id_result[0]["id"]

                    # Check if assignment exists
                    existing_assignment = spark.sql(f"""
                        SELECT id FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.feedback_tags
                        WHERE voice_feedback_id = '{voice_feedback_id}'
                            AND tag_id = '{tag_id}'
                    """).collect()

                    if not existing_assignment:
                        # Create assignment
                        assignment = spark.createDataFrame([{
                            "id": str(uuid.uuid4()),
                            "voice_feedback_id": voice_feedback_id,
                            "tag_id": tag_id,
                            "assigned_by": "auto_sentiment_analysis",
                            "confidence_score": result["sentiment"]["confidence"],
                            "created_at": datetime.now()
                        }])

                        assignment.write \
                            .format("delta") \
                            .mode("append") \
                            .saveAsTable(f"{CATALOG_NAME}.{RAW_DATA_SCHEMA}.feedback_tags")

    print("✓ Auto-tagged feedback with topics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Vector Search Index (Optional)

# COMMAND ----------

# Note: This requires Databricks Vector Search to be enabled
# Uncomment to create vector search index

# from databricks.vector_search.client import VectorSearchClient

# vsc = VectorSearchClient()

# # Create vector search endpoint
# vsc.create_endpoint(
#     name="voice-feedback-endpoint",
#     endpoint_type="STANDARD"
# )

# # Create vector search index
# vsc.create_delta_sync_index(
#     endpoint_name="voice-feedback-endpoint",
#     index_name=f"{CATALOG_NAME}.{PROCESSED_SCHEMA}.transcription_embeddings_index",
#     source_table_name=f"{CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions",
#     pipeline_type="TRIGGERED",
#     primary_key="id",
#     embedding_dimension=384,  # all-MiniLM-L6-v2 produces 384-dim embeddings
#     embedding_vector_column="text_embedding"
# )

# print("✓ Created vector search index")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Tables

# COMMAND ----------

# Optimize tables
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{RAW_DATA_SCHEMA}.tags")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{RAW_DATA_SCHEMA}.feedback_tags")

print("✓ Optimized tables")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Track API Costs

# COMMAND ----------

def track_api_costs(results, processing_duration):
    """Track API usage costs"""

    success_count = sum(1 for r in results if r["success"])

    # Cost estimation
    # Claude API: ~$0.003 per request (Sonnet 3.5)
    # OpenAI Embeddings: ~$0.0001 per request
    # Compute: $0.10 per hour

    claude_requests = success_count
    embedding_requests = success_count

    claude_cost = claude_requests * 0.003
    embedding_cost = embedding_requests * 0.0001
    compute_cost = (processing_duration / 3600) * 0.10
    total_cost = claude_cost + embedding_cost + compute_cost

    # Save to cost tracking table
    cost_record = spark.createDataFrame([{
        "id": f"sent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "organization_id": None,
        "resource_type": "sentiment_analysis",
        "resource_id": "batch_processing",
        "operation": "claude_api_sentiment",
        "quantity": float(success_count),
        "unit_cost": total_cost / success_count if success_count > 0 else 0.0,
        "total_cost": total_cost,
        "currency": "USD",
        "cost_date": datetime.now().date(),
        "metadata": json.dumps({
            "processing_duration_seconds": processing_duration,
            "claude_requests": claude_requests,
            "embedding_requests": embedding_requests,
            "claude_cost": claude_cost,
            "embedding_cost": embedding_cost,
            "compute_cost": compute_cost,
            "success_count": success_count,
            "total_count": len(results)
        }),
        "created_at": datetime.now()
    }])

    cost_record.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable(f"{CATALOG_NAME}.analytics.cost_tracking")

    print(f"\n✓ Tracked API costs:")
    print(f"  Claude API cost: ${claude_cost:.4f}")
    print(f"  Embedding cost: ${embedding_cost:.4f}")
    print(f"  Compute cost: ${compute_cost:.4f}")
    print(f"  Total cost: ${total_cost:.4f}")
    print(f"  Cost per analysis: ${total_cost/success_count:.4f}" if success_count > 0 else "  N/A")

# Track costs if results exist
if sentiment_results:
    track_api_costs(sentiment_results, processing_duration)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sentiment Statistics

# COMMAND ----------

# Generate sentiment statistics
sentiment_stats_df = spark.sql(f"""
    SELECT
        sentiment_label,
        COUNT(*) as count,
        AVG(sentiment_score) as avg_score,
        AVG(sentiment_confidence) as avg_confidence,
        AVG(processing_time_ms) as avg_processing_time_ms
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis
    WHERE created_at >= current_date()
    GROUP BY sentiment_label
    ORDER BY count DESC
""")

print("\nSENTIMENT DISTRIBUTION (Today)")
print("="*60)
display(sentiment_stats_df)

# COMMAND ----------

# Top topics
top_topics_df = spark.sql(f"""
    SELECT
        EXPLODE(FROM_JSON(topics, 'array<string>')) as topic,
        COUNT(*) as count
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis
    WHERE created_at >= current_date()
        AND topics IS NOT NULL
    GROUP BY topic
    ORDER BY count DESC
    LIMIT 20
""")

print("\nTOP TOPICS (Today)")
print("="*60)
display(top_topics_df)

# COMMAND ----------

# Emotion analysis
emotions_df = spark.sql(f"""
    SELECT
        EXPLODE(FROM_JSON(emotions, 'array<string>')) as emotion,
        COUNT(*) as count
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.sentiment_analysis
    WHERE created_at >= current_date()
        AND emotions IS NOT NULL
    GROUP BY emotion
    ORDER BY count DESC
    LIMIT 15
""")

print("\nTOP EMOTIONS (Today)")
print("="*60)
display(emotions_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"""
Sentiment Analysis Complete!

Summary:
--------
✓ Processed {len(sentiment_results)} transcriptions
✓ Successful: {sum(1 for r in sentiment_results if r['success'])}
✓ Failed: {sum(1 for r in sentiment_results if not r['success'])}

Features:
---------
• Sentiment classification (positive/negative/neutral)
• Sentiment scoring (-1 to 1)
• Emotion detection
• Key phrase extraction
• Topic identification
• Text embeddings (384-dimensional vectors)

Models Used:
------------
• Claude 3.5 Sonnet for sentiment analysis
• all-MiniLM-L6-v2 for embeddings

Results:
--------
• Auto-generated tags from topics
• Auto-assigned tags to feedback
• Updated enhanced transcriptions
• Ready for vector search

Next Steps:
-----------
1. Run 04_analytics_queries.sql for business insights
2. Run 05_model_training.py to train custom models
3. Set up Vector Search for semantic similarity
4. Schedule this notebook for continuous processing
5. Create dashboards using sentiment data

Cost Optimization:
------------------
• Batch processing reduces API overhead
• Use smaller models for lower costs
• Cache embeddings to avoid recomputation
• Consider fine-tuned models for better accuracy
• Monitor API usage and set budgets

Vector Search Setup:
--------------------
To enable semantic search:
1. Enable Databricks Vector Search
2. Create endpoint and index (see commented code)
3. Query similar feedback using embeddings
4. Build recommendation systems
""")

# COMMAND ----------
