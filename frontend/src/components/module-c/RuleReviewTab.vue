<template>
  <div class="rule-review-tab">
    <!-- 操作栏 -->
    <el-card shadow="never" class="action-card">
      <div class="action-bar">
        <el-button type="primary" :disabled="!selectedIds.length" :loading="batchLoading" @click="handleBatchValidate">
          批量验证（{{ selectedIds.length }} 条）
        </el-button>
        <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never" style="margin-top: 12px;">
      <el-table :data="tasks" stripe size="small" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" :selectable="row => row.status !== 'validating'" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="rule_task_id" label="关联规则ID" width="110" />
        <el-table-column prop="rule_filename" label="规则文件名" show-overflow-tooltip />
        <el-table-column prop="model" label="模型" width="120" />
        <el-table-column label="验证状态" width="100">
          <template #default="{ row }">
            <el-tag :type="validationStatusMap[row.status]?.type" size="small">
              {{ validationStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="row.status !== 'validating'"
              link type="success" size="small"
              @click="handleValidate(row)"
            >验证</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > 0"
        style="margin-top: 12px; justify-content: flex-end;"
        :current-page="page"
        :page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="三元组详情" width="80%" destroy-on-close>
      <template v-if="detailTask">
        <div class="detail-header">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="任务ID">{{ detailTask.id }}</el-descriptions-item>
            <el-descriptions-item label="验证状态">
              <el-tag :type="validationStatusMap[detailTask.validation_status]?.type" size="small">
                {{ validationStatusMap[detailTask.validation_status]?.label || detailTask.validation_status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(detailTask.created_at) }}</el-descriptions-item>
          </el-descriptions>
          <el-button type="primary" plain size="small" :loading="exporting" @click="handleExportThinking">
            导出思考
          </el-button>
        </div>

        <!-- 违规摘要 -->
        <template v-if="detailTask.validation_status === 'unqualified' && detailTask.validation_result">
          <div class="violation-summary" style="margin-top: 12px;">
            <div class="violation-summary-title">校验未通过，共 {{ detailViolations.length }} 项违规</div>
            <div v-for="v in detailViolations" :key="v.rule + v.level" class="violation-item">
              <span class="violation-badge" :style="{ backgroundColor: v.color + '22', color: v.color, border: `1px solid ${v.color}` }">
                规则{{ v.rule }} · {{ v.level }}
              </span>
              <span class="violation-msg">{{ v.message }}</span>
            </div>
          </div>
        </template>

        <!-- 表格区域 -->
        <el-tabs v-if="detailTask.triple_json" v-model="detailActiveTab" class="detail-tabs">
          <el-tab-pane label="Table1_Alignment" name="table1">
            <ReadonlyTable :data="detailTableData.table1" :columns="table1Cols" :violations="detailViolations" tableName="Table1_Alignment" />
          </el-tab-pane>
          <el-tab-pane label="Table2_Entities_Attributes" name="table2">
            <ReadonlyTable :data="detailTableData.table2" :columns="table2Cols" :violations="detailViolations" tableName="Table2_Entities_Attributes" />
          </el-tab-pane>
          <el-tab-pane label="Table3_Relations" name="table3">
            <ReadonlyTable :data="detailTableData.table3" :columns="table3Cols" :violations="detailViolations" tableName="Table3_Relations" />
          </el-tab-pane>
          <el-tab-pane label="原始JSON" name="raw">
            <JsonPreview :data="detailTask.triple_json" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getRuleValidationList, getRuleValidationDetail, validateRule, batchValidateRules } from '@/api/ruleValidation'
import { exportThinking } from '@/api/triple'
import ReadonlyTable from '@/components/module-b/ReadonlyTable.vue'
import JsonPreview from '@/components/common/JsonPreview.vue'

const validationStatusMap = {
  pending: { label: '待验证', type: 'warning' },
  validating: { label: '验证中', type: 'primary' },
  passed: { label: '合格', type: 'success' },
  unqualified: { label: '不合格', type: 'danger' },
}

const table1Cols = ['row_index', 'raw_cmd', 'raw_rollback', 'step_name', 'au_name', 'role', 'entity', 'parameters']
const table2Cols = ['id', 'label', 'name', 'properties']
const table3Cols = ['source_entity', 'relation_type', 'target_entity', 'relation_attributes']

const tasks = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const selectedIds = ref([])
const batchLoading = ref(false)

// 详情
const detailVisible = ref(false)
const detailTask = ref(null)
const detailActiveTab = ref('table1')
const exporting = ref(false)

// 自动刷新（验证中时轮询）
let refreshTimer = null

async function loadTasks() {
  loading.value = true
  try {
    const res = await getRuleValidationList({ page: page.value, per_page: perPage })
    tasks.value = res.data.items || []
    total.value = res.data.total || 0
    startAutoRefresh()
  } catch {} finally {
    loading.value = false
  }
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  const hasValidating = tasks.value.some(t => t.status === 'validating')
  if (hasValidating) {
    refreshTimer = setInterval(() => {
      getRuleValidationList({ page: page.value, per_page: perPage }).then(res => {
        tasks.value = res.data.items || []
        total.value = res.data.total || 0
        if (!tasks.value.some(t => t.status === 'validating')) {
          clearInterval(refreshTimer)
          refreshTimer = null
        }
      }).catch(() => {})
    }, 5000)
  }
}

function handlePageChange(p) {
  page.value = p
  loadTasks()
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

async function handleValidate(row) {
  try {
    await validateRule(row.id)
    ElMessage.success('验证任务已触发')
    loadTasks()
  } catch {}
}

async function handleBatchValidate() {
  batchLoading.value = true
  try {
    const res = await batchValidateRules(selectedIds.value)
    ElMessage.success(res.message || '批量验证已触发')
    selectedIds.value = []
    loadTasks()
  } catch {} finally {
    batchLoading.value = false
  }
}

async function openDetail(row) {
  try {
    const res = await getRuleValidationDetail(row.id)
    detailTask.value = res.data
    detailActiveTab.value = 'table1'
    detailVisible.value = true
  } catch {}
}

const detailViolations = computed(() => {
  return detailTask.value?.validation_result?.violations || []
})

const detailTableData = computed(() => {
  const json = detailTask.value?.triple_json || {}
  return {
    table1: json.Table1_Alignment || [],
    table2: json.Table2_Entities_Attributes || [],
    table3: json.Table3_Relations || [],
  }
})

async function handleExportThinking() {
  if (!detailTask.value) return
  exporting.value = true
  try {
    const resp = await exportThinking(detailTask.value.id)
    const blob = resp.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `thinking_task_${detailTask.value.id}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch {} finally {
    exporting.value = false
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

onMounted(() => loadTasks())
</script>

<style scoped>
.action-card :deep(.el-card__body) { padding: 12px 16px; }
.action-bar { display: flex; gap: 12px; align-items: center; }
.detail-header { display: flex; align-items: flex-start; justify-content: space-between; }
.detail-header .el-descriptions { flex: 1; }
.detail-tabs { margin-top: 16px; }
.violation-summary {
  border: 1px solid #EBEEF5;
  border-radius: 6px;
  padding: 12px 16px;
}
.violation-summary-title { font-weight: 600; margin-bottom: 10px; color: #303133; }
.violation-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.violation-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}
.violation-msg { font-size: 13px; color: #606266; }
</style>
