import request from './request'

/**
 * 获取待审核列表
 * @returns {Promise}
 */
export function getPendingList(params) {
  return request({
    url: '/api/review/list',
    method: 'get',
    params,
  })
}

/**
 * 获取已通过列表
 * @returns {Promise}
 */
export function getApprovedList() {
  return request({
    url: '/api/review/approved',
    method: 'get',
  })
}

/**
 * 获取已驳回列表
 * @returns {Promise}
 */
export function getRejectedList() {
  return request({
    url: '/api/review/rejected',
    method: 'get',
  })
}

/**
 * 获取审核详情数据
 * @param {number|string} tripleTaskId
 * @returns {Promise}
 */
export function getReviewData(tripleTaskId) {
  return request({
    url: `/api/review/${tripleTaskId}`,
    method: 'get',
  })
}

/**
 * 提交审核结果
 * @param {number|string} tripleTaskId
 * @param {{ table1: Array, table2: Array, table3: Array, review_status: string, reviewer: string }} data
 * @returns {Promise}
 */
export function submitReview(tripleTaskId, data) {
  return request({
    url: `/api/review/${tripleTaskId}/submit`,
    method: 'post',
    data,
  })
}
