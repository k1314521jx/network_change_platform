<template>
  <div class="pipeline">
    <!-- 顶部流程指示 -->
    <div class="pipeline-header">
      <div class="step" :class="{ active: true }">
        <div class="step-num">1</div>
        <div class="step-label">规则审核</div>
      </div>
      <div class="step-arrow">→</div>
      <div class="step" :class="{ active: true }">
        <div class="step-num">2</div>
        <div class="step-label">AI 审核</div>
      </div>
      <div class="step-arrow">→</div>
      <div class="step" :class="{ active: true }">
        <div class="step-num">3</div>
        <div class="step-label">人工审核</div>
      </div>
    </div>

    <!-- 三列管道 -->
    <div class="pipeline-columns">
      <!-- 列1：规则审核 -->
      <div class="pipeline-col">
        <div class="col-header">
          <span class="col-title">规则审核</span>
          <el-tag size="small" type="info">{{ filteredRuleTasks.length }} 条</el-tag>
          <div class="col-actions">
            <el-button type="primary" size="small" :disabled="!selectedRuleIds.length" :loading="batchValidating" @click="handleBatchValidate">
              批量验证({{ selectedRuleIds.length }})
            </el-button>
          </div>
        </div>
        <div class="col-filter">
          <span
            v-for="f in ruleFilters" :key="f.value"
            class="filter-tag" :class="{ active: ruleFilter === f.value }"
            @click="ruleFilter = f.value"
          >{{ f.label }}</span>
        </div>
        <div class="col-body" v-loading="ruleLoading">
          <div v-if="!filteredRuleTasks.length" class="empty-tip">暂无数据</div>
          <div
            v-for="item in filteredRuleTasks"
            :key="item.id"
            class="pipeline-card"
            :class="{ selected: selectedRuleIds.includes(item.id) }"
            @click.self="toggleRuleSelect(item)"
          >
            <div class="card-top">
              <el-checkbox
                :model-value="selectedRuleIds.includes(item.id)"
                @change="toggleRuleSelect(item)"
                @click.stop
                size="small"
              />
              <span class="card-id">#{{ item.id }}</span>
              <el-tag size="small" :type="ruleStatusMap[item.status]?.type">
                {{ ruleStatusMap[item.status]?.label || item.status }}
              </el-tag>
            </div>
            <div class="card-info">
              <div class="card-row"><span class="card-label">文件:</span> {{ item.rule_filename }}</div>
              <div class="card-row"><span class="card-label">模型:</span> {{ item.model }}</div>
              <div class="card-row"><span class="card-label">时间:</span> {{ formatDT(item.created_at) }}</div>
            </div>
            <div class="card-actions">
              <el-button link type="primary" size="small" @click="openRuleDetail(item)">详情</el-button>
              <el-button
                v-if="item.status !== 'validating' && item.status !== 'passed'"
                link type="success" size="small"
                @click="handleValidate(item)"
              >验证</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 列间箭头 -->
      <div class="col-divider"><span class="divider-arrow">›</span></div>

      <!-- 列2：AI审核 -->
      <div class="pipeline-col">
        <div class="col-header">
          <span class="col-title">AI 审核</span>
          <el-tag size="small" type="info">{{ filteredAiTasks.length }} 条</el-tag>
          <div class="col-actions">
            <el-select v-model="aiModel" placeholder="模型" size="small" style="width: 120px;">
              <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.name" />
            </el-select>
            <el-select v-model="aiPromptId" placeholder="提示词" clearable size="small" style="width: 120px;">
              <el-option v-for="p in promptOptions" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
        </div>
        <div class="col-filter">
          <span
            v-for="f in aiFilters" :key="f.value"
            class="filter-tag" :class="{ active: aiFilter === f.value }"
            @click="aiFilter = f.value"
          >{{ f.label }}</span>
        </div>
        <div class="col-body" v-loading="aiLoading">
          <div v-if="!filteredAiTasks.length" class="empty-tip">暂无数据</div>
          <div v-for="item in filteredAiTasks" :key="item.id" class="pipeline-card">
            <div class="card-top">
              <span class="card-id">#{{ item.id }}</span>
              <el-tag size="small" :type="aiStatusMap[item.status]?.type">
                {{ aiStatusMap[item.status]?.label || item.status }}
              </el-tag>
            </div>
            <div class="card-info">
              <div class="card-row"><span class="card-label">任务:</span> #{{ item.triple_task_id }}</div>
              <div class="card-row"><span class="card-label">文件:</span> {{ item.rule_filename }}</div>
              <div v-if="item.score != null" class="card-row">
                <span class="card-label">得分:</span>
                <span :style="{ color: getScoreColor(item.score), fontWeight: 600 }">{{ item.score }}</span>
              </div>
              <div class="card-row"><span class="card-label">模型:</span> {{ item.model }}</div>
            </div>
            <div class="card-actions">
              <el-button link type="primary" size="small" @click="openAiDetail(item)">详情</el-button>
              <el-button
                v-if="item.status === 'failed'"
                link type="warning" size="small"
                @click="handleAiRetry(item)"
              >重试</el-button>
              <el-button
                v-if="item.status === 'pending'"
                link type="success" size="small"
                @click="handleAiCreate(item)"
              >审核</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 列间箭头 -->
      <div class="col-divider"><span class="divider-arrow">›</span></div>

      <!-- 列3：人工审核 -->
      <div class="pipeline-col">
        <div class="col-header">
          <span class="col-title">人工审核</span>
          <el-tag size="small" type="info">{{ filteredHumanTasks.length }} 条</el-tag>
        </div>
        <div class="col-filter">
          <span
            v-for="f in humanFilters" :key="f.value"
            class="filter-tag" :class="{ active: humanFilter === f.value }"
            @click="humanFilter = f.value"
          >{{ f.label }}</span>
        </div>
        <div class="col-body" v-loading="humanLoading">
          <div v-if="!filteredHumanTasks.length" class="empty-tip">暂无数据</div>
          <div v-for="item in filteredHumanTasks" :key="item.id" class="pipeline-card">
            <div class="card-top">
              <span class="card-id">#{{ item.id }}</span>
              <el-tag v-if="item.review_status" size="small" :type="item.review_status === 'approved' ? 'success' : item.review_status === 'rejected' ? 'danger' : 'warning'">
                {{ item.review_status === 'approved' ? '已通过' : item.review_status === 'rejected' ? '已驳回' : '待审核' }}
              </el-tag>
            </div>
            <div class="card-info">
              <div class="card-row"><span class="card-label">文件:</span> {{ item.rule_filename }}</div>
            </div>
            <div class="card-actions">
              <el-button link type="primary" size="small" @click="openHumanDetail(item)">审核</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 规则审核详情弹窗 -->
    <el-dialog v-model="ruleDetailVisible" width="80%" :fullscreen="ruleDetailFullscreen" destroy-on-close>
      <template #header>
        <div class="dialog-header-bar">
          <span>规则审核详情</span>
          <el-button link @click="ruleDetailFullscreen = !ruleDetailFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>
      </template>
      <template v-if="ruleDetailData">
        <div class="detail-header">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="任务ID">{{ ruleDetailData.id }}</el-descriptions-item>
            <el-descriptions-item label="验证状态">
              <el-tag size="small" :type="ruleStatusMap[ruleDetailData.validation_status]?.type">
                {{ ruleStatusMap[ruleDetailData.validation_status]?.label }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDT(ruleDetailData.created_at) }}</el-descriptions-item>
          </el-descriptions>
          <el-button type="primary" plain size="small" :loading="exporting" @click="handleExportThinking(ruleDetailData.id)">
            导出思考
          </el-button>
        </div>
        <template v-if="ruleDetailData.validation_status === 'unqualified' && ruleDetailData.validation_result">
          <div class="violation-summary" style="margin-top: 12px;">
            <div class="violation-summary-title">校验未通过，共 {{ ruleViolations.length }} 项违规</div>
            <div v-for="v in ruleViolations" :key="v.rule + v.level" class="violation-item">
              <span class="violation-badge" :style="{ backgroundColor: v.color + '22', color: v.color, border: `1px solid ${v.color}` }">
                规则{{ v.rule }} · {{ v.level }}
              </span>
              <span class="violation-msg">{{ v.message }}</span>
            </div>
          </div>
        </template>
        <el-tabs v-if="ruleDetailData.triple_json" v-model="detailActiveTab" class="detail-tabs">
          <el-tab-pane label="Table1" name="t1">
            <EditableSheetTable v-if="isRuleUnqualified && !errorOnlyT1" v-model="editableRuleData.table1" :columns="t1Cols" :violations="ruleViolations" tableName="Table1_Alignment" :maxHeight="detailTableHeight" :showErrorToggle="true" v-model:errorOnly="errorOnlyT1" />
            <ReadonlyTable v-else :data="errorOnlyT1 && isRuleUnqualified ? errorFilteredData.table1 : ruleTableData.table1" :columns="t1Cols" :violations="ruleViolations" tableName="Table1_Alignment" :maxHeight="detailTableHeight" />
          </el-tab-pane>
          <el-tab-pane label="Table2" name="t2">
            <EditableSheetTable v-if="isRuleUnqualified && !errorOnlyT2" v-model="editableRuleData.table2" :columns="t2Cols" :violations="ruleViolations" tableName="Table2_Entities_Attributes" :maxHeight="detailTableHeight" :showErrorToggle="true" v-model:errorOnly="errorOnlyT2" />
            <ReadonlyTable v-else :data="errorOnlyT2 && isRuleUnqualified ? errorFilteredData.table2 : ruleTableData.table2" :columns="t2Cols" :violations="ruleViolations" tableName="Table2_Entities_Attributes" :maxHeight="detailTableHeight" />
          </el-tab-pane>
          <el-tab-pane label="Table3" name="t3">
            <EditableSheetTable v-if="isRuleUnqualified && !errorOnlyT3" v-model="editableRuleData.table3" :columns="t3Cols" :violations="ruleViolations" tableName="Table3_Relations" :maxHeight="detailTableHeight" :showErrorToggle="true" v-model:errorOnly="errorOnlyT3" />
            <ReadonlyTable v-else :data="errorOnlyT3 && isRuleUnqualified ? errorFilteredData.table3 : ruleTableData.table3" :columns="t3Cols" :violations="ruleViolations" tableName="Table3_Relations" :maxHeight="detailTableHeight" />
          </el-tab-pane>
          <el-tab-pane label="JSON" name="raw">
            <JsonPreview :data="ruleDetailData.triple_json" />
          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer v-if="isRuleUnqualified">
        <el-button type="primary" :loading="saveAndValidating" @click="handleSaveAndRevalidate">
          确定并重新验证
        </el-button>
      </template>
    </el-dialog>

    <!-- AI审核详情弹窗 -->
    <AiReviewDetailDialog v-model="aiDetailVisible" :review="aiDetailData" />

    <!-- 人工审核弹窗 -->
    <el-dialog v-model="humanDetailVisible" width="80%" :fullscreen="humanDetailFullscreen" destroy-on-close>
      <template #header>
        <div class="dialog-header-bar">
          <span>人工审核 #{{ humanDetailTaskId }}</span>
          <el-button link @click="humanDetailFullscreen = !humanDetailFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>
      </template>
      <template v-if="humanDetailData">
        <div style="margin-bottom: 12px;">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="任务ID">{{ humanDetailTaskId }}</el-descriptions-item>
            <el-descriptions-item label="文件">{{ humanDetailData.rule_filename || '' }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <el-collapse v-if="humanDetailData.ai_review" style="margin-bottom: 12px;">
          <el-collapse-item :title="`AI 审核结果（得分: ${humanDetailData.ai_review.score}）`">
            <div style="font-size: 13px; color: #606266; white-space: pre-wrap;">{{ humanDetailData.ai_review.summary }}</div>
          </el-collapse-item>
        </el-collapse>
        <TripleEditor
          v-if="humanEditData"
          :editData="humanEditData"
          :currentTaskId="humanDetailTaskId"
          :reviewStatus="humanDetailData?.review_status"
          @submit="handleHumanSubmit"
        />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import { getRuleValidationList, getRuleValidationDetail, validateRule, batchValidateRules } from '@/api/ruleValidation'
import { getAiReviewList, getAiReviewDetail, createAiReview, retryAiReview, startAiReview } from '@/api/aiReview'
import { getPendingList, getReviewData, submitReview } from '@/api/review'
import { getModelOptions } from '@/api/model'
import { getPromptOptions } from '@/api/prompt'
import { exportThinking, updateAndValidate } from '@/api/triple'
import ReadonlyTable from '@/components/module-b/ReadonlyTable.vue'
import EditableSheetTable from '@/components/module-c/EditableSheetTable.vue'
import JsonPreview from '@/components/common/JsonPreview.vue'
import AiReviewDetailDialog from '@/components/module-c/AiReviewDetailDialog.vue'
import TripleEditor from '@/components/module-c/TripleEditor.vue'

// ---- 状态映射 ----
const ruleStatusMap = {
  pending: { label: '待验证', type: 'warning' },
  validating: { label: '验证中', type: 'primary' },
  passed: { label: '合格', type: 'success' },
  unqualified: { label: '不合格', type: 'danger' },
}
const aiStatusMap = {
  pending: { label: '待审核', type: 'warning' },
  reviewing: { label: '审核中', type: 'primary' },
  reviewed: { label: '已审核', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

const t1Cols = ['row_index', 'raw_cmd', 'raw_rollback', 'step_name', 'au_name', 'role', 'entity', 'parameters']
const t2Cols = ['id', 'label', 'name', 'properties']
const t3Cols = ['source_entity', 'relation_type', 'target_entity', 'relation_attributes']

// ---- 状态筛选配置 ----
const ruleFilters = [
  { label: '全部', value: 'all' },
  { label: '待验证', value: 'pending' },
  { label: '合格', value: 'passed' },
  { label: '不合格', value: 'unqualified' },
]
const aiFilters = [
  { label: '全部', value: 'all' },
  { label: '待审核', value: 'pending_review' },
  { label: '审核中', value: 'reviewing' },
  { label: '已审核', value: 'reviewed' },
]
const humanFilters = [
  { label: '全部', value: 'all' },
  { label: '待审核', value: 'pending_review' },
  { label: '通过', value: 'approved' },
  { label: '驳回', value: 'rejected' },
]

const ruleFilter = ref('all')
const aiFilter = ref('all')
const humanFilter = ref('all')

const detailTableHeight = computed(() => ruleDetailFullscreen.value ? window.innerHeight - 280 : 450)

// ---- 列1：规则审核 ----
const ruleTasks = ref([])
const ruleLoading = ref(false)
const selectedRuleIds = ref([])
const batchValidating = ref(false)

const ruleDetailVisible = ref(false)
const ruleDetailData = ref(null)
const detailActiveTab = ref('t1')
const exporting = ref(false)
const ruleDetailFullscreen = ref(false)

const isRuleUnqualified = computed(() => ruleDetailData.value?.validation_status === 'unqualified')

// 不合格时的可编辑数据
const editableRuleData = ref({ table1: [], table2: [], table3: [] })
const errorOnlyT1 = ref(false)
const errorOnlyT2 = ref(false)
const errorOnlyT3 = ref(false)
const saveAndValidating = ref(false)

const filteredRuleTasks = computed(() => {
  if (ruleFilter.value === 'all') return ruleTasks.value
  return ruleTasks.value.filter(t => t.status === ruleFilter.value)
})

async function loadRuleTasks(silent = false) {
  if (!silent) ruleLoading.value = true
  try {
    const res = await getRuleValidationList({ page: 1, per_page: 50 })
    ruleTasks.value = res.data.items || []
  } catch {} finally {
    if (!silent) ruleLoading.value = false
  }
}

function toggleRuleSelect(item) {
  const idx = selectedRuleIds.value.indexOf(item.id)
  if (idx >= 0) selectedRuleIds.value.splice(idx, 1)
  else selectedRuleIds.value.push(item.id)
}

async function handleValidate(item) {
  try {
    await validateRule(item.id)
    ElMessage.success('验证已触发')
    loadRuleTasks()
  } catch {}
}

async function handleBatchValidate() {
  batchValidating.value = true
  try {
    const res = await batchValidateRules(selectedRuleIds.value)
    ElMessage.success(res.message || '批量验证已触发')
    selectedRuleIds.value = []
    loadRuleTasks()
  } catch {} finally {
    batchValidating.value = false
  }
}

async function openRuleDetail(item) {
  try {
    const res = await getRuleValidationDetail(item.id)
    ruleDetailData.value = res.data
    detailActiveTab.value = 't1'
    ruleDetailFullscreen.value = false
    errorOnlyT1.value = false
    errorOnlyT2.value = false
    errorOnlyT3.value = false
    if (res.data.validation_status === 'unqualified') {
      const json = res.data.triple_json || {}
      editableRuleData.value = {
        table1: JSON.parse(JSON.stringify(json.Table1_Alignment || [])),
        table2: JSON.parse(JSON.stringify(json.Table2_Entities_Attributes || [])),
        table3: JSON.parse(JSON.stringify(json.Table3_Relations || [])),
      }
    }
    ruleDetailVisible.value = true
  } catch {}
}

const ruleViolations = computed(() => ruleDetailData.value?.validation_result?.violations || [])
const ruleTableData = computed(() => {
  const json = ruleDetailData.value?.triple_json || {}
  return { table1: json.Table1_Alignment || [], table2: json.Table2_Entities_Attributes || [], table3: json.Table3_Relations || [] }
})

function getErrorRowIndices(tableName) {
  const indices = new Set()
  for (const v of ruleViolations.value) {
    for (const loc of (v.locations || [])) {
      if (loc.table === tableName) indices.add(loc.row_index)
    }
  }
  return indices
}

const errorFilteredData = computed(() => {
  const tables = [
    { key: 'table1', name: 'Table1_Alignment' },
    { key: 'table2', name: 'Table2_Entities_Attributes' },
    { key: 'table3', name: 'Table3_Relations' },
  ]
  const result = {}
  for (const { key, name } of tables) {
    const indices = getErrorRowIndices(name)
    result[key] = ruleTableData.value[key].filter((row, i) => indices.has(row.row_index ?? (i + 1)))
  }
  return result
})

async function handleSaveAndRevalidate() {
  saveAndValidating.value = true
  try {
    await updateAndValidate(ruleDetailData.value.id, {
      table1: editableRuleData.value.table1,
      table2: editableRuleData.value.table2,
      table3: editableRuleData.value.table3,
    })
    ElMessage.success('已保存并触发重新验证')
    ruleDetailVisible.value = false
    loadRuleTasks()
  } catch {} finally {
    saveAndValidating.value = false
  }
}

async function handleExportThinking(taskId) {
  exporting.value = true
  try {
    const resp = await exportThinking(taskId)
    const blob = resp.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `thinking_task_${taskId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch {} finally {
    exporting.value = false
  }
}

// ---- 列2：AI审核 ----
const aiTasks = ref([])
const aiLoading = ref(false)
const aiModel = ref('')
const aiPromptId = ref(null)
const modelOptions = ref([])
const promptOptions = ref([])
const aiDetailVisible = ref(false)
const aiDetailData = ref(null)

const filteredAiTasks = computed(() => {
  if (aiFilter.value === 'all') return aiTasks.value
  if (aiFilter.value === 'pending_review') return aiTasks.value.filter(t => t.status === 'pending' || t.status === 'failed')
  if (aiFilter.value === 'reviewing') return aiTasks.value.filter(t => t.status === 'reviewing')
  return aiTasks.value.filter(t => t.status === aiFilter.value)
})

async function loadAiTasks(silent = false) {
  if (!silent) aiLoading.value = true
  try {
    const res = await getAiReviewList({ page: 1, per_page: 50 })
    aiTasks.value = res.data.items || []
  } catch {} finally {
    if (!silent) aiLoading.value = false
  }
}

async function openAiDetail(item) {
  try {
    const res = await getAiReviewDetail(item.id)
    aiDetailData.value = res.data
    aiDetailVisible.value = true
  } catch {}
}

async function handleAiRetry(item) {
  try {
    await retryAiReview(item.id)
    ElMessage.success('重试已触发')
    loadAiTasks()
  } catch {}
}

async function handleAiCreate(item) {
  try {
    if (item.status === 'pending') {
      await startAiReview(item.id, { model: aiModel.value, prompt_id: aiPromptId.value })
    } else {
      await createAiReview({ triple_task_id: item.triple_task_id, model: aiModel.value, prompt_id: aiPromptId.value })
    }
    // 立即更新本地状态为 reviewing，避免等轮询
    item.status = 'reviewing'
    ElMessage.success('AI审核已触发')
  } catch {}
}

function getScoreColor(score) {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// ---- 列3：人工审核 ----
const humanTasks = ref([])
const humanLoading = ref(false)
const humanDetailVisible = ref(false)
const humanDetailFullscreen = ref(false)
const humanDetailTaskId = ref(null)
const humanDetailData = ref(null)
const humanEditData = ref(null)

const filteredHumanTasks = computed(() => {
  if (humanFilter.value === 'all') return humanTasks.value
  if (humanFilter.value === 'pending_review') return humanTasks.value.filter(t => !t.review_status)
  return humanTasks.value.filter(t => t.review_status === humanFilter.value)
})

async function loadHumanTasks(silent = false) {
  if (!silent) humanLoading.value = true
  try {
    const res = await getPendingList()
    humanTasks.value = res.data || []
  } catch {} finally {
    if (!silent) humanLoading.value = false
  }
}

async function openHumanDetail(item) {
  humanDetailTaskId.value = item.id
  humanDetailFullscreen.value = false
  try {
    const res = await getReviewData(item.id)
    humanDetailData.value = { ...res.data, rule_filename: item.rule_filename }
    humanEditData.value = {
      table1: res.data.table1 || [],
      table2: res.data.table2 || [],
      table3: res.data.table3 || [],
    }
    humanDetailVisible.value = true
  } catch {}
}

async function handleHumanSubmit(reviewStatus) {
  try {
    await submitReview(humanDetailTaskId.value, {
      table1: humanEditData.value.table1,
      table2: humanEditData.value.table2,
      table3: humanEditData.value.table3,
      review_status: reviewStatus,
      reviewer: '',
    })
    ElMessage.success('审核提交成功')
    humanDetailVisible.value = false
    loadHumanTasks()
  } catch {}
}

// ---- 公共 ----
function formatDT(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ---- 自动刷新（静默，不触发 loading） ----
let timer = null
function startAutoRefresh() {
  timer = setInterval(() => {
    loadRuleTasks(true)
    loadAiTasks(true)
    loadHumanTasks(true)
  }, 10000)
}

onMounted(async () => {
  loadRuleTasks()
  loadAiTasks()
  loadHumanTasks()
  try {
    const mr = await getModelOptions()
    modelOptions.value = mr.data || []
    if (modelOptions.value.length && !aiModel.value) aiModel.value = modelOptions.value[0].name
  } catch {}
  try {
    const pr = await getPromptOptions({ type: 'review' })
    promptOptions.value = pr.data || []
  } catch {}
  startAutoRefresh()
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.pipeline {
  padding: 4px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

/* 顶部流程指示 */
.pipeline-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  background: #fff;
  border-radius: 6px;
  margin-bottom: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
}
.step.active { color: #303133; }
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}
.step.active .step-num { background: #409eff; }
.step-label { font-weight: 600; font-size: 15px; }
.step-arrow { font-size: 22px; color: #c0c4cc; margin: 0 20px; font-weight: 300; }

/* 三列管道 */
.pipeline-columns {
  display: flex;
  flex: 1;
  gap: 0;
  min-height: 0;
}

.pipeline-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  border-radius: 6px;
  overflow: hidden;
}

.col-divider {
  width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 28px;
  font-weight: 300;
  user-select: none;
}

.col-header {
  padding: 10px 12px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.col-title { font-weight: 600; font-size: 14px; color: #303133; }
.col-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

/* 状态筛选栏 */
.col-filter {
  padding: 6px 12px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  gap: 4px;
}
.filter-tag {
  padding: 2px 10px;
  font-size: 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #909399;
  background: #f4f4f5;
  transition: all 0.15s;
  user-select: none;
}
.filter-tag:hover { color: #409eff; background: #ecf5ff; }
.filter-tag.active { color: #fff; background: #409eff; }

.col-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 13px;
}

/* 卡片 */
.pipeline-card {
  background: #fff;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  cursor: default;
  transition: border-color 0.2s;
}
.pipeline-card:hover { border-color: #c0c4cc; }
.pipeline-card.selected { border-color: #409eff; background: #ecf5ff; }

.card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.card-id { font-weight: 600; font-size: 13px; color: #606266; }

.card-info { font-size: 12px; color: #909399; }
.card-row { margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-label { color: #606266; }

.card-actions {
  margin-top: 6px;
  display: flex;
  gap: 4px;
  border-top: 1px solid #f2f6fc;
  padding-top: 6px;
}

/* 详情弹窗样式 */
.dialog-header-bar { display: flex; justify-content: space-between; align-items: center; }
.detail-header { display: flex; align-items: flex-start; justify-content: space-between; }
.detail-header .el-descriptions { flex: 1; }
.detail-tabs { margin-top: 16px; }
.tab-toolbar { margin-bottom: 8px; }
.violation-summary { border: 1px solid #EBEEF5; border-radius: 6px; padding: 12px 16px; }
.violation-summary-title { font-weight: 600; margin-bottom: 10px; color: #303133; }
.violation-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.violation-badge { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.violation-msg { font-size: 13px; color: #606266; }
</style>
