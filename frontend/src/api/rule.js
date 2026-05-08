import request from './request'

/**
 * 上传 Excel 文件
 * @param {FormData} formData - 包含 excel 文件的 FormData
 * @returns {Promise}
 */
export function uploadExcel(formData) {
  return request({
    url: '/api/rule/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 获取规则任务列表
 * @param {{ page: number, per_page: number, filename?: string }} params
 * @returns {Promise}
 */
export function getRuleTasks(params) {
  return request({
    url: '/api/rule/tasks',
    method: 'get',
    params,
  })
}

/**
 * 获取单个规则任务详情
 * @param {number|string} id
 * @returns {Promise}
 */
export function getRuleTask(id) {
  return request({
    url: `/api/rule/tasks/${id}`,
    method: 'get',
  })
}

/**
 * 重试失败的规则任务
 * @param {number|string} id
 * @returns {Promise}
 */
export function retryRuleTask(id) {
  return request({
    url: `/api/rule/tasks/${id}/retry`,
    method: 'post',
  })
}

export function deleteRuleTask(id) {
  return request({
    url: `/api/rule/tasks/${id}`,
    method: 'delete',
  })
}

/**
 * 获取所有成功的规则任务
 * @returns {Promise}
 */
export function getSuccessRuleTasks() {
  return request({
    url: '/api/rule/tasks/success',
    method: 'get',
  })
}
