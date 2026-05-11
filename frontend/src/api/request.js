import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
})

service.interceptors.response.use(
  (response) => {
    // blob 响应直接返回原始 response（用于文件下载）
    if (response.config.responseType === 'blob') {
      const contentType = response.headers['content-type'] || ''
      // 后端返回了 JSON 错误（content-type 是 application/json），解析错误信息
      if (contentType.includes('application/json')) {
        return new Promise((_, reject) => {
          const reader = new FileReader()
          reader.onload = () => {
            try {
              const err = JSON.parse(reader.result)
              ElMessage.error(err.message || '请求失败')
              reject(new Error(err.message))
            } catch {
              ElMessage.error('请求失败')
              reject(new Error('请求失败'))
            }
          }
          reader.readAsText(response.data)
        })
      }
      return response
    }
    const res = response.data
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    // 401 未登录 → 清除状态并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('loggedIn')
      localStorage.removeItem('username')
      if (window.location.hash !== '#/login' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
    // blob 请求的错误响应需要先读取 blob 内容再解析 JSON
    if (error.config?.responseType === 'blob' && error.response?.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const err = JSON.parse(reader.result)
          ElMessage.error(err.message || '请求失败')
        } catch {
          ElMessage.error(error.message || '网络错误')
        }
      }
      reader.readAsText(error.response.data)
      return Promise.reject(error)
    }
    const msg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default service
