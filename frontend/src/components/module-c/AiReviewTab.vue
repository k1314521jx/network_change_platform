<template>
  <div class="ai-review-tab">
    <!-- 顶部操作栏 -->
    <el-card shadow="never" class="action-card">
      <div class="action-bar">
        <el-select v-model="selectedModel" placeholder="选择审核模型" style="width: 160px">
          <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.name" />
        </el-select>
        <el-select v-model="selectedTask" placeholder="选择待审核任务" filterable style="width: 300px">
          <el-option v-for="t in eligibleTasks" :key="t.id" :label="`#${t.id} ${t.rule_filename}`" :value="t.id" />
        </el-select>
        <el-select v-model="selectedPrompt" placeholder="默认提示词" clearable style="width: 180px">
          <el-option v-for="p in promptOptions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" :loading="creating" @click="handleCreate">开始审核</el-button>
      </div>
    </el-card>

    <!-- 审核列表 -->
    <el-card shadow="never" style="margin-top: 12px;">
      <el-table :data="reviews" stripe size="small" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="triple_task_id" label="任务ID" width="80" />
        <el-table-column prop="rule_filename" label="规则文件" show-overflow-tooltip />
        <el-table-column prop="model" label="模型" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getAiStatusTag(row.status).type" size="small">{{ getAiStatusTag(row.status).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="得分" width="80">
          <template #default="{ row }">
            <span v-if="row.score != null" :style="{ color: getScoreColor(row.score), fontWeight: 600 }">{{ row.score }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.status !== 'reviewed' && row.status !== 'reviewing' && row.status !== 'pending'" link type="warning" size="small" @click="handleRetry(row)">重试</el-button>
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
    <AiReviewDetailDialog v-model="detailVisible" :review="currentReview" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useStatusTag } from '@/composables/useStatusTag'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { createAiReview, getAiReviewList, getAiReviewDetail, retryAiReview } from '@/api/aiReview'
import { getPassedTasks } from '@/api/ruleValidation'
import { getPromptOptions } from '@/api/prompt'
import { getModelOptions } from '@/api/model'
import AiReviewDetailDialog from './AiReviewDetailDialog.vue'

const { getStatusTag } = useStatusTag()

function getAiStatusTag(status) {
  const map = { pending: 'ai_pending', reviewing: 'reviewing', reviewed: 'reviewed', failed: 'ai_failed' }
  return getStatusTag(map[status] || status)
}

function getScoreColor(score) {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const reviews = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const creating = ref(false)

const selectedModel = ref('')
const selectedTask = ref(null)
const eligibleTasks = ref([])
const selectedPrompt = ref(null)
const promptOptions = ref([])
const modelOptions = ref([])

const detailVisible = ref(false)
const currentReview = ref(null)

async function loadReviews() {
  loading.value = true
  try {
    const res = await getAiReviewList({ page: page.value, per_page: perPage })
    reviews.value = res.data.items || []
    total.value = res.data.total || 0
  } catch {} finally {
    loading.value = false
  }
}

async function loadEligibleTasks() {
  try {
    const res = await getPassedTasks()
    eligibleTasks.value = res.data || []
  } catch {}
}

async function handleCreate() {
  if (!selectedTask.value) {
    ElMessage.warning('请选择待审核任务')
    return
  }
  creating.value = true
  try {
    await createAiReview({ triple_task_id: selectedTask.value, model: selectedModel.value, prompt_id: selectedPrompt.value })
    ElMessage.success('AI审核已触发')
    selectedTask.value = null
    loadReviews()
    loadEligibleTasks()
  } catch {} finally {
    creating.value = false
  }
}

async function handleRetry(row) {
  try {
    await retryAiReview(row.id)
    ElMessage.success('重试已触发')
    loadReviews()
  } catch {}
}

async function openDetail(row) {
  try {
    const res = await getAiReviewDetail(row.id)
    currentReview.value = res.data
    detailVisible.value = true
  } catch {}
}

function handlePageChange(p) {
  page.value = p
  loadReviews()
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const { start, stop } = useAutoRefresh(() => {
  if (reviews.value.some(r => r.status === 'pending' || r.status === 'reviewing')) {
    loadReviews()
  }
}, 5000)

onMounted(() => {
  loadReviews()
  loadEligibleTasks()
  loadPromptOptions()
  loadModelOptions()
  start()
})

async function loadPromptOptions() {
  try {
    const res = await getPromptOptions({ type: 'review' })
    promptOptions.value = res.data || []
  } catch {}
}

async function loadModelOptions() {
  try {
    const res = await getModelOptions()
    modelOptions.value = res.data || []
    if (modelOptions.value.length && !selectedModel.value) {
      selectedModel.value = modelOptions.value[0].name
    }
  } catch {}
}
</script>

<style scoped>
.action-card :deep(.el-card__body) { padding: 12px 16px; }
.action-bar { display: flex; gap: 12px; align-items: center; }
</style>
