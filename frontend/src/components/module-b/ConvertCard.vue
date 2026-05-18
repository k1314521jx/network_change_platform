<template>
  <el-card shadow="never" class="action-card">
    <el-button type="primary" @click="dialogVisible = true">选择规则化数据</el-button>

    <el-dialog
      v-model="dialogVisible"
      title="选择规则化数据"
      width="75%"
      destroy-on-close
      @open="onDialogOpen"
    >
      <el-table
        ref="tableRef"
        v-loading="tableLoading"
        :data="ruleTasks"
        border
        stripe
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
        <el-table-column label="创建时间" width="180" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
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
          @current-change="loadRuleTasks"
          @size-change="loadRuleTasks"
        />
      </div>

      <div class="dialog-footer">
        <div class="footer-left">
          <el-select v-model="model" placeholder="选择模型" style="width: 160px;">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.name" />
          </el-select>
          <el-select v-model="promptId" placeholder="默认提示词" clearable style="width: 180px;">
            <el-option v-for="p in promptOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <el-button type="primary" :loading="converting" :disabled="selected.length === 0" @click="doConvert">
            开始转换
          </el-button>
        </div>
        <div class="footer-right">
          <span v-if="selected.length" class="selected-tip">已选 {{ selected.length }} 条</span>
          <el-button @click="dialogVisible = false">取消</el-button>
        </div>
      </div>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRuleTasks } from '@/api/rule'
import { batchConvertToTriple } from '@/api/triple'
import { getPromptOptions } from '@/api/prompt'
import { getModelOptions } from '@/api/model'

const emit = defineEmits(['converted'])

const dialogVisible = ref(false)
const tableRef = ref(null)
const tableLoading = ref(false)
const ruleTasks = ref([])
const selected = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)

const model = ref('')
const promptId = ref(null)
const promptOptions = ref([])
const modelOptions = ref([])
const converting = ref(false)

function formatTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function loadRuleTasks() {
  tableLoading.value = true
  try {
    const res = await getRuleTasks({ page: page.value, per_page: perPage.value, status: 'success' })
    ruleTasks.value = res.data.items || []
    total.value = res.data.total || 0
  } catch {
    ruleTasks.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

async function loadOptions() {
  try {
    const res = await getPromptOptions({ type: 'extraction' })
    promptOptions.value = res.data || []
  } catch {}
  try {
    const res = await getModelOptions()
    modelOptions.value = res.data || []
    if (modelOptions.value.length && !model.value) {
      model.value = modelOptions.value[0].name
    }
  } catch {}
}

function onDialogOpen() {
  page.value = 1
  selected.value = []
  loadRuleTasks()
  loadOptions()
}

function onSelectionChange(rows) {
  selected.value = rows
}

async function doConvert() {
  if (selected.value.length === 0) {
    ElMessage.warning('请至少选择一条规则数据')
    return
  }

  converting.value = true
  try {
    const ids = selected.value.map(r => r.id)
    const res = await batchConvertToTriple({
      rule_task_ids: ids,
      model: model.value,
      prompt_id: promptId.value,
    })
    ElMessage.success(res.message || '转换任务已创建')
    dialogVisible.value = false
    emit('converted')
  } catch {
  } finally {
    converting.value = false
  }
}
</script>

<style scoped>
.action-card :deep(.el-card__body) {
  padding: 12px 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
.footer-left {
  display: flex;
  gap: 12px;
  align-items: center;
}
.footer-right {
  display: flex;
  gap: 8px;
  align-items: center;
}
.selected-tip {
  font-size: 13px;
  color: #409eff;
}
</style>
