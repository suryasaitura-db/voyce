import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { CHART_COLORS } from '../utils/constants';

interface SentimentData {
  name: string;
  value: number;
}

interface TimeSeriesDataPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

interface SentimentDistributionProps {
  data: SentimentData[];
}

export const SentimentDistribution = ({ data }: SentimentDistributionProps) => {
  const COLORS = [CHART_COLORS.positive, CHART_COLORS.neutral, CHART_COLORS.negative];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Sentiment Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

interface SentimentTrendsProps {
  data: TimeSeriesDataPoint[];
}

export const SentimentTrends = ({ data }: SentimentTrendsProps) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Sentiment Trends Over Time
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="positive"
            stroke={CHART_COLORS.positive}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="neutral"
            stroke={CHART_COLORS.neutral}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="negative"
            stroke={CHART_COLORS.negative}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

interface SentimentComparisonProps {
  data: TimeSeriesDataPoint[];
}

export const SentimentComparison = ({ data }: SentimentComparisonProps) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Sentiment Comparison
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="positive" fill={CHART_COLORS.positive} />
          <Bar dataKey="neutral" fill={CHART_COLORS.neutral} />
          <Bar dataKey="negative" fill={CHART_COLORS.negative} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
