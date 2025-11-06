import { ArrowUp, ArrowDown } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  trend?: string
  trendUp?: boolean
}

export default function StatsCard({ title, value, icon, trend, trendUp }: StatsCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              {trendUp ? (
                <ArrowUp className="h-4 w-4 text-green-600 mr-1" />
              ) : (
                <ArrowDown className="h-4 w-4 text-red-600 mr-1" />
              )}
              <span className={`text-sm font-medium ${trendUp ? 'text-green-600' : 'text-red-600'}`}>
                {trend}
              </span>
              <span className="text-sm text-gray-500 ml-1">vs last month</span>
            </div>
          )}
        </div>
        <div className="ml-4 p-3 bg-blue-50 rounded-lg">
          <div className="text-blue-600">{icon}</div>
        </div>
      </div>
    </div>
  )
}
