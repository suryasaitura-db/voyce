# Databricks notebook source
# MAGIC %md
# MAGIC # Voice Processing Pipeline
# MAGIC
# MAGIC This notebook handles:
# MAGIC - Audio file processing from Unity Catalog volumes
# MAGIC - Audio feature extraction (MFCC, spectral features)
# MAGIC - Speech-to-text using OpenAI Whisper
# MAGIC - Audio normalization and preprocessing
# MAGIC - Batch processing with cost optimization

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Required Libraries

# COMMAND ----------

# MAGIC %pip install openai-whisper librosa soundfile pydub

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
import os
import uuid

# Audio processing libraries
import whisper
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

# COMMAND ----------

# Configuration
CATALOG_NAME = "voice_feedback_prod"
RAW_DATA_SCHEMA = "raw_data"
PROCESSED_SCHEMA = "processed_data"

# Volume paths (Unity Catalog volumes)
AUDIO_VOLUME_PATH = f"/Volumes/{CATALOG_NAME}/{RAW_DATA_SCHEMA}/audio_files"
PROCESSED_AUDIO_PATH = f"/Volumes/{CATALOG_NAME}/{PROCESSED_SCHEMA}/processed_audio"

# Whisper model configuration
WHISPER_MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large
WHISPER_DEVICE = "cpu"  # Use "cuda" if GPU is available

# Processing batch size
BATCH_SIZE = 100

