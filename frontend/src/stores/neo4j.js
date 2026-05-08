import { defineStore } from 'pinia'
import { getNeo4jStatus, importToNeo4j, getImportLogs } from '@/api/neo4j'
import { getApprovedList } from '@/api/review'

export const useNeo4jStore = defineStore('neo4j', {
  state: () => ({
    /** Neo4j 连接状态：false=未连接, null=检测中, true=已连接 */
    connected: null,
    /** 审核通过的数据列表 */
    approvedReviews: [],
    /** 已选中的审核记录 ID 集合 */
    selectedReviewIds: new Set(),
    /** 导入日志列表 */
    logs: [],
    /** 日志总数 */
    logTotal: 0,
    /** 日志当前页码 */
    logPage: 1,
    /** 日志每页条数 */
    logPerPage: 15,
    /** 是否正在导入 */
    importing: false,
    /** 加载状态 */
    loading: false,
  }),

  actions: {
    /**
     * 检查 Neo4j 连接状态
     */
    async checkStatus() {
      try {
        const res = await getNeo4jStatus()
        this.connected = res.data.connected
      } catch {
        this.connected = false
      }
    },

    /**
     * 获取审核通过的数据列表（可导入的数据源）
     */
    async fetchApprovedReviews() {
      this.loading = true
      try {
        const res = await getApprovedList()
        this.approvedReviews = res.data || []
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取导入日志
     */
    async fetchLogs() {
      this.loading = true
      try {
        const res = await getImportLogs({
          page: this.logPage,
          per_page: this.logPerPage,
        })
        this.logs = res.data.items || []
        this.logTotal = res.data.total || 0
      } finally {
        this.loading = false
      }
    },

    /**
     * 执行导入到 Neo4j
     */
    async importToNeo4j() {
      if (this.selectedReviewIds.size === 0) return
      this.importing = true
      try {
        const res = await importToNeo4j({
          review_ids: Array.from(this.selectedReviewIds),
        })
        // 导入完成后清空选择并刷新日志
        this.selectedReviewIds = new Set()
        await this.fetchLogs()
        return res
      } finally {
        this.importing = false
      }
    },

    /**
     * 切换审核记录的选中状态
     * @param {number|string} id
     */
    toggleSelection(id) {
      const newSet = new Set(this.selectedReviewIds)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      this.selectedReviewIds = newSet
    },

    /**
     * 全选 / 取消全选
     * @param {boolean} checked
     */
    toggleSelectAll(checked) {
      if (checked) {
        this.selectedReviewIds = new Set(this.approvedReviews.map(r => r.id))
      } else {
        this.selectedReviewIds = new Set()
      }
    },

    /**
     * 日志翻页
     * @param {number} newPage
     */
    handleLogPageChange(newPage) {
      this.logPage = newPage
      return this.fetchLogs()
    },
  },
})
