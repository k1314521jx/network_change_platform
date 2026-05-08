import request from './request'

export function getPromptList(params) {
  return request({ url: '/api/prompt/list', method: 'get', params })
}

export function getPromptDetail(promptId) {
  return request({ url: `/api/prompt/detail/${promptId}`, method: 'get' })
}

export function createPrompt(data) {
  return request({ url: '/api/prompt/create', method: 'post', data })
}

export function updatePrompt(promptId, data) {
  return request({ url: `/api/prompt/update/${promptId}`, method: 'put', data })
}

export function deletePrompt(promptId) {
  return request({ url: `/api/prompt/delete/${promptId}`, method: 'delete' })
}

export function getPromptHistory(name, params) {
  return request({ url: `/api/prompt/history/${encodeURIComponent(name)}`, method: 'get', params })
}

export function getPromptOptions(params) {
  return request({ url: '/api/prompt/options', method: 'get', params })
}

export function activatePrompt(promptId) {
  return request({ url: `/api/prompt/activate/${promptId}`, method: 'post' })
}
