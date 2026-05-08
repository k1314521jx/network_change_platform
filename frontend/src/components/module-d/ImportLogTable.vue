<template>
  <el-card shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="card-title">入库日志</span>
        <el-button :icon="Refresh" size="small" @click="load" :loading="loading">刷新</el-button>
      </div>
    </template>
    <el-table :data="items" stripe style="width: 100%" v-loading="loading" size="small" empty-text="暂无日志">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="triple_review_id" label="审核ID" width="90" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
            {{ row.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      <el-table-column label="导入时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
    <div class="pagination-wrap">
      <el-pagination v-model:current-page="page" :page-size="perPage" :total="total" layout="total, prev, pager, next" background small @current-change="handlePageChange" />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { usePagination } from '@/composables/usePagination'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { getImportLogs } from '@/api/neo4j'

const { page, perPage, total, items, loading, load, handlePageChange } = usePagination(getImportLogs)
const { start } = useAutoRefresh((silent) => load(silent), 5000)

onMounted(() => start())

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

defineExpose({ refresh: load })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
