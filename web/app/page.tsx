'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Users, Target, Bell, Search, Filter } from 'lucide-react'
import SignalsWall from '@/components/SignalsWall'
import StatsCard from '@/components/StatsCard'
import { fetchDashboardMetrics, fetchRecentSignals } from '@/lib/api'
import logger from '@/lib/logger'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null)
  const [signals, setSignals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    logger.logComponentMount('Dashboard')
    loadData()

    return () => {
      logger.logComponentUnmount('Dashboard')
    }
  }, [])

  const loadData = async () => {
    const startTime = performance.now()

    try {
      logger.info('Loading dashboard data')
      setLoading(true)
      setError(null)

      const [metricsData, signalsData] = await Promise.all([
        fetchDashboardMetrics(),
        fetchRecentSignals()
      ])

      setMetrics(metricsData)
      setSignals(signalsData)

      const loadTime = performance.now() - startTime
      logger.logPerformance('dashboard_load_time', loadTime)
      logger.info('Dashboard data loaded successfully', {
        metrics_count: Object.keys(metricsData).length,
        signals_count: signalsData.length,
        load_time_ms: Math.round(loadTime)
      })

    } catch (error) {
      const loadTime = performance.now() - startTime
      logger.error('Failed to load dashboard data', error as Error, {
        load_time_ms: Math.round(loadTime)
      })
      setError('Failed to load dashboard data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Target className="h-8 w-8 text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">Lead Qualification Platform</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="relative p-2 text-gray-600 hover:text-gray-900">
                <Bell className="h-6 w-6" />
                <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-red-500"></span>
              </button>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium">
                  U
                </div>
                <span className="text-sm font-medium text-gray-700">User</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Companies"
            value={metrics?.total_companies || 0}
            icon={<Users className="h-6 w-6" />}
            trend="+12%"
            trendUp={true}
          />
          <StatsCard
            title="Active Signals"
            value={metrics?.total_signals || 0}
            icon={<Activity className="h-6 w-6" />}
            trend="+8%"
            trendUp={true}
          />
          <StatsCard
            title="High-Value Leads"
            value={metrics?.high_score_leads || 0}
            icon={<TrendingUp className="h-6 w-6" />}
            trend="+24%"
            trendUp={true}
          />
          <StatsCard
            title="Win Rate"
            value={`${((metrics?.win_rate || 0) * 100).toFixed(1)}%`}
            icon={<Target className="h-6 w-6" />}
            trend="+5%"
            trendUp={true}
          />
        </div>

        {/* Signals Wall */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Real-Time Signals</h2>
              <div className="flex items-center space-x-3">
                <button className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                  <Filter className="h-4 w-4" />
                  <span>Filter</span>
                </button>
                <button className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                  <Search className="h-4 w-4" />
                  <span>Search</span>
                </button>
              </div>
            </div>
          </div>
          <SignalsWall signals={signals} onRefresh={loadData} />
        </div>
      </main>
    </div>
  )
}
