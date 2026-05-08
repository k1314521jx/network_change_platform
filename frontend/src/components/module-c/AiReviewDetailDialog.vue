<template>
  <el-dialog v-model="visible" width="85%" :fullscreen="fullscreen" destroy-on-close>
    <template #header>
      <div class="dialog-header-bar">
        <span>AI审核详情</span>
        <el-button link @click="fullscreen = !fullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>
      </div>
    </template>
    <template v-if="review">
      <div class="detail-header">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="审核ID">{{ review.id }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ review.model }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getAiStatusTag(review.status).type" size="small">{{ getAiStatusTag(review.status).label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="得分">
            <span v-if="review.score != null" class="score-text" :style="{ color: scoreColor }">{{ review.score }}</span>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
        <el-button v-if="review.status === 'reviewed' || review.status === 'failed'" type="primary" plain size="small" :loading="exporting" @click="handleExportThinking">导出思考</el-button>
      </div>

      <!-- 失败提示 -->
      <el-alert v-if="review.status === 'failed' && review.error_message" type="error" :closable="false" show-icon style="margin-top: 12px;">
        <template #title>失败原因：{{ review.error_message }}</template>
      </el-alert>

      <!-- 维度评分 -->
      <template v-if="review.dimensions && review.dimensions.length">
        <div class="section-title">维度评分</div>
        <div class="dimension-grid">
          <div v-for="dim in review.dimensions" :key="dim.name" class="dimension-card" :style="{ borderLeftColor: getDimColor(dim.score) }">
            <div class="dim-name">{{ dim.name }}</div>
            <div class="dim-score" :style="{ color: getDimColor(dim.score) }">{{ dim.score }}</div>
            <div class="dim-comment">{{ dim.comment }}</div>
          </div>
        </div>
      </template>

      <!-- 建议 -->
      <template v-if="suggestions.length">
        <div class="section-title">修改建议 ({{ suggestions.length }})</div>
        <el-table :data="suggestions" stripe size="small" max-height="250">
          <el-table-column prop="table" label="表" width="180" />
          <el-table-column prop="row_index" label="行号" width="70" />
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="issue" label="问题" />
          <el-table-column prop="suggestion" label="建议" />
        </el-table>
      </template>

      <!-- 摘要 -->
      <template v-if="review.summary">
        <div class="section-title">整体评价</div>
        <div class="summary-text">{{ review.summary }}</div>
      </template>

      <!-- 三表标注 -->
      <template v-if="review.status === 'reviewed' && tableData.table1.length">
        <div class="section-title">三元组数据标注</div>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="Table1_Alignment" name="table1">
            <ReadonlyTable :data="tableData.table1" :columns="table1Cols" :violations="suggestionViolations" tableName="Table1_Alignment" :maxHeight="tableMaxHeight" />
          </el-tab-pane>
          <el-tab-pane label="Table2_Entities_Attributes" name="table2">
            <ReadonlyTable :data="tableData.table2" :columns="table2Cols" :violations="suggestionViolations" tableName="Table2_Entities_Attributes" :maxHeight="tableMaxHeight" />
          </el-tab-pane>
          <el-tab-pane label="Table3_Relations" name="table3">
            <ReadonlyTable :data="tableData.table3" :columns="table3Cols" :violations="suggestionViolations" tableName="Table3_Relations" :maxHeight="tableMaxHeight" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import ReadonlyTable from '@/components/module-b/ReadonlyTable.vue'
import { useStatusTag } from '@/composables/useStatusTag'
import { exportAiReviewThinking } from '@/api/aiReview'

const fullscreen = ref(false)
const tableMaxHeight = computed(() => fullscreen.value ? window.innerHeight - 280 : 400)

const table1Cols = ['row_index', 'raw_cmd', 'raw_rollback', 'step_name', 'au_name', 'role', 'entity', 'parameters']
const table2Cols = ['id', 'label', 'name', 'properties']
const table3Cols = ['source_entity', 'relation_type', 'target_entity', 'relation_attributes']

const props = defineProps({ modelValue: Boolean, review: Object })
const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const { getStatusTag } = useStatusTag()
const activeTab = ref('table1')
const exporting = ref(false)

function getAiStatusTag(status) {
  const map = { pending: 'ai_pending', reviewing: 'reviewing', reviewed: 'reviewed', failed: 'ai_failed' }
  return getStatusTag(map[status] || status)
}

const scoreColor = computed(() => {
  const s = props.review?.score
  if (s == null) return '#909399'
  if (s >= 80) return '#67C23A'
  if (s >= 60) return '#E6A23C'
  return '#F56C6C'
})

const suggestions = computed(() => props.review?.suggestions || [])

const suggestionViolations = computed(() => {
  return suggestions.value.map((s, i) => ({
    rule: i + 1,
    level: 'AI建议',
    color: '#E6A23C',
    message: `${s.issue} → ${s.suggestion}`,
    locations: [{ table: s.table, row_index: s.row_index, field: s.field }],
  }))
})

const tableData = computed(() => {
  const json = props.review?.triple_json || {}
  return {
    table1: json.Table1_Alignment || [],
    table2: json.Table2_Entities_Attributes || [],
    table3: json.Table3_Relations || [],
  }
})

function getDimColor(score) {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

async function handleExportThinking() {
  if (!props.review) return
  exporting.value = true
  try {
    const resp = await exportAiReviewThinking(props.review.id)
    const blob = resp.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai_review_thinking_${props.review.id}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch {
    // 拦截器已处理错误提示
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.dialog-header-bar { display: flex; justify-content: space-between; align-items: center; }
.detail-header { display: flex; align-items: flex-start; justify-content: space-between; }
.detail-header .el-descriptions { flex: 1; }
.score-text { font-size: 24px; font-weight: 700; }
.section-title { font-weight: 600; margin: 16px 0 8px; color: #303133; }
.dimension-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.dimension-card {
  border: 1px solid #EBEEF5; border-radius: 6px; padding: 10px 12px;
  border-left: 3px solid #67C23A; background: #fafafa;
}
.dim-name { font-size: 13px; color: #606266; margin-bottom: 4px; }
.dim-score { font-size: 22px; font-weight: 700; }
.dim-comment { font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.5; }
.summary-text { background: #f5f7fa; padding: 12px; border-radius: 6px; font-size: 13px; color: #606266; line-height: 1.6; }
</style>
