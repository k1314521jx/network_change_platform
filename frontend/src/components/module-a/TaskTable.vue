<template>
  <el-card shadow="hover" class="task-table-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">规则任务列表</span>
        <div class="header-filters">
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="处理中" value="pending" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-input
            v-model="search"
            placeholder="搜索文件名"
            :prefix-icon="Search"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </div>
      </div>
    </template>

    <el-table
      v-loading="loading"
      :data="items"
      stripe
      border
      style="width: 100%"
      empty-text="暂无任务数据"
    >
      <el-table-column prop="id" label="ID" width="80" align="center" />
      <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status).type" size="small" effect="light">
            {{ getStatusTag(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" align="center" />
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="$emit('view-detail', row.id)">
            详情
          </el-button>
          <el-button
            v-if="row.status === 'failed'"
            type="warning"
            link
            size="small"
            @click="handleRetry(row.id)"
          >
            重试
          </el-button>
          <el-button
            v-if="row.status === 'failed'"
            type="danger"
            link
            size="small"
            @click="handleDelete(row.id)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="handlePageChange"
        @size-change="load"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useStatusTag } from '@/composables/useStatusTag'
import { usePagination } from '@/composables/usePagination'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { getRuleTasks, retryRuleTask, deleteRuleTask } from '@/api/rule'

const emit = defineEmits(['view-detail'])

const { getStatusTag } = useStatusTag()

const statusFilter = ref('')

const {
  page,
  perPage,
  total,
  search,
  items,
  loading,
  load,
  handlePageChange,
  handleSearch,
  extraParams,
} = usePagination(getRuleTasks)

function handleFilterChange() {
  const params = {}
  if (statusFilter.value) params.status = statusFilter.value
  extraParams.value = params
  page.value = 1
  load()
}

async function handleRetry(id) {
  try {
    await ElMessageBox.confirm('确定要重试该任务吗？', '确认重试', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await retryRuleTask(id)
    ElMessage.success('重试任务已提交')
    load()
  } catch {
    // 用户取消
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？删除后不可恢复。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteRuleTask(id)
    ElMessage.success('删除成功')
    load()
  } catch {
    // 用户取消
  }
}

function refresh() {
  load()
}

const { start } = useAutoRefresh((silent) => load(silent), 5000)

onMounted(() => start())

defineExpose({ refresh })
</script>

<style scoped>
.task-table-card {
  min-height: 400px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-filters {
  display: flex;
  gap: 8px;
  align-items: center;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
