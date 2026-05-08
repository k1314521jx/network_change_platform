import request from './request'

export function getRuleValidationList(params) {
  return request({ url: '/api/rule-validation/list', method: 'get', params })
}

export function getRuleValidationDetail(tripleTaskId) {
  return request({ url: `/api/rule-validation/detail/${tripleTaskId}`, method: 'get' })
}

export function validateRule(tripleTaskId) {
  return request({ url: `/api/triple/tasks/${tripleTaskId}/validate`, method: 'post' })
}

export function batchValidateRules(ids) {
  return request({ url: '/api/triple/tasks/batch-validate', method: 'post', data: { ids } })
}

export function getPassedTasks() {
  return request({ url: '/api/rule-validation/passed-tasks', method: 'get' })
}

export function exportTripleXlsx(tripleTaskId) {
  return request({
    url: `/api/rule-validation/${tripleTaskId}/export-xlsx`,
    method: 'get',
    responseType: 'blob',
  })
}

export function importTripleXlsx(tripleTaskId, formData) {
  return request({
    url: `/api/rule-validation/${tripleTaskId}/import-xlsx`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
