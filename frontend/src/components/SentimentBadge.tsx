import { SentimentType } from '../types';
import { getSentimentLabel, getSentimentColor } from '../utils/helpers';
import clsx from 'clsx';

interface SentimentBadgeProps {
  sentiment: SentimentType;
  confidence?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const SentimentBadge = ({
  sentiment,
  confidence,
  size = 'md',
}: SentimentBadgeProps) => {
  const color = getSentimentColor(sentiment);
  const label = getSentimentLabel(sentiment);

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <div className="flex items-center space-x-2">
      <span
        className={clsx(
          'inline-flex items-center rounded-full font-medium text-white',
          sizeClasses[size]
        )}
        style={{ backgroundColor: color }}
      >
        {label}
      </span>
      {confidence !== undefined && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  );
};
