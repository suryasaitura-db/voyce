# ML/AI Pipeline Documentation

Machine Learning and AI pipeline documentation for the Voyce Voice Feedback Platform.

## Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Speech-to-Text (Transcription)](#speech-to-text-transcription)
- [Sentiment Analysis](#sentiment-analysis)
- [Intent Classification](#intent-classification)
- [Entity Extraction](#entity-extraction)
- [Model Training](#model-training)
- [Model Deployment](#model-deployment)
- [Performance Optimization](#performance-optimization)
- [Monitoring and Evaluation](#monitoring-and-evaluation)

## Overview

### ML Components

The Voyce platform uses several ML/AI models for voice feedback processing:

1. **Speech-to-Text**: Convert audio to text (Whisper, AssemblyAI)
2. **Sentiment Analysis**: Detect sentiment and emotions
3. **Intent Classification**: Identify user intent
4. **Entity Extraction**: Extract key entities and topics
5. **Summarization**: Generate concise summaries

### Technology Stack

- **ML Framework**: PyTorch, HuggingFace Transformers
- **Speech-to-Text**: OpenAI Whisper, AssemblyAI
- **NLP Models**: BERT, RoBERTa, GPT-4
- **Orchestration**: Databricks MLflow
- **Serving**: FastAPI, TorchServe
- **Monitoring**: MLflow, Prometheus

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ML/AI PROCESSING PIPELINE                      │
└─────────────────────────────────────────────────────────────────────┘

Audio File Upload
      │
      ▼
┌──────────────────────┐
│  Audio Validation    │
│  - Format check      │
│  - Duration check    │
│  - Quality check     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Audio Preprocessing │
│  - Normalize         │
│  - Denoise           │
│  - Resample          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Speech-to-Text      │
│  Model: Whisper      │
│  Output: Text +      │
│          Timestamps  │
└──────────┬───────────┘
           │
           ├──────────────────────────────┐
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Sentiment Analysis  │      │  Entity Extraction   │
│  Model: RoBERTa      │      │  Model: NER          │
│  Output: Sentiment,  │      │  Output: Entities,   │
│          Emotions    │      │          Keywords    │
└──────────┬───────────┘      └──────────┬───────────┘
           │                              │
           └──────────────┬───────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │ Intent Classification│
                │ Model: Text Classifier│
                │ Output: Intent,      │
                │         Categories   │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  Summarization       │
                │  Model: GPT-4        │
                │  Output: Summary,    │
                │          Key Points, │
                │          Action Items│
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  Store Results       │
                │  - Transcription DB  │
                │  - Analysis DB       │
                │  - Vector Store      │
                └──────────────────────┘
```

## Speech-to-Text (Transcription)

### Whisper Model

**Model Selection:**
```python
# Available models: tiny, base, small, medium, large, large-v2, large-v3
# Trade-off: accuracy vs speed vs cost

WHISPER_MODELS = {
    "tiny": {
        "size": "39 MB",
        "speed": "~32x realtime",
        "accuracy": "Good for simple audio"
    },
    "base": {
        "size": "74 MB",
        "speed": "~16x realtime",
        "accuracy": "Better accuracy"
    },
    "large-v3": {
        "size": "2.9 GB",
        "speed": "~2x realtime",
        "accuracy": "Highest accuracy"
    }
}

# Production configuration
PRODUCTION_MODEL = "whisper-large-v3"
```

### Transcription Implementation

```python
import whisper
import torch

class WhisperTranscriber:
    def __init__(self, model_name="large-v3"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(model_name, device=self.device)

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio file with word-level timestamps"""
        result = self.model.transcribe(
            audio_path,
            language="en",  # Or auto-detect
            task="transcribe",
            word_timestamps=True,
            temperature=0.0,  # Deterministic output
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        return {
            "text": result["text"],
            "language": result["language"],
            "segments": [
                {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "confidence": self._calculate_confidence(segment)
                }
                for segment in result["segments"]
            ],
            "words": self._extract_words(result)
        }

    def _calculate_confidence(self, segment) -> float:
        """Calculate confidence score from logprobs"""
        if "avg_logprob" in segment:
            # Convert log probability to confidence (0-1)
            return min(1.0, max(0.0, 1 + segment["avg_logprob"]))
        return 0.9  # Default confidence

    def _extract_words(self, result) -> list:
        """Extract word-level timestamps"""
        words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                words.append({
                    "word": word["word"].strip(),
                    "start": word["start"],
                    "end": word["end"],
                    "confidence": word.get("probability", 0.9)
                })
        return words
```

### Audio Preprocessing

```python
from pydub import AudioSegment
from pydub.effects import normalize
import noisereduce as nr
import librosa
import soundfile as sf

class AudioPreprocessor:
    def preprocess(self, input_path: str, output_path: str):
        """Preprocess audio for better transcription"""
        # Load audio
        audio, sr = librosa.load(input_path, sr=16000)

        # Noise reduction
        audio = nr.reduce_noise(y=audio, sr=sr)

        # Normalize volume
        audio = librosa.util.normalize(audio)

        # Save preprocessed audio
        sf.write(output_path, audio, sr)

        return output_path
```

## Sentiment Analysis

### Model Selection

**Using Pre-trained Models:**
```python
from transformers import pipeline

# Option 1: DistilBERT (Fast, lightweight)
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

# Option 2: RoBERTa (More accurate)
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

# Option 3: Custom fine-tuned model
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="voyce/sentiment-classifier-v1"
)
```

### Sentiment Analysis Implementation

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class SentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def analyze(self, text: str) -> dict:
        """Analyze sentiment of text"""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # Extract results
        scores = probabilities[0].cpu().numpy()

        # Map to sentiment labels
        sentiment_mapping = {
            0: "negative",
            1: "neutral",
            2: "positive"
        }

        predicted_class = scores.argmax()
        sentiment = sentiment_mapping[predicted_class]

        # Calculate sentiment score (-1 to 1)
        sentiment_score = (scores[2] - scores[0])  # positive - negative

        return {
            "sentiment": sentiment,
            "sentiment_score": float(sentiment_score),
            "sentiment_confidence": float(scores[predicted_class]),
            "sentiment_breakdown": {
                "positive": float(scores[2]),
                "neutral": float(scores[1]),
                "negative": float(scores[0])
            }
        }

    def analyze_emotions(self, text: str) -> dict:
        """Detect emotions using emotion model"""
        emotion_analyzer = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )

        results = emotion_analyzer(text)[0]

        emotions = {
            result["label"]: result["score"]
            for result in results
        }

        dominant_emotion = max(emotions.items(), key=lambda x: x[1])

        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion[0],
            "emotion_confidence": dominant_emotion[1]
        }
```

## Intent Classification

### Custom Intent Classifier

```python
from transformers import pipeline

class IntentClassifier:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

        self.intent_labels = [
            "feedback",
            "complaint",
            "suggestion",
            "question",
            "bug_report",
            "feature_request",
            "appreciation",
            "other"
        ]

    def classify(self, text: str) -> dict:
        """Classify user intent"""
        result = self.classifier(
            text,
            candidate_labels=self.intent_labels,
            multi_label=True
        )

        # Primary intent
        primary_intent = result["labels"][0]
        primary_confidence = result["scores"][0]

        # Secondary intents (score > 0.3)
        sub_intents = [
            label for label, score in zip(result["labels"][1:], result["scores"][1:])
            if score > 0.3
        ]

        return {
            "intent": primary_intent,
            "intent_confidence": primary_confidence,
            "sub_intents": sub_intents,
            "all_scores": {
                label: score
                for label, score in zip(result["labels"], result["scores"])
            }
        }
```

## Entity Extraction

### Named Entity Recognition

```python
from transformers import pipeline

class EntityExtractor:
    def __init__(self):
        self.ner = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple"
        )

    def extract_entities(self, text: str) -> dict:
        """Extract named entities"""
        entities_raw = self.ner(text)

        # Group by entity type
        entities = {}
        for entity in entities_raw:
            entity_type = entity["entity_group"]
            entity_text = entity["word"]

            if entity_type not in entities:
                entities[entity_type] = []

            entities[entity_type].append({
                "text": entity_text,
                "score": entity["score"],
                "start": entity["start"],
                "end": entity["end"]
            })

        return entities

    def extract_keywords(self, text: str, top_k: int = 10) -> list:
        """Extract important keywords using KeyBERT"""
        from keybert import KeyBERT

        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_k,
            use_mmr=True,
            diversity=0.7
        )

        return [
            {"keyword": kw, "relevance": score}
            for kw, score in keywords
        ]
```

## Model Training

### Fine-tuning Sentiment Model

```python
from transformers import Trainer, TrainingArguments
from datasets import load_dataset

def train_sentiment_model():
    """Fine-tune sentiment model on custom data"""

    # Load dataset
    dataset = load_dataset("voyce/feedback-sentiment")

    # Load base model
    model = AutoModelForSequenceClassification.from_pretrained(
        "roberta-base",
        num_labels=3
    )
    tokenizer = AutoTokenizer.from_pretrained("roberta-base")

    # Tokenize dataset
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=512
        )

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./models/sentiment-v1",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=100,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy"
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        compute_metrics=compute_metrics
    )

    # Train
    trainer.train()

    # Save model
    trainer.save_model("./models/sentiment-final")

def compute_metrics(eval_pred):
    """Compute accuracy and F1 score"""
    from sklearn.metrics import accuracy_score, f1_score

    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=-1)

    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1": f1_score(labels, predictions, average="weighted")
    }
```

### MLflow Tracking

```python
import mlflow
import mlflow.pytorch

def train_with_mlflow():
    """Train model with MLflow tracking"""

    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("model", "roberta-base")
        mlflow.log_param("learning_rate", 2e-5)
        mlflow.log_param("batch_size", 16)
        mlflow.log_param("epochs", 3)

        # Train model
        trainer.train()

        # Log metrics
        metrics = trainer.evaluate()
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.pytorch.log_model(
            model,
            "model",
            registered_model_name="sentiment-classifier"
        )
```

## Model Deployment

### Databricks Model Serving

```python
# Register model in MLflow
import mlflow.pyfunc

class SentimentModelWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        """Load model artifacts"""
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(context.artifacts["tokenizer"])
        self.model = AutoModelForSequenceClassification.from_pretrained(
            context.artifacts["model"]
        )

    def predict(self, context, model_input):
        """Run inference"""
        texts = model_input["text"].tolist()

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )

        outputs = self.model(**inputs)
        predictions = outputs.logits.softmax(dim=-1).detach().numpy()

        return predictions

# Log model
mlflow.pyfunc.log_model(
    artifact_path="sentiment-model",
    python_model=SentimentModelWrapper(),
    artifacts={
        "model": "./models/sentiment-final",
        "tokenizer": "./models/sentiment-final"
    }
)
```

## Performance Optimization

### Batch Processing

```python
def batch_transcribe(audio_files: list, batch_size: int = 8):
    """Process multiple files in batches"""
    results = []

    for i in range(0, len(audio_files), batch_size):
        batch = audio_files[i:i + batch_size]

        # Process batch in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [
                executor.submit(transcriber.transcribe, file)
                for file in batch
            ]

            batch_results = [f.result() for f in futures]
            results.extend(batch_results)

    return results
```

### Model Quantization

```python
import torch

def quantize_model(model_path: str, output_path: str):
    """Quantize model for faster inference"""
    model = torch.load(model_path)

    # Dynamic quantization
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8
    )

    torch.save(quantized_model, output_path)

    # 4x smaller, 2-3x faster
```

## Monitoring and Evaluation

### Performance Metrics

```python
class ModelMonitor:
    def log_inference(self, input_text: str, prediction: dict, latency: float):
        """Log model performance"""
        metrics = {
            "model_latency_ms": latency * 1000,
            "input_length": len(input_text),
            "confidence": prediction["confidence"],
            "timestamp": datetime.now()
        }

        # Log to Prometheus
        INFERENCE_LATENCY.observe(latency)
        INFERENCE_COUNT.labels(
            model="sentiment",
            prediction=prediction["label"]
        ).inc()

    def evaluate_model(self, test_dataset):
        """Evaluate model on test set"""
        from sklearn.metrics import classification_report

        predictions = []
        labels = []

        for example in test_dataset:
            pred = self.model.predict(example["text"])
            predictions.append(pred["label"])
            labels.append(example["label"])

        report = classification_report(labels, predictions)
        print(report)

        return report
```

### A/B Testing

```python
def ab_test_models(text: str) -> dict:
    """Compare two models"""
    import random

    # Randomly assign to model A or B
    if random.random() < 0.5:
        model = "model_a"
        result = model_a.predict(text)
    else:
        model = "model_b"
        result = model_b.predict(text)

    # Log which model was used
    mlflow.log_param("model_version", model)

    return result
```

## Best Practices

1. **Version Control**: Track model versions with MLflow
2. **Monitoring**: Monitor accuracy drift over time
3. **Retraining**: Retrain models monthly with new data
4. **A/B Testing**: Test new models before full deployment
5. **Caching**: Cache model predictions for common inputs
6. **Batch Processing**: Process multiple inputs together
7. **Error Handling**: Gracefully handle model failures
8. **Documentation**: Document model behavior and limitations
