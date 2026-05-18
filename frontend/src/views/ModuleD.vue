<template>
  <div class="module-d">
    <Neo4jStatusCard :connected="connected" @select="showDialog = true" />
    <DataSelectDialog v-model="showDialog" @imported="handleImported" />
    <div class="log-section">
      <ImportLogTable ref="logTable" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Neo4jStatusCard from '@/components/module-d/Neo4jStatusCard.vue'
import DataSelectDialog from '@/components/module-d/DataSelectDialog.vue'
import ImportLogTable from '@/components/module-d/ImportLogTable.vue'
import { getNeo4jStatus } from '@/api/neo4j'

const CACHE_KEY = 'neo4j_connected'

const connected = ref(null)
const showDialog = ref(false)
const logTable = ref(null)

onMounted(async () => {
  const cached = localStorage.getItem(CACHE_KEY)
  if (cached !== null) {
    connected.value = cached === 'true'
  }
  try {
    const res = await getNeo4jStatus()
    connected.value = res.data.connected
    localStorage.setItem(CACHE_KEY, String(connected.value))
  } catch {
    connected.value = false
    localStorage.setItem(CACHE_KEY, 'false')
  }
})

function handleImported() {
  logTable.value?.refresh()
}
</script>

<style scoped>
.module-d {
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.log-section {
  flex: 1;
}
</style>
