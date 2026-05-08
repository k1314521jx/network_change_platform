<template>
  <div class="human-review-tab">
    <el-row :gutter="16">
      <!-- 左侧侧边栏 -->
      <el-col :span="6">
        <ReviewSidebar :active-id="currentTaskId" @select="onSelect" />
      </el-col>
      <!-- 右侧编辑区 -->
      <el-col :span="18">
        <template v-if="currentTaskId">
          <!-- AI审核上下文 -->
          <el-collapse v-if="aiReviewContext" style="margin-bottom: 12px;">
            <el-collapse-item>
              <template #title>
                <span class="ai-context-title">AI审核结果 · 得分 <strong :style="{ color: getScoreColor(aiReviewContext.score) }">{{ aiReviewContext.score }}</strong></span>
              </template>
              <div class="ai-context-body">
                <div v-if="aiReviewContext.summary" class="ai-summary">{{ aiReviewContext.summary }}</div>
                <div v-if="aiReviewContext.suggestions && aiReviewContext.suggestions.length" class="ai-suggestions">
                  <div v-for="(s, i) in aiReviewContext.suggestions" :key="i" class="ai-suggestion-item">
                    <el-tag size="small" type="warning">建议</el-tag>
                    <span>{{ s.table }} 第{{ s.row_index }}行 {{ s.field }}: {{ s.issue }}</span>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <TripleEditor
            :edit-data="editData"
            :current-task-id="currentTaskId"
            :review-status="reviewStatus"
            :is-readonly="reviewStatus === 'approved'"
            @submit="onSubmit"
          />
        </template>
        <el-empty v-else description="请从左侧选择待审核数据" />
      </el-col>
    </el-row>

    <ReviewerDialog v-model="reviewerVisible" @confirm="onReviewerConfirm" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import ReviewSidebar from './ReviewSidebar.vue'
import TripleEditor from './TripleEditor.vue'
import ReviewerDialog from './ReviewerDialog.vue'
import { getReviewData, submitReview } from '@/api/review'

const currentTaskId = ref(null)
const reviewStatus = ref(null)
const reviewerVisible = ref(false)
const pendingAction = ref('')
const aiReviewContext = ref(null)

const editData = reactive({ table1: [], table2: [], table3: [] })

function getScoreColor(score) {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

async function onSelect({ tripleTaskId, reviewStatus: status }) {
  currentTaskId.value = tripleTaskId
  reviewStatus.value = status
  try {
    const res = await getReviewData(tripleTaskId)
    editData.table1 = res.data.table1 || []
    editData.table2 = res.data.table2 || []
    editData.table3 = res.data.table3 || []
    reviewStatus.value = res.data.review_status || status
    aiReviewContext.value = res.data.ai_review || null
  } catch {}
}

function onSubmit(action) {
  pendingAction.value = action
  reviewerVisible.value = true
}

async function onReviewerConfirm(reviewer) {
  try {
    await submitReview(currentTaskId.value, {
      table1: editData.table1,
      table2: editData.table2,
      table3: editData.table3,
      review_status: pendingAction.value,
      reviewer,
    })
    ElMessage.success(pendingAction.value === 'approved' ? '审核通过' : '已驳回')
    currentTaskId.value = null
    reviewStatus.value = null
    aiReviewContext.value = null
  } catch {}
}
</script>

<style scoped>
.ai-context-title { font-size: 14px; }
.ai-context-body { font-size: 13px; color: #606266; }
.ai-summary { margin-bottom: 8px; line-height: 1.6; }
.ai-suggestions { display: flex; flex-direction: column; gap: 4px; }
.ai-suggestion-item { display: flex; align-items: center; gap: 8px; }
</style>
