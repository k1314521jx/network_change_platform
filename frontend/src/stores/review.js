import { defineStore } from 'pinia'
import { getPendingList, getApprovedList, getRejectedList, getReviewData, submitReview } from '@/api/review'

export const useReviewStore = defineStore('review', {
  state: () => ({
    /** 待审核列表 */
    pendingList: [],
    /** 已通过列表 */
    approvedList: [],
    /** 已驳回列表 */
    rejectedList: [],
    /** 当前审核详情 */
    currentReview: null,
    /** 编辑区数据：三张表的内容 */
    editData: {
      table1: [],
      table2: [],
      table3: [],
    },
    /** 当前激活的标签页 */
    activeTab: 'pending',
    /** 是否只读模式（已通过/已驳回时为只读） */
    isReadonly: false,
    /** 加载状态 */
    loading: false,
  }),

  actions: {
    /**
     * 获取待审核列表
     */
    async fetchPendingList() {
      this.loading = true
      try {
        const res = await getPendingList()
        this.pendingList = res.data || []
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取已通过列表
     */
    async fetchApprovedList() {
      this.loading = true
      try {
        const res = await getApprovedList()
        this.approvedList = res.data || []
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取已驳回列表
     */
    async fetchRejectedList() {
      this.loading = true
      try {
        const res = await getRejectedList()
        this.rejectedList = res.data || []
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取审核详情并初始化编辑器
     * @param {number|string} tripleTaskId
     * @param {boolean} readonly
     */
    async fetchReview(tripleTaskId, readonly = false) {
      this.loading = true
      try {
        const res = await getReviewData(tripleTaskId)
        this.currentReview = res.data
        this.isReadonly = readonly
        // 初始化编辑数据
        this.editData = {
          table1: (res.data.table1 || []).map(row => ({ ...row })),
          table2: (res.data.table2 || []).map(row => ({ ...row })),
          table3: (res.data.table3 || []).map(row => ({ ...row })),
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * 提交审核结果
     * @param {number|string} tripleTaskId
     * @param {string} reviewStatus - 'approved' | 'rejected'
     * @param {string} reviewer
     */
    async submitReview(tripleTaskId, reviewStatus, reviewer) {
      const res = await submitReview(tripleTaskId, {
        table1: this.editData.table1,
        table2: this.editData.table2,
        table3: this.editData.table3,
        review_status: reviewStatus,
        reviewer,
      })
      // 提交后刷新列表
      await this.fetchPendingList()
      await this.fetchApprovedList()
      await this.fetchRejectedList()
      return res
    },

    /**
     * 在指定表格中添加一行
     * @param {'table1'|'table2'|'table3'} tableKey
     * @param {Object} columns - 列定义，键为字段名，值为默认值
     */
    addRow(tableKey, columns) {
      if (this.isReadonly) return
      this.editData[tableKey].push({ ...columns })
    },

    /**
     * 删除指定表格中的一行
     * @param {'table1'|'table2'|'table3'} tableKey
     * @param {number} rowIndex
     */
    deleteRow(tableKey, rowIndex) {
      if (this.isReadonly) return
      this.editData[tableKey].splice(rowIndex, 1)
    },

    /**
     * 更新指定表格中某个单元格的值
     * @param {'table1'|'table2'|'table3'} tableKey
     * @param {number} rowIndex
     * @param {string} col - 字段名
     * @param {*} value - 新值
     */
    updateCell(tableKey, rowIndex, col, value) {
      if (this.isReadonly) return
      if (this.editData[tableKey][rowIndex]) {
        this.editData[tableKey][rowIndex][col] = value
      }
    },

    /**
     * 重置编辑器数据到初始状态
     */
    resetEditor() {
      if (this.currentReview) {
        this.editData = {
          table1: (this.currentReview.table1 || []).map(row => ({ ...row })),
          table2: (this.currentReview.table2 || []).map(row => ({ ...row })),
          table3: (this.currentReview.table3 || []).map(row => ({ ...row })),
        }
      } else {
        this.editData = { table1: [], table2: [], table3: [] }
      }
    },
  },
})
