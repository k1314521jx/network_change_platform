<template>
  <div class="module-d">
    <el-row :gutter="20">
      <el-col :span="8">
        <Neo4jStatusCard
          :connected="connected"
          :selected-ids="selectedIds"
          :importing="importing"
          @import="(force) => doImport(force)"
        />
        <ApprovedCheckList v-model="selectedIds" style="margin-top: 16px;" />
      </el-col>
      <el-col :span="16">
        <ImportLogTable ref="logTable" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Neo4jStatusCard from '@/components/module-d/Neo4jStatusCard.vue'
import ApprovedCheckList from '@/components/module-d/ApprovedCheckList.vue'
import ImportLogTable from '@/components/module-d/ImportLogTable.vue'
import { getNeo4jStatus, importToNeo4j } from '@/api/neo4j'
import { ElMessage } from 'element-plus'

const connected = ref(null)
const selectedIds = ref([])
const importing = ref(false)
const logTable = ref(null)

onMounted(async () => {
  try {
    const res = await getNeo4jStatus()
    connected.value = res.data.connected
  } catch {
    connected.value = false
  }
})

async function doImport(force = false) {
  if (!selectedIds.value.length) {
    ElMessage.warning('请选择要入库的审核记录')
    return
  }
  importing.value = true
  try {
    const res = await importToNeo4j({ review_ids: selectedIds.value, force })
    ElMessage.success(res.message)
    selectedIds.value = []
    logTable.value?.refresh()
  } catch {
    // error handled by interceptor
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.module-d { padding: 4px; }
</style>
