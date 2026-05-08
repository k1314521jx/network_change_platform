<template>
  <el-dialog v-model="visible" width="80%" :fullscreen="fullscreen" destroy-on-close>
    <template #header>
      <div class="dialog-header-bar">
        <span>三元组详情</span>
        <el-button link @click="fullscreen = !fullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>
      </div>
    </template>
    <template v-if="task">
      <div class="detail-header">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTag(task.status).type" size="small">{{ getStatusTag(task.status).label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(task.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-button
          v-if="task.status !== 'pending'"
          type="primary"
          plain
          size="small"
          :loading="exporting"
          @click="handleExportThinking"
        >
          导出思考
        </el-button>
      </div>

      <!-- 失败提示 -->
      <el-alert v-if="task.status === 'failed' && task.error_message" type="error" :closable="false" show-icon style="margin-top: 12px;">
        <template #title>失败原因：{{ task.error_message }}</template>
      </el-alert>

      <!-- 表格区域：成功状态显示三表数据 -->
      <el-tabs v-if="task.status === 'success'" v-model="activeTab" class="detail-tabs">
        <el-tab-pane label="Table1_Alignment" name="table1">
          <ReadonlyTable :data="tableData.table1" :columns="table1Cols" :maxHeight="tableMaxHeight" />
        </el-tab-pane>
        <el-tab-pane label="Table2_Entities_Attributes" name="table2">
          <ReadonlyTable :data="tableData.table2" :columns="table2Cols" :maxHeight="tableMaxHeight" />
        </el-tab-pane>
        <el-tab-pane label="Table3_Relations" name="table3">
          <ReadonlyTable :data="tableData.table3" :columns="table3Cols" :maxHeight="tableMaxHeight" />
        </el-tab-pane>
        <el-tab-pane label="原始JSON" name="raw">
          <JsonPreview :data="task.triple_json" />
        </el-tab-pane>
      </el-tabs>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'

const fullscreen = ref(false)
const tableMaxHeight = computed(() => fullscreen.value ? window.innerHeight - 280 : 400)
import JsonPreview from '@/components/common/JsonPreview.vue'
import ReadonlyTable from './ReadonlyTable.vue'
import { useStatusTag } from '@/composables/useStatusTag'
import { exportThinking } from '@/api/triple'

const table1Cols = ['row_index', 'raw_cmd', 'raw_rollback', 'step_name', 'au_name', 'role', 'entity', 'parameters']
const table2Cols = ['id', 'label', 'name', 'properties']
const table3Cols = ['source_entity', 'relation_type', 'target_entity', 'relation_attributes']

const props = defineProps({ modelValue: Boolean, task: Object })
const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const { getStatusTag } = useStatusTag()
const activeTab = ref('table1')
const exporting = ref(false)

const tableData = computed(() => {
  const json = props.task?.triple_json || {}
  return {
    table1: json.Table1_Alignment || [],
    table2: json.Table2_Entities_Attributes || [],
    table3: json.Table3_Relations || [],
  }
})

async function handleExportThinking() {
  if (!props.task) return
  exporting.value = true
  try {
    const resp = await exportThinking(props.task.id)
    // resp 是 axios response 对象（blob 模式）
    const blob = resp.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `thinking_task_${props.task.id}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    // 拦截器已处理错误提示（数据过期或数据未生成）
  } finally {
    exporting.value = false
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
</script>

<style scoped>
.dialog-header-bar { display: flex; justify-content: space-between; align-items: center; }
.detail-header { display: flex; align-items: flex-start; justify-content: space-between; }
.detail-header .el-descriptions { flex: 1; }
.detail-tabs { margin-top: 16px; }
</style>
