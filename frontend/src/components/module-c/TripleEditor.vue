<template>
  <el-card shadow="hover">
    <template #header>
      <div class="editor-header">
        <div class="editor-title">
          <span>三元组数据 #{{ currentTaskId }}</span>
          <el-tag v-if="isReadonly" type="success" size="small">已通过（只读）</el-tag>
          <el-tag v-else-if="reviewStatus === 'rejected'" type="danger" size="small">已驳回（可编辑）</el-tag>
          <el-tag v-else type="info" size="small">待审核</el-tag>
        </div>
        <div class="editor-actions">
          <el-button type="success" :disabled="isReadonly" @click="emit('submit', 'approved')">
            <el-icon><CircleCheck /></el-icon> 审核通过
          </el-button>
          <el-button type="danger" :disabled="isReadonly" @click="emit('submit', 'rejected')">
            <el-icon><CircleClose /></el-icon> 驳回
          </el-button>
        </div>
      </div>
    </template>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Table1_Alignment" name="table1">
        <template #label>Table1_Alignment <el-badge :value="editData.table1.length" type="info" /></template>
        <EditableSheetTable v-model="editData.table1" :columns="table1Cols" :readonly="isReadonly" :violations="violations" tableName="Table1_Alignment" />
      </el-tab-pane>
      <el-tab-pane label="Table2_Entities_Attributes" name="table2">
        <template #label>Table2_Entities <el-badge :value="editData.table2.length" type="info" /></template>
        <EditableSheetTable v-model="editData.table2" :columns="table2Cols" :readonly="isReadonly" :violations="violations" tableName="Table2_Entities_Attributes" />
      </el-tab-pane>
      <el-tab-pane label="Table3_Relations" name="table3">
        <template #label>Table3_Relations <el-badge :value="editData.table3.length" type="info" /></template>
        <EditableSheetTable v-model="editData.table3" :columns="table3Cols" :readonly="isReadonly" :violations="violations" tableName="Table3_Relations" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import EditableSheetTable from './EditableSheetTable.vue'

const table1Cols = ['row_index', 'raw_cmd', 'raw_rollback', 'step_name', 'au_name', 'role', 'entity', 'parameters']
const table2Cols = ['id', 'label', 'name', 'properties']
const table3Cols = ['source_entity', 'relation_type', 'target_entity', 'relation_attributes']

const props = defineProps({
  editData: { type: Object, default: () => ({ table1: [], table2: [], table3: [] }) },
  isReadonly: { type: Boolean, default: false },
  currentTaskId: { type: Number, default: null },
  reviewStatus: { type: String, default: null },
  violations: { type: Array, default: () => [] },
})
const emit = defineEmits(['submit'])
const activeTab = ref('table1')
</script>

<style scoped>
.editor-header { display: flex; justify-content: space-between; align-items: center; }
.editor-title { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.editor-actions { display: flex; gap: 8px; }
</style>
