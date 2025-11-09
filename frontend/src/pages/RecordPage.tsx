import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { VoiceRecorder } from '../components/VoiceRecorder';
import { useCreateSubmission } from '../hooks/useSubmissions';
import { ApiError } from '../types';

export const RecordPage = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const createSubmission = useCreateSubmission();
  const navigate = useNavigate();

  const handleRecordingComplete = async (blob: Blob) => {
    setError(null);
    setSuccess(false);

    // Auto-submit the recording
    try {
      setIsSubmitting(true);

      // Convert blob to file
      const file = new File([blob], `recording-${Date.now()}.webm`, {
        type: 'audio/webm',
      });

      await createSubmission.mutateAsync(file);
      setSuccess(true);

      // Redirect to submissions after 2 seconds
      setTimeout(() => {
        navigate('/submissions');
      }, 2000);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || 'Failed to submit recording. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Record Voice Feedback
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Click the microphone button to start recording your voice feedback
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg max-w-2xl mx-auto">
            Recording submitted successfully! Redirecting to submissions...
          </div>
        )}

        {isSubmitting && (
          <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 px-4 py-3 rounded-lg max-w-2xl mx-auto">
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-700 dark:border-blue-400"></div>
              <span>Analyzing your recording...</span>
            </div>
          </div>
        )}

        <VoiceRecorder onRecordingComplete={handleRecordingComplete} />

        <div className="mt-12 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 max-w-2xl mx-auto">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Tips for Best Results
          </h3>
          <ul className="space-y-2 text-gray-600 dark:text-gray-300">
            <li className="flex items-start">
              <svg
                className="w-5 h-5 text-primary-600 mr-2 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Speak clearly and at a moderate pace</span>
            </li>
            <li className="flex items-start">
              <svg
                className="w-5 h-5 text-primary-600 mr-2 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Minimize background noise for better transcription</span>
            </li>
            <li className="flex items-start">
              <svg
                className="w-5 h-5 text-primary-600 mr-2 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Position your microphone 6-12 inches from your mouth</span>
            </li>
            <li className="flex items-start">
              <svg
                className="w-5 h-5 text-primary-600 mr-2 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Review your recording before submitting</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
