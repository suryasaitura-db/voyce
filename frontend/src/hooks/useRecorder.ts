import { useState, useRef, useCallback, useEffect } from 'react';
import { RecordingState } from '../types';
import { MAX_RECORDING_DURATION, AUDIO_CONSTRAINTS } from '../utils/constants';

interface UseRecorderReturn extends RecordingState {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  resetRecording: () => void;
  error: string | null;
}

export const useRecorder = (): UseRecorderReturn => {
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    audioBlob: null,
    audioUrl: null,
  });
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);
  const pausedDurationRef = useRef<number>(0);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTimer();
      stopMediaStream();
    };
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    stopTimer();
    startTimeRef.current = Date.now() - pausedDurationRef.current;

    timerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);

      setRecordingState((prev) => ({
        ...prev,
        duration: elapsed,
      }));

      // Auto-stop at max duration
      if (elapsed >= MAX_RECORDING_DURATION) {
        stopRecording();
      }
    }, 100);
  }, []);

  const stopMediaStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      audioChunksRef.current = [];

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia(AUDIO_CONSTRAINTS);
      streamRef.current = stream;

      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      });
      mediaRecorderRef.current = mediaRecorder;

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);

        setRecordingState((prev) => ({
          ...prev,
          audioBlob,
          audioUrl,
          isRecording: false,
          isPaused: false,
        }));

        stopMediaStream();
      };

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      startTimer();

      setRecordingState((prev) => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        duration: 0,
        audioBlob: null,
        audioUrl: null,
      }));

      pausedDurationRef.current = 0;
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to access microphone. Please check your permissions.');
      stopMediaStream();
    }
  }, [startTimer, stopMediaStream]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState.isRecording) {
      mediaRecorderRef.current.stop();
      stopTimer();
    }
  }, [recordingState.isRecording, stopTimer]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState.isRecording && !recordingState.isPaused) {
      mediaRecorderRef.current.pause();
      stopTimer();
      pausedDurationRef.current = recordingState.duration * 1000;

      setRecordingState((prev) => ({
        ...prev,
        isPaused: true,
      }));
    }
  }, [recordingState.isRecording, recordingState.isPaused, recordingState.duration, stopTimer]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState.isRecording && recordingState.isPaused) {
      mediaRecorderRef.current.resume();
      startTimer();

      setRecordingState((prev) => ({
        ...prev,
        isPaused: false,
      }));
    }
  }, [recordingState.isRecording, recordingState.isPaused, startTimer]);

  const resetRecording = useCallback(() => {
    stopRecording();
    stopTimer();
    stopMediaStream();

    if (recordingState.audioUrl) {
      URL.revokeObjectURL(recordingState.audioUrl);
    }

    audioChunksRef.current = [];
    pausedDurationRef.current = 0;

    setRecordingState({
      isRecording: false,
      isPaused: false,
      duration: 0,
      audioBlob: null,
      audioUrl: null,
    });

    setError(null);
  }, [recordingState.audioUrl, stopRecording, stopTimer, stopMediaStream]);

  return {
    ...recordingState,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
    error,
  };
};
