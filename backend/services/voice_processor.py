"""
Voice-to-Text Processing Pipeline
Multi-engine support with automatic fallback and cost optimization
"""
import asyncio
import io
import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

import aiofiles
from pydub import AudioSegment
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class STTEngine(str, Enum):
    """Speech-to-Text Engine Options"""
    WHISPER = "whisper"
    GOOGLE = "google"
    AWS = "aws"
    AZURE = "azure"
    DEEPGRAM = "deepgram"


@dataclass
class TranscriptionResult:
    """Transcription result with metadata"""
    text: str
    confidence: float
    language: str
    duration_ms: int
    engine: STTEngine
    word_count: int
    character_count: int
    cost_usd: float
    metadata: Dict[str, Any]


class AudioPreprocessor:
    """Audio preprocessing and normalization"""

    @staticmethod
    async def preprocess(audio_path: str) -> str:
        """
        Preprocess audio file:
        - Convert to optimal format (WAV, 16kHz, mono)
        - Noise reduction
        - Normalization
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)

            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Set sample rate to 16kHz (optimal for STT)
            audio = audio.set_frame_rate(16000)

            # Normalize volume
            audio = audio.normalize()

            # Apply noise reduction (simple high-pass filter)
            audio = audio.high_pass_filter(100)

            # Export as WAV
            preprocessed_path = audio_path.rsplit('.', 1)[0] + '_preprocessed.wav'
            audio.export(preprocessed_path, format='wav')

            logger.info(f"Audio preprocessed: {preprocessed_path}")
            return preprocessed_path

        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            return audio_path  # Return original if preprocessing fails


class WhisperEngine:
    """OpenAI Whisper STT Engine"""

    def __init__(self, api_key: Optional[str] = None, use_local: bool = False):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_local = use_local or os.getenv('USE_LOCAL_WHISPER', 'false').lower() == 'true'
        self.model_name = os.getenv('WHISPER_MODEL', 'base')
        self.local_model = None

        if self.use_local:
            try:
                import whisper
                self.local_model = whisper.load_model(self.model_name)
                logger.info(f"Loaded local Whisper model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load local Whisper model: {e}")
                self.use_local = False

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio using Whisper"""
        start_time = time.time()

        try:
            if self.use_local and self.local_model:
                result = await self._transcribe_local(audio_path, language)
            else:
                result = await self._transcribe_api(audio_path, language)

            duration_ms = int((time.time() - start_time) * 1000)

            return TranscriptionResult(
                text=result['text'].strip(),
                confidence=result.get('confidence', 0.95),
                language=result.get('language', language or 'en'),
                duration_ms=duration_ms,
                engine=STTEngine.WHISPER,
                word_count=len(result['text'].split()),
                character_count=len(result['text']),
                cost_usd=self._calculate_cost(audio_path),
                metadata=result
            )

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise

    async def _transcribe_local(self, audio_path: str, language: Optional[str]) -> Dict:
        """Local Whisper transcription"""
        result = self.local_model.transcribe(
            audio_path,
            language=language,
            fp16=False
        )

        # Calculate average confidence from segments
        if 'segments' in result:
            confidences = [s.get('no_speech_prob', 0) for s in result['segments']]
            avg_confidence = 1 - (sum(confidences) / len(confidences)) if confidences else 0.95
        else:
            avg_confidence = 0.95

        return {
            'text': result['text'],
            'language': result.get('language', language),
            'confidence': avg_confidence,
            'segments': result.get('segments', [])
        }

    async def _transcribe_api(self, audio_path: str, language: Optional[str]) -> Dict:
        """OpenAI Whisper API transcription"""
        import openai

        client = openai.AsyncOpenAI(api_key=self.api_key)

        async with aiofiles.open(audio_path, 'rb') as audio_file:
            audio_data = await audio_file.read()

        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=io.BytesIO(audio_data),
            language=language,
            response_format="verbose_json"
        )

        return {
            'text': response.text,
            'language': response.language,
            'confidence': 0.95,  # API doesn't provide confidence
            'duration': response.duration
        }

    def _calculate_cost(self, audio_path: str) -> float:
        """Calculate Whisper API cost ($0.006 per minute)"""
        if self.use_local:
            return 0.0  # Local is free

        # Get audio duration
        audio = AudioSegment.from_file(audio_path)
        duration_minutes = len(audio) / 1000 / 60
        return duration_minutes * 0.006


