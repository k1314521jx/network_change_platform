import request from './request'

/**
 * 获取 Neo4j 连接状态
 * @returns {Promise}
 */
export function getNeo4jStatus() {
  return request({
    url: '/api/neo4j/status',
    method: 'get',
  })
}

/**
 * 将审核通过的数据导入 Neo4j
 * @param {{ review_ids: Array<number|string> }} data
 * @returns {Promise}
 */
export function importToNeo4j(data) {
  return request({
    url: '/api/neo4j/import',
    method: 'post',
    data,
  })
}

/**
 * 获取导入日志
 * @param {{ page: number, per_page: number }} params
 * @returns {Promise}
 */
export function getImportLogs(params) {
  return request({
    url: '/api/neo4j/logs',
    method: 'get',
    params,
  })
}
