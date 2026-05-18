import request from './request'

export function getDashboardOverview() {
  return request.get('/api/dashboard/overview')
}

export function getDashboardDailyTrend() {
  return request.get('/api/dashboard/daily-trend')
}

export function getDashboardAiScoreByModel() {
  return request.get('/api/dashboard/ai-score-by-model')
}

export function getDashboardViolationRateByModel() {
  return request.get('/api/dashboard/violation-rate-by-model')
}
