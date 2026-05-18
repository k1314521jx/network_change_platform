<template>
  <el-dialog
    v-model="visible"
    title="选择审核通过的数据"
    width="720px"
    :close-on-click-modal="false"
    @open="handleOpen"
  >
    <el-table
      ref="tableRef"
      :data="reviews"
      stripe
      v-loading="loading"
      size="small"
      max-height="400"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="45" />
      <el-table-column prop="id" label="审核ID" width="75" />
      <el-table-column prop="file_name" label="文件名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="reviewer" label="审核人" width="100" />
      <el-table-column label="审核通过时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.review_time) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.imported" type="info" size="small">已入库</el-tag>
          <el-tag v-else type="warning" size="small">待入库</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button
        type="primary"
        :loading="importing"
        :disabled="!selected.length"
        @click="handleImport(false)"
      >
        批量入库 ({{ selected.length }})
      </el-button>
      <el-button
        :loading="reImporting"
        :disabled="!selected.length"
        @click="handleImport(true)"
      >
        重新入库 ({{ selected.length }})
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { getApprovedList } from '@/api/review'
import { importToNeo4j } from '@/api/neo4j'
import { ElMessage } from 'element-plus'

const visible = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['imported'])

const reviews = ref([])
const selected = ref([])
const loading = ref(false)
const importing = ref(false)
const reImporting = ref(false)
const tableRef = ref(null)

async function handleOpen() {
  loading.value = true
  try {
    const res = await getApprovedList()
    reviews.value = res.data || []
  } catch {
    reviews.value = []
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(rows) {
  selected.value = rows
}

async function handleImport(force) {
  if (force) {
    reImporting.value = true
  } else {
    importing.value = true
  }
  try {
    const reviewIds = selected.value.map(r => r.id)
    const res = await importToNeo4j({ review_ids: reviewIds, force })
    ElMessage.success(res.message)
    visible.value = false
    emit('imported')
  } catch {
    // error handled by interceptor
  } finally {
    importing.value = false
    reImporting.value = false
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>
