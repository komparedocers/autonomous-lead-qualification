import logger from './logger'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080'

/**
 * Enhanced fetch wrapper with comprehensive logging and error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const startTime = performance.now()

  try {
    logger.debug(`API Request: ${options.method || 'GET'} ${endpoint}`)

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    const duration = performance.now() - startTime

    // Extract request ID from response headers
    const requestId = response.headers.get('X-Request-ID')
    if (requestId) {
      logger.setRequestId(requestId)
    }

    // Log API call
    logger.logApiCall(
      options.method || 'GET',
      endpoint,
      response.status,
      duration
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const error = new Error(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`
      )

      logger.error(`API Error: ${options.method || 'GET'} ${endpoint}`, error, {
        status: response.status,
        statusText: response.statusText,
        requestId,
        errorData,
        duration,
      })

      throw error
    }

    const data = await response.json()

    logger.debug(`API Response: ${options.method || 'GET'} ${endpoint}`, {
      status: response.status,
      requestId,
      duration,
    })

    return data
  } catch (error) {
    const duration = performance.now() - startTime

    logger.error(`API Request Failed: ${options.method || 'GET'} ${endpoint}`, error as Error, {
      duration,
      url,
    })

    throw error
  }
}

export async function fetchDashboardMetrics() {
  try {
    logger.info('Fetching dashboard metrics')

    // Mock data for now - replace with actual API call
    // return await apiFetch('/api/v1/dashboard/metrics')

    const mockData = {
      total_companies: 245,
      total_signals: 89,
      total_proposals: 34,
      high_score_leads: 28,
      signals_today: 12,
      win_rate: 0.42,
      avg_deal_value: 125000
    }

    logger.info('Dashboard metrics fetched successfully', {
      total_companies: mockData.total_companies,
      total_signals: mockData.total_signals
    })

    return mockData
  } catch (error) {
    logger.error('Failed to fetch dashboard metrics', error as Error)
    throw error
  }
}

export async function fetchRecentSignals() {
  try {
    logger.info('Fetching recent signals')

    // Mock data for now - replace with actual API call
    // return await apiFetch('/api/v1/signals/search?limit=20')

    const mockSignals = [
      {
        id: 1,
        company_id: 101,
        kind: 'hiring_spike',
        score: 85,
        explanation: 'Company is rapidly hiring for Data Engineering roles (15 new positions in the last 30 days)',
        timestamp_start: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        evidence: [
          { url: 'https://example.com/careers', snippet: '15 Data Engineer positions' }
        ]
      },
      {
        id: 2,
        company_id: 102,
        kind: 'tech_adoption',
        score: 92,
        explanation: 'Recently adopted Snowflake and showing interest in modern data stack solutions',
        timestamp_start: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        evidence: [
          { url: 'https://example.com/blog', snippet: 'Migrating to Snowflake' }
        ]
      },
      {
        id: 3,
        company_id: 103,
        kind: 'funding_event',
        score: 88,
        explanation: 'Raised $50M Series B funding, likely to invest in infrastructure',
        timestamp_start: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        evidence: [
          { url: 'https://example.com/news', snippet: 'Series B funding announcement' }
        ]
      },
      {
        id: 4,
        company_id: 104,
        kind: 'expansion',
        score: 78,
        explanation: 'Opening new offices in 3 regions, expanding operations globally',
        timestamp_start: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        evidence: [
          { url: 'https://example.com/press', snippet: 'Global expansion announcement' }
        ]
      },
      {
        id: 5,
        company_id: 105,
        kind: 'hiring_spike',
        score: 82,
        explanation: 'Hiring VP of Engineering and multiple senior technical leaders',
        timestamp_start: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        evidence: [
          { url: 'https://example.com/jobs', snippet: 'VP Engineering role' }
        ]
      }
    ]

    logger.info('Recent signals fetched successfully', { count: mockSignals.length })

    return mockSignals
  } catch (error) {
    logger.error('Failed to fetch signals', error as Error)
    throw error
  }
}

export async function fetchCompanies() {
  logger.info('Fetching companies list')
  return await apiFetch('/api/v1/companies/')
}

export async function fetchCompany360(companyId: number) {
  logger.info('Fetching company 360 view', { companyId })
  return await apiFetch(`/api/v1/companies/${companyId}`)
}

export async function searchSignals(filters: any) {
  logger.info('Searching signals', { filters })
  const params = new URLSearchParams(filters)
  return await apiFetch(`/api/v1/signals/search?${params}`)
}

export async function createProposal(companyId: number, productId: string) {
  logger.info('Creating proposal', { companyId, productId })
  logger.logUserAction('create_proposal', { companyId, productId })

  return await apiFetch(
    `/api/v1/proposals/draft?company_id=${companyId}&product_id=${productId}`,
    { method: 'POST' }
  )
}

export async function runAgent(agentName: string, agentType: string, companyId?: number) {
  logger.info('Running agent', { agentName, agentType, companyId })
  logger.logUserAction('run_agent', { agentName, agentType, companyId })

  return await apiFetch('/api/v1/agents/run', {
    method: 'POST',
    body: JSON.stringify({
      agent_name: agentName,
      agent_type: agentType,
      company_id: companyId
    })
  })
}
