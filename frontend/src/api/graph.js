import request from './request'

export function getGraphLabels() {
  return request({ url: '/api/graph/labels', method: 'get' })
}

export function getGraphRelTypes() {
  return request({ url: '/api/graph/relationship-types', method: 'get' })
}

export function getGraphData(params) {
  return request({ url: '/api/graph/graph', method: 'get', params })
}

export function getShortestPath(params) {
  return request({ url: '/api/graph/shortest-path', method: 'get', params })
}

export function searchNodes(params) {
  return request({ url: '/api/graph/search-nodes', method: 'get', params })
}
