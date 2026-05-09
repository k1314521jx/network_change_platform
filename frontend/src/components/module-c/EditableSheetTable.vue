<template>
  <div class="editable-sheet-table">
    <div class="table-toolbar">
      <el-button v-if="!readonly" type="primary" plain size="small" @click="addRow">
        <el-icon><Plus /></el-icon> 新增行
      </el-button>
      <el-button v-if="showErrorToggle" size="small" :type="errorOnly ? 'primary' : ''" @click="emit('update:errorOnly', !errorOnly)">
        {{ errorOnly ? '显示全部' : '只看错误行' }}
      </el-button>
      <el-button v-if="showExportImport" size="small" @click="emit('export')">
        <el-icon><Download /></el-icon> 导出
      </el-button>
      <el-upload
        v-if="showExportImport"
        :show-file-list="false"
        :before-upload="handleImport"
        accept=".xlsx"
        :auto-upload="false"
      >
        <el-button size="small">
          <el-icon><Upload /></el-icon> 导入
        </el-button>
      </el-upload>
    </div>
    <el-table :data="localData" stripe border size="small" style="width: 100%;" :max-height="maxHeight">
      <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" :min-width="getColumnWidth(col)">
        <template #default="{ row, $index }">
          <el-tooltip
            v-if="findViolations(row, col).length"
            :content="getCellTitle(row, col)"
            placement="top"
            :show-after="300"
          >
            <div :style="getCellStyle(row, col)" class="violation-cell">
              <el-input
                v-if="isObjectValue(row[col]) && !readonly"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 4 }"
                :model-value="getObjModelValue(row, col)"
                @focus="startObjEdit(row, col)"
                @input="onObjInput"
                @blur="finishObjEdit(row, col)"
                size="small"
              />
              <el-input
                v-else-if="!readonly"
                :model-value="String(row[col] ?? '')"
                @input="onCellInput(row, col, $event)"
                @change="emitUpdate()"
                size="small"
              />
              <span v-else>{{ formatCell(row[col]) }}</span>
            </div>
          </el-tooltip>
          <template v-else>
            <el-input
              v-if="isObjectValue(row[col]) && !readonly"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              :model-value="getObjModelValue(row, col)"
              @focus="startObjEdit(row, col)"
              @input="onObjInput"
              @blur="finishObjEdit(row, col)"
              size="small"
            />
            <el-input
              v-else-if="!readonly"
              :model-value="String(row[col] ?? '')"
              @input="onCellInput(row, col, $event)"
              @change="emitUpdate()"
              size="small"
            />
            <span v-else>{{ formatCell(row[col]) }}</span>
          </template>
        </template>
      </el-table-column>
      <el-table-column v-if="!readonly" label="操作" width="70" fixed="right">
        <template #default="{ $index }">
          <el-button type="danger" link size="small" @click="deleteRow($index)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Delete, Download, Upload } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
  violations: { type: Array, default: () => [] },
  tableName: { type: String, default: '' },
  maxHeight: { type: [Number, String], default: 450 },
  showErrorToggle: { type: Boolean, default: false },
  errorOnly: { type: Boolean, default: false },
  showExportImport: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'update:errorOnly', 'export', 'import'])

const localData = ref([])

watch(() => props.modelValue, (val) => {
  localData.value = Array.isArray(val) ? val.map(r => ({ ...r })) : []
}, { immediate: true, deep: true })

const objectColumns = new Set(['parameters', 'properties', 'relation_attributes'])

const editingCell = ref(null)

function isObjectValue(val) {
  return val !== null && val !== undefined && typeof val === 'object'
}

function isObjectColumn(col) {
  return objectColumns.has(col)
}

function getColumnWidth(col) {
  const widths = { raw_cmd: 180, raw_rollback: 180, parameters: 200, properties: 200, relation_attributes: 180 }
  return widths[col] || 120
}

function formatCell(val) {
  if (val === null || val === undefined) return ''
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function formatObjValue(val) {
  if (val === null || val === undefined) return ''
  if (typeof val === 'object') return JSON.stringify(val, null, 2)
  return String(val)
}

function getObjModelValue(row, col) {
  if (editingCell.value && editingCell.value.row === row && editingCell.value.col === col) {
    return editingCell.value.text
  }
  return formatObjValue(row[col])
}

function startObjEdit(row, col) {
  editingCell.value = { row, col, text: formatObjValue(row[col]) }
}

function onObjInput(val) {
  if (editingCell.value) {
    editingCell.value = { ...editingCell.value, text: val }
  }
}

function finishObjEdit(row, col) {
  if (!editingCell.value) return
  const text = editingCell.value.text.trim()
  try {
    row[col] = JSON.parse(text)
  } catch {
    row[col] = text
  }
  editingCell.value = null
  emitUpdate()
}

function onCellInput(row, col, value) {
  row[col] = value
}

function addRow() {
  const newRow = {}
  props.columns.forEach(c => { newRow[c] = '' })
  localData.value.push(newRow)
  emitUpdate()
  ElMessage.success('已添加新行')
}

async function deleteRow(index) {
  try {
    await ElMessageBox.confirm('确定删除该行？', '提示', { type: 'warning' })
    localData.value.splice(index, 1)
    emitUpdate()
    ElMessage.warning('行已删除')
  } catch {
    // 用户取消
  }
}

function emitUpdate() {
  emit('update:modelValue', localData.value.map(r => ({ ...r })))
}

function handleImport(file) {
  emit('import', file)
  return false // 阻止自动上传
}

// ---- 违规标记 ----
function findViolations(row, col) {
  const rowIndex = row.row_index ?? (localData.value.indexOf(row) + 1)
  const rowId = row.id
  return props.violations.filter(v => {
    if (!v.locations) return false
    return v.locations.some(loc => {
      if (loc.table !== props.tableName) return false
      // 匹配行: row_index / id（都转字符串比较，兼容数字与字符串）
      const locIdx = String(loc.row_index)
      if (locIdx !== String(rowIndex) && (rowId == null || locIdx !== String(rowId))) return false
      // 匹配列: 直接匹配 / sub_key / 点号子字段(如 "properties.xxx")
      if (loc.field === col) return true
      if (loc.sub_key && loc.field === col) return true
      if (loc.field.startsWith(col + '.')) return true
      return false
    })
  })
}

function getCellStyle(row, col) {
  const viols = findViolations(row, col)
  if (viols.length === 0) return {}
  const color = viols[0].color || '#F56C6C'
  return {
    backgroundColor: color + '22',
    borderLeft: `3px solid ${color}`,
    padding: '2px 6px',
    borderRadius: '2px',
  }
}

function getCellTitle(row, col) {
  const viols = findViolations(row, col)
  if (viols.length === 0) return ''
  return viols.map(v => `[规则${v.rule}] ${v.level}: ${v.message}`).join('\n')
}
</script>

<style scoped>
.table-toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.editable-sheet-table :deep(.el-table .el-table__cell) {
  padding: 4px 0;
}
.violation-cell :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
}
</style>
