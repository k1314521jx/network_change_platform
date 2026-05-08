import { defineStore } from 'pinia'
import { uploadExcel, getRuleTasks, getRuleTask, retryRuleTask, getSuccessRuleTasks } from '@/api/rule'

export const useRuleStore = defineStore('rule', {
  state: () => ({
    /** 规则任务列表 */
    tasks: [],
    /** 任务总数 */
    total: 0,
    /** 当前页码 */
    page: 1,
    /** 每页条数 */
    perPage: 15,
    /** 搜索关键词 */
    search: '',
    /** 当前查看的任务详情 */
    currentTask: null,
    /** 加载状态 */
    loading: false,
  }),

  actions: {
    /**
     * 获取规则任务列表
     */
    async fetchTasks() {
      this.loading = true
      try {
        const res = await getRuleTasks({
          page: this.page,
          per_page: this.perPage,
          filename: this.search,
        })
        this.tasks = res.data.items || []
        this.total = res.data.total || 0
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取单个规则任务详情
     * @param {number|string} id
     */
    async fetchTask(id) {
      this.loading = true
      try {
        const res = await getRuleTask(id)
        this.currentTask = res.data
      } finally {
        this.loading = false
      }
    },

    /**
     * 重试失败的规则任务
     * @param {number|string} id
     */
    async retryTask(id) {
      const res = await retryRuleTask(id)
      // 重试后刷新列表
      await this.fetchTasks()
      return res
    },

    /**
     * 上传 Excel 文件
     * @param {FormData} formData
     */
    async uploadExcel(formData) {
      const res = await uploadExcel(formData)
      // 上传后刷新列表
      await this.fetchTasks()
      return res
    },

    /**
     * 获取所有成功的规则任务（供三元组模块使用）
     * @returns {Array}
     */
    async fetchSuccessTasks() {
      const res = await getSuccessRuleTasks()
      return res.data || []
    },

    /**
     * 切换页码
     * @param {number} newPage
     */
    handlePageChange(newPage) {
      this.page = newPage
      return this.fetchTasks()
    },

    /**
     * 搜索
     */
    handleSearch() {
      this.page = 1
      return this.fetchTasks()
    },
  },
})