print(f"Catalog: {CATALOG_NAME}")
print(f"Audio Volume: {AUDIO_VOLUME_PATH}")
print(f"Processed Audio: {PROCESSED_AUDIO_PATH}")
print(f"Whisper Model: {WHISPER_MODEL_SIZE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Whisper Model

# COMMAND ----------

# Load Whisper model once for the entire notebook
print(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
whisper_model = whisper.load_model(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE)
print("✓ Whisper model loaded successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Audio Processing Functions

# COMMAND ----------

def extract_audio_features(audio_path):
    """Extract comprehensive audio features using librosa"""

    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=16000)  # Resample to 16kHz

        # Basic audio properties
        duration = librosa.get_duration(y=y, sr=sr)
        channels = 1 if len(y.shape) == 1 else y.shape[1]

        # Volume/amplitude features
        avg_volume = float(np.mean(np.abs(y)))
        max_volume = float(np.max(np.abs(y)))

        # Silence ratio (frames below threshold)
        silence_threshold = 0.01
        silence_ratio = float(np.sum(np.abs(y) < silence_threshold) / len(y))

        # Zero crossing rate (speech rate indicator)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        speech_rate = float(np.mean(zcr))

        # Pitch (fundamental frequency) using librosa
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = float(np.mean(pitches[pitches > 0])) if len(pitches[pitches > 0]) > 0 else 0.0
        pitch_std = float(np.std(pitches[pitches > 0])) if len(pitches[pitches > 0]) > 0 else 0.0

        # Energy features
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_std = float(np.std(rms))

        # MFCC features (13 coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_features = [float(x) for x in np.mean(mfccs, axis=1)]

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

        spectral_features = [
            float(np.mean(spectral_centroids)),
            float(np.std(spectral_centroids)),
            float(np.mean(spectral_rolloff)),
            float(np.std(spectral_rolloff)),
            float(np.mean(spectral_bandwidth)),
            float(np.std(spectral_bandwidth))
        ]

        return {
            "duration_seconds": float(duration),
            "sample_rate": int(sr),
            "bit_rate": 256000,  # Estimated
            "channels": int(channels),
            "avg_volume": avg_volume,
            "max_volume": max_volume,
            "silence_ratio": silence_ratio,
            "speech_rate": speech_rate,
            "pitch_mean": pitch_mean,
            "pitch_std": pitch_std,
            "energy_mean": energy_mean,
            "energy_std": energy_std,
            "mfcc_features": mfcc_features,
            "spectral_features": spectral_features,
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "duration_seconds": None,
            "sample_rate": None,
            "bit_rate": None,
            "channels": None,
            "avg_volume": None,
            "max_volume": None,
            "silence_ratio": None,
            "speech_rate": None,
            "pitch_mean": None,
            "pitch_std": None,
            "energy_mean": None,
            "energy_std": None,
            "mfcc_features": None,
            "spectral_features": None,
            "success": False,
            "error": str(e)
        }

# COMMAND ----------

def transcribe_audio(audio_path, model):
    """Transcribe audio using Whisper"""

    try:
        start_time = datetime.now()

        # Transcribe
        result = model.transcribe(audio_path, fp16=False)

        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        # Extract text and metadata
        transcription_text = result["text"].strip()
        language = result.get("language", "unknown")

        # Calculate word count
        word_count = len(transcription_text.split()) if transcription_text else 0

        # Estimate confidence (Whisper doesn't provide direct confidence scores)
        # We'll use a heuristic based on detected language confidence
        confidence_score = 0.85  # Default confidence

        return {
            "transcription_text": transcription_text,
            "language_detected": language,
            "word_count": word_count,
            "confidence_score": confidence_score,
            "processing_time_ms": processing_time,
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "transcription_text": None,
            "language_detected": None,
            "word_count": None,
            "confidence_score": None,
            "processing_time_ms": None,
            "success": False,
            "error": str(e)
        }

# COMMAND ----------

def normalize_audio(input_path, output_path, target_sample_rate=16000):
    """Normalize audio file for consistent processing"""

    try:
        # Load audio
        audio = AudioSegment.from_file(input_path)

        # Normalize to -20 dBFS
        normalized_audio = audio.normalize()

        # Convert to mono if stereo
        if normalized_audio.channels > 1:
            normalized_audio = normalized_audio.set_channels(1)

        # Set sample rate
        normalized_audio = normalized_audio.set_frame_rate(target_sample_rate)

        # Export as WAV
        normalized_audio.export(output_path, format="wav")

        return {
            "success": True,
            "output_path": output_path,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "output_path": None,
            "error": str(e)
        }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Pending Voice Feedback Records

# COMMAND ----------

# Get voice feedback records that need processing
pending_feedback_df = spark.sql(f"""
    SELECT
        vf.id as voice_feedback_id,
        vf.organization_id,
        vf.audio_file_path,
        vf.created_at
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.voice_feedback vf
    LEFT JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions t
        ON vf.id = t.voice_feedback_id
    WHERE vf.status = 'pending'
        AND t.id IS NULL
    LIMIT {BATCH_SIZE}
""")

pending_count = pending_feedback_df.count()
print(f"Found {pending_count} voice feedback records pending processing")

# Display sample
display(pending_feedback_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process Audio Files (Batch)

# COMMAND ----------

def process_audio_batch(feedback_records):
    """Process a batch of audio files"""

    results = []
    processing_start = datetime.now()

    for idx, record in enumerate(feedback_records, 1):
        try:
            voice_feedback_id = record["voice_feedback_id"]
            organization_id = record["organization_id"]
            audio_file_path = record["audio_file_path"]

            print(f"\n[{idx}/{len(feedback_records)}] Processing: {voice_feedback_id}")

            # Construct full path
            full_audio_path = f"{AUDIO_VOLUME_PATH}/{audio_file_path}"

            # Check if file exists
            if not os.path.exists(full_audio_path):
                print(f"  ✗ Audio file not found: {full_audio_path}")
                results.append({
                    "voice_feedback_id": voice_feedback_id,
                    "success": False,
                    "error": "Audio file not found"
                })
                continue

            # 1. Extract audio features
            print(f"  - Extracting audio features...")
            audio_features = extract_audio_features(full_audio_path)

            if not audio_features["success"]:
                print(f"  ✗ Feature extraction failed: {audio_features['error']}")
                results.append({
                    "voice_feedback_id": voice_feedback_id,
                    "success": False,
                    "error": f"Feature extraction failed: {audio_features['error']}"
                })
                continue

            # 2. Transcribe audio
            print(f"  - Transcribing audio...")
            transcription = transcribe_audio(full_audio_path, whisper_model)

            if not transcription["success"]:
                print(f"  ✗ Transcription failed: {transcription['error']}")
                results.append({
                    "voice_feedback_id": voice_feedback_id,
                    "success": False,
                    "error": f"Transcription failed: {transcription['error']}"
                })
                continue

            # 3. Save results
            results.append({
                "voice_feedback_id": voice_feedback_id,
                "organization_id": organization_id,
                "audio_features": audio_features,
                "transcription": transcription,
                "success": True,
                "error": None
            })

            print(f"  ✓ Processed successfully")
            print(f"    Duration: {audio_features['duration_seconds']:.2f}s")
            print(f"    Transcription: {transcription['transcription_text'][:100]}...")

        except Exception as e:
            print(f"  ✗ Error processing {voice_feedback_id}: {str(e)}")
            results.append({
                "voice_feedback_id": voice_feedback_id,
                "success": False,
                "error": str(e)
            })

    processing_end = datetime.now()
    processing_duration = (processing_end - processing_start).total_seconds()

    print(f"\n{'='*60}")
    print(f"Batch processing complete!")
    print(f"Total time: {processing_duration:.2f} seconds")
    print(f"Success: {sum(1 for r in results if r['success'])}/{len(results)}")
    print(f"{'='*60}")

    return results

# COMMAND ----------

# Process the batch
if pending_count > 0:
    # Convert to list for processing
    feedback_records = pending_feedback_df.collect()

    # Process batch
    processing_results = process_audio_batch(feedback_records)
else:
    processing_results = []
    print("No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Results to Delta Tables

# COMMAND ----------

if processing_results:
    # Prepare audio features data
    audio_features_data = []
    transcription_data = []

    for result in processing_results:
        if result["success"]:
            # Audio features
            features = result["audio_features"]
            audio_features_data.append({
                "id": str(uuid.uuid4()),
                "voice_feedback_id": result["voice_feedback_id"],
                "organization_id": result["organization_id"],
                "duration_seconds": features["duration_seconds"],
                "sample_rate": features["sample_rate"],
                "bit_rate": features["bit_rate"],
                "channels": features["channels"],
                "avg_volume": features["avg_volume"],
                "max_volume": features["max_volume"],
                "silence_ratio": features["silence_ratio"],
                "speech_rate": features["speech_rate"],
                "pitch_mean": features["pitch_mean"],
                "pitch_std": features["pitch_std"],
                "energy_mean": features["energy_mean"],
                "energy_std": features["energy_std"],
                "mfcc_features": features["mfcc_features"],
                "spectral_features": features["spectral_features"],
                "created_at": datetime.now()
            })

            # Transcription
            trans = result["transcription"]
            transcription_id = str(uuid.uuid4())
            transcription_data.append({
                "id": transcription_id,
                "voice_feedback_id": result["voice_feedback_id"],
                "transcription_text": trans["transcription_text"],
                "transcription_engine": f"whisper-{WHISPER_MODEL_SIZE}",
                "confidence_score": trans["confidence_score"],
                "language_detected": trans["language_detected"],
                "word_count": trans["word_count"],
                "processing_time_ms": trans["processing_time_ms"],
                "error_message": None,
                "created_at": datetime.now()
            })

    # Save audio features
    if audio_features_data:
        audio_features_df = spark.createDataFrame(audio_features_data)
        audio_features_df.write \
            .format("delta") \
            .mode("append") \
            .saveAsTable(f"{CATALOG_NAME}.{PROCESSED_SCHEMA}.audio_features")

        print(f"✓ Saved {len(audio_features_data)} audio feature records")

    # Save transcriptions
    if transcription_data:
        transcription_df = spark.createDataFrame(transcription_data)
        transcription_df.write \
            .format("delta") \
            .mode("append") \
            .saveAsTable(f"{CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions")

        print(f"✓ Saved {len(transcription_data)} transcription records")

    # Update voice_feedback status
    success_ids = [r["voice_feedback_id"] for r in processing_results if r["success"]]
    if success_ids:
        success_ids_str = "', '".join(success_ids)

        spark.sql(f"""
            UPDATE {CATALOG_NAME}.{RAW_DATA_SCHEMA}.voice_feedback
            SET status = 'processed', updated_at = current_timestamp()
            WHERE id IN ('{success_ids_str}')
        """)

        print(f"✓ Updated status for {len(success_ids)} voice feedback records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Enhanced Transcriptions

# COMMAND ----------

# Create enhanced transcriptions with features
spark.sql(f"""
    INSERT INTO {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions
    SELECT
        t.id,
        t.voice_feedback_id,
        vf.organization_id,
        t.transcription_text,
        REGEXP_REPLACE(LOWER(t.transcription_text), '[^a-z0-9\\s]', '') as cleaned_text,
        t.language_detected as language,
        t.word_count,
        SIZE(SPLIT(t.transcription_text, '[.!?]')) as sentence_count,
        AVG(LENGTH(w.word)) as avg_word_length,
        COUNT(DISTINCT w.word) as unique_word_count,
        NULL as sentiment_label,
        NULL as sentiment_score,
        NULL as key_phrases,
        NULL as topics,
        NULL as named_entities,
        NULL as text_embedding,
        current_timestamp() as processing_timestamp,
        current_timestamp() as created_at
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions t
    JOIN {CATALOG_NAME}.{RAW_DATA_SCHEMA}.voice_feedback vf
        ON t.voice_feedback_id = vf.id
    LEFT JOIN {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions et
        ON t.id = et.id
    LATERAL VIEW EXPLODE(SPLIT(LOWER(t.transcription_text), '\\s+')) w as word
    WHERE et.id IS NULL
        AND t.transcription_text IS NOT NULL
    GROUP BY
        t.id,
        t.voice_feedback_id,
        vf.organization_id,
        t.transcription_text,
        t.language_detected,
        t.word_count
""")

print("✓ Created enhanced transcriptions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Tables

# COMMAND ----------

# Optimize processed tables
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{PROCESSED_SCHEMA}.audio_features")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions")
spark.sql(f"OPTIMIZE {CATALOG_NAME}.{PROCESSED_SCHEMA}.enhanced_transcriptions")

print("✓ Optimized tables")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Track Processing Costs

# COMMAND ----------

def track_processing_costs(results, processing_duration):
    """Track processing costs"""

    success_count = sum(1 for r in results if r["success"])

    # Cost estimation
    # Whisper processing: $0.006 per minute
    # Compute: $0.10 per hour
    total_audio_minutes = sum(
        r.get("audio_features", {}).get("duration_seconds", 0) / 60
        for r in results if r["success"]
    )

    whisper_cost = total_audio_minutes * 0.006
    compute_cost = (processing_duration / 3600) * 0.10
    total_cost = whisper_cost + compute_cost

    # Save to cost tracking table
    cost_record = spark.createDataFrame([{
        "id": f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "organization_id": None,
        "resource_type": "voice_processing",
        "resource_id": "batch_processing",
        "operation": f"whisper-{WHISPER_MODEL_SIZE}",
        "quantity": float(success_count),
        "unit_cost": total_cost / success_count if success_count > 0 else 0.0,
        "total_cost": total_cost,
        "currency": "USD",
        "cost_date": datetime.now().date(),
        "metadata": json.dumps({
            "processing_duration_seconds": processing_duration,
            "total_audio_minutes": total_audio_minutes,
            "whisper_cost": whisper_cost,
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

    print(f"\n✓ Tracked processing costs:")
    print(f"  Whisper cost: ${whisper_cost:.4f}")
    print(f"  Compute cost: ${compute_cost:.4f}")
    print(f"  Total cost: ${total_cost:.4f}")
    print(f"  Cost per file: ${total_cost/success_count:.4f}" if success_count > 0 else "  N/A")

# Track costs if results exist
if processing_results:
    track_processing_costs(processing_results, processing_duration)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Processing Statistics

# COMMAND ----------

# Generate statistics
stats_df = spark.sql(f"""
    SELECT
        COUNT(*) as total_transcriptions,
        AVG(t.word_count) as avg_word_count,
        AVG(t.confidence_score) as avg_confidence,
        AVG(t.processing_time_ms) as avg_processing_time_ms,
        COUNT(DISTINCT t.language_detected) as unique_languages,
        AVG(af.duration_seconds) as avg_duration_seconds,
        AVG(af.silence_ratio) as avg_silence_ratio,
        AVG(af.speech_rate) as avg_speech_rate
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions t
    JOIN {CATALOG_NAME}.{PROCESSED_SCHEMA}.audio_features af
        ON t.voice_feedback_id = af.voice_feedback_id
    WHERE t.created_at >= current_date()
""")

print("\nPROCESSING STATISTICS (Today)")
print("="*60)
display(stats_df)

# COMMAND ----------

# Language distribution
language_df = spark.sql(f"""
    SELECT
        language_detected,
        COUNT(*) as count,
        AVG(confidence_score) as avg_confidence
    FROM {CATALOG_NAME}.{RAW_DATA_SCHEMA}.transcriptions
    WHERE created_at >= current_date()
    GROUP BY language_detected
    ORDER BY count DESC
""")

print("\nLANGUAGE DISTRIBUTION")
print("="*60)
display(language_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"""
Voice Processing Complete!

Summary:
--------
✓ Processed {len(processing_results)} audio files
✓ Successful: {sum(1 for r in processing_results if r['success'])}
✓ Failed: {sum(1 for r in processing_results if not r['success'])}

Features Extracted:
-------------------
• Audio duration, sample rate, channels
• Volume and amplitude features
• Silence ratio and speech rate
• Pitch and energy statistics
• MFCC features (13 coefficients)
• Spectral features (centroid, rolloff, bandwidth)

Transcription Engine:
---------------------
• Model: Whisper {WHISPER_MODEL_SIZE}
• Average confidence: {stats_df.collect()[0]['avg_confidence'] if pending_count > 0 else 'N/A'}
• Average processing time: {stats_df.collect()[0]['avg_processing_time_ms'] if pending_count > 0 else 'N/A'} ms

Next Steps:
-----------
1. Run 03_sentiment_analysis.py for sentiment classification
2. Schedule this notebook for continuous processing
3. Monitor processing costs and optimize batch size
4. Consider GPU acceleration for faster processing

Optimization Tips:
------------------
• Use larger batch sizes for better throughput
• Use GPU (WHISPER_DEVICE = "cuda") for 2-3x speedup
• Use smaller Whisper model (tiny) for faster processing
• Pre-filter short/invalid audio files
• Process during off-peak hours for cost savings
""")

# COMMAND ----------
