import request from './request'

export function getModelList() {
  return request({ url: '/api/model/list', method: 'get' })
}

export function getModelDetail(modelId) {
  return request({ url: `/api/model/detail/${modelId}`, method: 'get' })
}

export function createModel(data) {
  return request({ url: '/api/model/create', method: 'post', data })
}

export function updateModel(modelId, data) {
  return request({ url: `/api/model/update/${modelId}`, method: 'put', data })
}

export function deleteModel(modelId) {
  return request({ url: `/api/model/delete/${modelId}`, method: 'delete' })
}

export function getModelOptions() {
  return request({ url: '/api/model/options', method: 'get' })
}

export function testModelConnection(data) {
  return request({ url: '/api/model/test', method: 'post', data })
}
