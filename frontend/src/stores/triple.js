import { defineStore } from 'pinia'
import { convertToTriple, getTripleTasks, getTripleTask } from '@/api/triple'
import { getSuccessRuleTasks } from '@/api/rule'

export const useTripleStore = defineStore('triple', {
  state: () => ({
    /** 三元组任务列表 */
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
    /** 成功的规则任务列表（供转换时选择） */
    successRuleTasks: [],
    /** 是否正在转换 */
    converting: false,
    /** 加载状态 */
    loading: false,
  }),

  actions: {
    /**
     * 获取三元组任务列表
     */
    async fetchTasks() {
      this.loading = true
      try {
        const res = await getTripleTasks({
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
     * 获取单个三元组任务详情
     * @param {number|string} id
     */
    async fetchTask(id) {
      this.loading = true
      try {
        const res = await getTripleTask(id)
        this.currentTask = res.data
      } finally {
        this.loading = false
      }
    },

    /**
     * 执行三元组转换
     * @param {{ rule_task_id: number|string, model: string }} data
     */
    async convert(data) {
      this.converting = true
      try {
        const res = await convertToTriple(data)
        // 转换完成后刷新列表
        await this.fetchTasks()
        return res
      } finally {
        this.converting = false
      }
    },

    /**
     * 获取成功的规则任务列表（用于转换时选择源任务）
     */
    async fetchSuccessRuleTasks() {
      const res = await getSuccessRuleTasks()
      this.successRuleTasks = res.data || []
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
