<template>
  <el-card shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="card-title">三元组任务列表</span>
        <div class="header-actions">
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 110px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="处理中" value="pending" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-select v-model="modelFilter" placeholder="模型" clearable style="width: 130px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
          </el-select>
          <el-input v-model="search" placeholder="按规则文件名搜索..." :prefix-icon="Search" clearable style="width: 220px;" @keyup.enter="handleSearch" @clear="handleSearch" />
        </div>
      </div>
    </template>
    <el-table :data="items" stripe style="width: 100%" v-loading="loading" empty-text="暂无数据">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="rule_task_id" label="关联规则ID" width="110" />
      <el-table-column prop="rule_filename" label="规则文件名" show-overflow-tooltip />
      <el-table-column prop="model" label="模型" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status).type" :color="getStatusTag(row.status).color" size="small" style="border:none;">{{ getStatusTag(row.status).label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="emit('viewDetail', row.id)">详情</el-button>
          <el-button v-if="row.status === 'failed'" type="warning" link size="small" @click="handleRetry(row)">重试</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-wrap">
      <el-pagination v-model:current-page="page" v-model:page-size="perPage" :page-sizes="[10, 20, 50]" :total="total" layout="total, sizes, prev, pager, next, jumper" background @current-change="handlePageChange" @size-change="load" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePagination } from '@/composables/usePagination'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useStatusTag } from '@/composables/useStatusTag'
import { getTripleTasks, retryTripleTask } from '@/api/triple'
import { getModelOptions } from '@/api/model'

const emit = defineEmits(['viewDetail'])
const { getStatusTag } = useStatusTag()

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const statusFilter = ref('')
const modelFilter = ref('')
const modelOptions = ref([])

const { page, perPage, total, search, items, loading, load, handlePageChange, handleSearch, extraParams } = usePagination(getTripleTasks)

function handleFilterChange() {
  const params = {}
  if (statusFilter.value) params.status = statusFilter.value
  if (modelFilter.value) params.model = modelFilter.value
  extraParams.value = params
  page.value = 1
  load()
}

async function handleRetry(row) {
  try {
    await ElMessageBox.confirm('确定要重试此转换任务吗？', '重试确认', { type: 'warning' })
    await retryTripleTask(row.id)
    ElMessage.success('重试已触发')
    load()
  } catch { /* cancelled */ }
}

async function loadModelOptions() {
  try {
    const res = await getModelOptions()
    const existing = new Set(items.value.map(i => i.model).filter(Boolean))
    const fromConfig = (res.data || []).map(m => m.name)
    modelOptions.value = [...new Set([...fromConfig, ...existing])]
  } catch {}
}

const { start } = useAutoRefresh((silent) => { load(silent); loadModelOptions() }, 5000)

onMounted(() => {
  start()
  loadModelOptions()
})

defineExpose({ refresh: load })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
