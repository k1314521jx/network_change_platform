<template>
  <el-card shadow="hover" class="sidebar-card">
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="待审核" name="pending">
        <el-scrollbar height="500px">
          <div v-if="pendingList.length === 0" class="empty-tip">暂无数据</div>
          <div
            v-for="item in pendingList"
            :key="item.id"
            class="list-item"
            :class="{ active: item.id === activeId }"
            @click="onSelect({ tripleTaskId: item.id, reviewStatus: item.review_status || 'review_pending' })"
          >
            <div class="item-header">
              <span class="item-id">#{{ item.id }}</span>
              <el-tag :type="getStatusTag(item.review_status || 'review_pending').type" size="small">
                {{ getStatusTag(item.review_status || 'review_pending').label }}
              </el-tag>
            </div>
            <div class="item-name">{{ item.rule_filename || '-' }}</div>
            <div class="item-time">{{ formatDateTime(item.created_at) }}</div>
          </div>
        </el-scrollbar>
      </el-tab-pane>
      <el-tab-pane label="已通过" name="approved">
        <el-scrollbar height="500px">
          <div v-if="approvedList.length === 0" class="empty-tip">暂无数据</div>
          <div
            v-for="item in approvedList"
            :key="item.id"
            class="list-item"
            :class="{ active: item.triple_task_id === activeId }"
            @click="onSelect({ tripleTaskId: item.triple_task_id, reviewStatus: 'approved' })"
          >
            <div class="item-header">
              <span class="item-id">#{{ item.triple_task_id }}</span>
              <el-tag type="success" size="small">已通过</el-tag>
            </div>
            <div class="item-info">审核人: {{ item.reviewer || '-' }}</div>
            <div class="item-time">{{ formatDateTime(item.review_time) }}</div>
          </div>
        </el-scrollbar>
      </el-tab-pane>
      <el-tab-pane label="已驳回" name="rejected">
        <el-scrollbar height="500px">
          <div v-if="rejectedList.length === 0" class="empty-tip">暂无数据</div>
          <div
            v-for="item in rejectedList"
            :key="item.id"
            class="list-item"
            :class="{ active: item.triple_task_id === activeId }"
            @click="onSelect({ tripleTaskId: item.triple_task_id, reviewStatus: 'rejected' })"
          >
            <div class="item-header">
              <span class="item-id">#{{ item.triple_task_id }}</span>
              <el-tag type="danger" size="small">已驳回</el-tag>
            </div>
            <div class="item-name">{{ item.rule_filename || '-' }}</div>
            <div class="item-info">审核人: {{ item.reviewer || '-' }}</div>
          </div>
        </el-scrollbar>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPendingList, getApprovedList, getRejectedList } from '@/api/review'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useStatusTag } from '@/composables/useStatusTag'

const props = defineProps({ activeId: { type: Number, default: null } })
const emit = defineEmits(['select'])
const { getStatusTag } = useStatusTag()

const activeTab = ref('pending')
const pendingList = ref([])
const approvedList = ref([])
const rejectedList = ref([])

async function loadPending() {
  try {
    const res = await getPendingList()
    pendingList.value = res.data || []
  } catch {}
}

async function loadApproved() {
  try {
    const res = await getApprovedList()
    approvedList.value = res.data || []
  } catch {}
}

async function loadRejected() {
  try {
    const res = await getRejectedList()
    rejectedList.value = res.data || []
  } catch {}
}

function onTabChange(tab) {
  if (tab === 'pending') loadPending()
  else if (tab === 'approved') loadApproved()
  else if (tab === 'rejected') loadRejected()
}

function onSelect(item) {
  emit('select', item)
}

const { start, stop } = useAutoRefresh(() => {
  if (activeTab.value === 'pending') loadPending()
}, 10000)

onMounted(() => {
  loadPending()
  start()
})

defineExpose({ refreshPending: loadPending, refreshApproved: loadApproved, refreshRejected: loadRejected })

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.sidebar-card { height: 100%; }
.sidebar-card :deep(.el-card__body) { padding: 0; }
.sidebar-card :deep(.el-tabs__header) { margin: 0; padding: 0 16px; }
.list-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}
.list-item:hover { background: #f5f7fa; }
.list-item.active { background: #ecf5ff; border-left: 3px solid #409EFF; }
.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.item-id { font-weight: 600; color: #303133; }
.item-name { font-size: 13px; color: #606266; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-info { font-size: 12px; color: #909399; }
.item-time { font-size: 12px; color: #c0c4cc; margin-top: 2px; }
.empty-tip { text-align: center; color: #c0c4cc; padding: 40px 0; }
</style>