class GoogleSTTEngine:
    """Google Cloud Speech-to-Text Engine"""

    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.client = None

        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                from google.cloud import speech
                self.client = speech.SpeechClient()
                logger.info("Google Speech-to-Text client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google STT: {e}")

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio using Google Cloud Speech-to-Text"""
        if not self.client:
            raise Exception("Google STT client not initialized")

        start_time = time.time()

        try:
            from google.cloud import speech

            async with aiofiles.open(audio_path, 'rb') as audio_file:
                audio_content = await audio_file.read()

            audio = speech.RecognitionAudio(content=audio_content)

            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language or 'en-US',
                enable_automatic_punctuation=True,
                model='latest_long',
                use_enhanced=True
            )

            response = self.client.recognize(config=config, audio=audio)

            if not response.results:
                raise Exception("No transcription results")

            # Combine all alternatives
            full_text = ' '.join([
                result.alternatives[0].transcript
                for result in response.results
            ])

            avg_confidence = sum([
                result.alternatives[0].confidence
                for result in response.results
            ]) / len(response.results)

            duration_ms = int((time.time() - start_time) * 1000)

            return TranscriptionResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                language=language or 'en',
                duration_ms=duration_ms,
                engine=STTEngine.GOOGLE,
                word_count=len(full_text.split()),
                character_count=len(full_text),
                cost_usd=self._calculate_cost(audio_path),
                metadata={'results': len(response.results)}
            )

        except Exception as e:
            logger.error(f"Google STT transcription failed: {e}")
            raise

    def _calculate_cost(self, audio_path: str) -> float:
        """Calculate Google STT cost ($0.024 per minute for enhanced model)"""
        audio = AudioSegment.from_file(audio_path)
        duration_minutes = len(audio) / 1000 / 60
        return duration_minutes * 0.024


class AWSSTT Engine:
    """AWS Transcribe Engine"""

    def __init__(self):
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket = os.getenv('AWS_S3_BUCKET')
        self.client = None
        self.s3_client = None

        if self.access_key and self.secret_key:
            try:
                import boto3
                self.client = boto3.client(
                    'transcribe',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                logger.info("AWS Transcribe client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AWS Transcribe: {e}")

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio using AWS Transcribe"""
        if not self.client or not self.s3_client:
            raise Exception("AWS Transcribe client not initialized")

        start_time = time.time()
        job_name = f"voyce_{int(time.time() * 1000)}"

        try:
            # Upload to S3
            s3_key = f"transcribe/{job_name}.wav"
            self.s3_client.upload_file(audio_path, self.bucket, s3_key)
            s3_uri = f"s3://{self.bucket}/{s3_key}"

            # Start transcription job
            self.client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='wav',
                LanguageCode=language or 'en-US'
            )

            # Wait for completion
            while True:
                status = self.client.get_transcription_job(TranscriptionJobName=job_name)
                job_status = status['TranscriptionJob']['TranscriptionJobStatus']

                if job_status in ['COMPLETED', 'FAILED']:
                    break

                await asyncio.sleep(2)

            if job_status == 'FAILED':
                raise Exception("AWS Transcribe job failed")

            # Get transcript
            transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(transcript_uri)
                result = response.json()

            full_text = result['results']['transcripts'][0]['transcript']

            # Calculate average confidence
            items = result['results']['items']
            confidences = [float(item['alternatives'][0]['confidence'])
                          for item in items if 'confidence' in item.get('alternatives', [{}])[0]]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.9

            duration_ms = int((time.time() - start_time) * 1000)

            # Cleanup S3
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)

            return TranscriptionResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                language=language or 'en',
                duration_ms=duration_ms,
                engine=STTEngine.AWS,
                word_count=len(full_text.split()),
                character_count=len(full_text),
                cost_usd=self._calculate_cost(audio_path),
                metadata={'job_name': job_name}
            )

        except Exception as e:
            logger.error(f"AWS Transcribe failed: {e}")
            raise
        finally:
            # Cleanup job
            try:
                self.client.delete_transcription_job(TranscriptionJobName=job_name)
            except:
                pass

    def _calculate_cost(self, audio_path: str) -> float:
        """Calculate AWS Transcribe cost ($0.024 per minute)"""
        audio = AudioSegment.from_file(audio_path)
        duration_minutes = len(audio) / 1000 / 60
        return duration_minutes * 0.024


