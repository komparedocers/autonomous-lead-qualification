import { RefreshCw, ExternalLink, TrendingUp, Zap, DollarSign, Users } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Signal {
  id: number
  company_id: number
  kind: string
  score: number
  explanation: string
  timestamp_start: string
  evidence: Array<{ url: string; snippet: string }>
}

interface SignalsWallProps {
  signals: Signal[]
  onRefresh: () => void
}

const signalIcons: Record<string, any> = {
  hiring_spike: Users,
  tech_adoption: Zap,
  funding_event: DollarSign,
  expansion: TrendingUp,
}

const signalColors: Record<string, string> = {
  hiring_spike: 'bg-blue-100 text-blue-700',
  tech_adoption: 'bg-purple-100 text-purple-700',
  funding_event: 'bg-green-100 text-green-700',
  expansion: 'bg-orange-100 text-orange-700',
}

export default function SignalsWall({ signals, onRefresh }: SignalsWallProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800'
    if (score >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
  }

  const formatSignalKind = (kind: string) => {
    return kind.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  return (
    <div className="divide-y divide-gray-200">
      {/* Header Actions */}
      <div className="px-6 py-3 bg-gray-50 flex justify-between items-center">
        <p className="text-sm text-gray-600">{signals.length} signals found</p>
        <button
          onClick={onRefresh}
          className="flex items-center space-x-2 px-3 py-1 text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Signals List */}
      <div className="max-h-[600px] overflow-y-auto">
        {signals.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500">No signals found. Agents are discovering new opportunities...</p>
          </div>
        ) : (
          signals.map((signal) => {
            const IconComponent = signalIcons[signal.kind] || Zap
            const colorClass = signalColors[signal.kind] || 'bg-gray-100 text-gray-700'

            return (
              <div
                key={signal.id}
                className="px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Signal Icon */}
                    <div className={`p-2 rounded-lg ${colorClass}`}>
                      <IconComponent className="h-5 w-5" />
                    </div>

                    {/* Signal Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
                          {formatSignalKind(signal.kind)}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getScoreColor(signal.score)}`}>
                          Score: {signal.score}
                        </span>
                      </div>

                      <p className="text-sm font-medium text-gray-900 mb-1">
                        Company #{signal.company_id}
                      </p>

                      <p className="text-sm text-gray-600 mb-2">
                        {signal.explanation}
                      </p>

                      {/* Evidence */}
                      {signal.evidence && signal.evidence.length > 0 && (
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <ExternalLink className="h-3 w-3" />
                          <span>{signal.evidence.length} evidence link(s)</span>
                        </div>
                      )}

                      {/* Timestamp */}
                      <p className="text-xs text-gray-400 mt-2">
                        {formatDistanceToNow(new Date(signal.timestamp_start), { addSuffix: true })}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col space-y-2 ml-4">
                    <button className="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">
                      Create Opp
                    </button>
                    <button className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50">
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
