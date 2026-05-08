import request from './request'

export function createAiReview(data) {
  return request({ url: '/api/ai-review/create', method: 'post', data })
}

export function getAiReviewList(params) {
  return request({ url: '/api/ai-review/list', method: 'get', params })
}

export function getAiReviewDetail(reviewId) {
  return request({ url: `/api/ai-review/${reviewId}`, method: 'get' })
}

export function retryAiReview(reviewId) {
  return request({ url: `/api/ai-review/${reviewId}/retry`, method: 'post' })
}

export function startAiReview(reviewId, data) {
  return request({ url: `/api/ai-review/${reviewId}/start`, method: 'post', data })
}

export function exportAiReviewThinking(reviewId) {
  return request({ url: `/api/ai-review/${reviewId}/thinking`, method: 'get', responseType: 'blob' })
}
