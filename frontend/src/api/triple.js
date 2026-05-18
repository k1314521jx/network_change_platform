import request from './request'

/**
 * 将规则任务转换为三元组
 * @param {{ rule_task_id: number|string, model: string }} data
 * @returns {Promise}
 */
export function convertToTriple(data) {
  return request({
    url: '/api/triple/convert',
    method: 'post',
    data,
  })
}

/**
 * 获取三元组任务列表
 * @param {{ page: number, per_page: number, filename?: string }} params
 * @returns {Promise}
 */
export function getTripleTasks(params) {
  return request({
    url: '/api/triple/tasks',
    method: 'get',
    params,
  })
}

/**
 * 获取单个三元组任务详情
 * @param {number|string} id
 * @returns {Promise}
 */
export function getTripleTask(id) {
  return request({
    url: `/api/triple/tasks/${id}`,
    method: 'get',
  })
}

/**
 * 重试失败的三元组转换任务
 * @param {number|string} id
 * @param {{ model?: string }} data
 * @returns {Promise}
 */
export function retryTripleTask(id, data = {}) {
  return request({
    url: `/api/triple/tasks/${id}/retry`,
    method: 'post',
    data,
  })
}

/**
 * 导出 LLM 思考过程（blob下载，需自行处理错误）
 * @param {number|string} id
 * @returns {Promise<Blob>}
 */
export function exportThinking(id) {
  return request({
    url: `/api/triple/tasks/${id}/thinking`,
    method: 'get',
    responseType: 'blob',
  })
}

export function updateAndValidate(taskId, data) {
  return request({
    url: `/api/triple/tasks/${taskId}/update-and-validate`,
    method: 'post',
    data,
  })
}

/**
 * 批量转换规则任务为三元组
 * @param {{ rule_task_ids: number[], model?: string, prompt_id?: number }} data
 * @returns {Promise}
 */
export function batchConvertToTriple(data) {
  return request({
    url: '/api/triple/batch-convert',
    method: 'post',
    data,
  })
}
