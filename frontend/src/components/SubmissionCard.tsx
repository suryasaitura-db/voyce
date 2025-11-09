import { Submission } from '../types';
import { formatDate, formatDuration, truncateText } from '../utils/helpers';
import { SentimentBadge } from './SentimentBadge';
import { AudioPlayer } from './AudioPlayer';

interface SubmissionCardProps {
  submission: Submission;
  onDelete?: (id: string) => void;
}

export const SubmissionCard = ({ submission, onDelete }: SubmissionCardProps) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <SentimentBadge
              sentiment={submission.sentiment}
              confidence={submission.confidence_score}
            />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(submission.created_at, 'MMM dd, yyyy HH:mm')}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
            Duration: {formatDuration(submission.duration)}
          </p>
        </div>

        {onDelete && (
          <button
            onClick={() => onDelete(submission.id)}
            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 p-2 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            title="Delete submission"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Transcription:
        </h4>
        <p className="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 rounded-md p-3">
          {submission.transcription || 'No transcription available'}
        </p>
      </div>

      <AudioPlayer src={submission.audio_url} />
    </div>
  );
};
