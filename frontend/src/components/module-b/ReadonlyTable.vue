<template>
  <el-table :data="data" stripe style="width: 100%" :max-height="maxHeight" empty-text="无数据" size="small">
    <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" show-overflow-tooltip>
      <template #default="{ row }">
        <span
          :style="getCellStyle(row, col)"
          :title="getCellTitle(row, col)"
        >{{ formatCell(row[col]) }}</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const props = defineProps({
  data: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  violations: { type: Array, default: () => [] },
  tableName: { type: String, default: '' },
  maxHeight: { type: [Number, String], default: 400 },
})

function formatCell(val) {
  if (val === null || val === undefined) return ''
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function findViolations(row, col) {
  const rowIndex = row.row_index ?? (props.data.indexOf(row) + 1)
  return props.violations.filter(v => {
    if (!v.locations) return false
    return v.locations.some(loc => {
      if (loc.table !== props.tableName || loc.row_index !== rowIndex) return false
      // 直接匹配列名
      if (loc.field === col) return true
      // sub_key 匹配：loc.field=parameters, loc.sub_key=source_verify_au, col=parameters
      if (loc.sub_key && loc.field === col) return true
      return false
    })
  })
}

function getCellStyle(row, col) {
  const viols = findViolations(row, col)
  if (viols.length === 0) return {}
  // 取最高风险等级的颜色
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