class VoiceToTextProcessor:
    """
    Main voice-to-text processor with multi-engine support and fallback
    """

    def __init__(self, engines: Optional[List[str]] = None):
        """
        Initialize with prioritized engine list

        Args:
            engines: List of engine names in priority order
                    Default: ['whisper', 'google', 'aws']
        """
        self.engines_priority = engines or os.getenv('STT_ENGINES', 'whisper,google,aws').split(',')
        self.preprocessor = AudioPreprocessor()

        # Initialize engines
        self.engines = {
            STTEngine.WHISPER: WhisperEngine(),
            STTEngine.GOOGLE: GoogleSTTEngine(),
            STTEngine.AWS: AWSSTTEngine()
        }

        logger.info(f"VoiceToTextProcessor initialized with engines: {self.engines_priority}")

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        min_confidence: float = 0.8,
        preprocess: bool = True
    ) -> TranscriptionResult:
        """
        Transcribe audio with automatic fallback

        Args:
            audio_path: Path to audio file
            language: Language hint (e.g., 'en', 'es', 'hi')
            min_confidence: Minimum confidence threshold
            preprocess: Whether to preprocess audio

        Returns:
            TranscriptionResult

        Raises:
            Exception if all engines fail
        """
        # Preprocess audio
        if preprocess:
            audio_path = await self.preprocessor.preprocess(audio_path)

        errors = []

        # Try each engine in priority order
        for engine_name in self.engines_priority:
            try:
                engine = self.engines.get(STTEngine(engine_name))
                if not engine:
                    logger.warning(f"Engine {engine_name} not available")
                    continue

                logger.info(f"Attempting transcription with {engine_name}")

                result = await engine.transcribe(audio_path, language)

                # Check confidence threshold
                if result.confidence >= min_confidence:
                    logger.info(f"Transcription successful with {engine_name} (confidence: {result.confidence:.2f})")
                    return result
                else:
                    logger.warning(f"{engine_name} confidence {result.confidence:.2f} below threshold {min_confidence}")
                    errors.append(f"{engine_name}: Low confidence ({result.confidence:.2f})")

            except Exception as e:
                logger.error(f"{engine_name} transcription failed: {e}")
                errors.append(f"{engine_name}: {str(e)}")
                continue

        # All engines failed
        error_msg = f"All STT engines failed: {'; '.join(errors)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def batch_transcribe(
        self,
        audio_paths: List[str],
        language: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files concurrently

        Args:
            audio_paths: List of audio file paths
            language: Language hint
            max_concurrent: Maximum concurrent transcriptions

        Returns:
            List of TranscriptionResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def transcribe_with_semaphore(path):
            async with semaphore:
                return await self.transcribe(path, language)

        tasks = [transcribe_with_semaphore(path) for path in audio_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful = [r for r in results if isinstance(r, TranscriptionResult)]
        failed = [r for r in results if isinstance(r, Exception)]

        logger.info(f"Batch transcription: {len(successful)} successful, {len(failed)} failed")

        return successful
