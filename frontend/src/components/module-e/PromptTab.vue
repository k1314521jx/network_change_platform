<template>
  <div class="prompt-tab">
    <!-- 顶部操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>新增提示词
      </el-button>
      <el-input
        v-model="searchText"
        placeholder="搜索提示词名称"
        clearable
        style="width: 240px;"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch"><el-icon><Search /></el-icon></el-button>
        </template>
      </el-input>
    </div>

    <!-- 提示词表格 -->
    <el-table :data="prompts" stripe size="small" v-loading="loading" style="margin-top: 12px;">
      <el-table-column prop="name" label="名称" show-overflow-tooltip />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="内置" width="70">
        <template #default="{ row }">
          <el-tag v-if="row.is_builtin" type="info" size="small">是</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openViewDialog(row)">查看</el-button>
          <el-button link type="warning" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button link type="info" size="small" @click="openHistoryDialog(row)">历史</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      style="margin-top: 12px; justify-content: flex-end;"
      :current-page="page"
      :page-size="perPage"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="handlePageChange"
    />

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="formVisible" :title="isEdit ? '编辑提示词' : '新增提示词'" width="700px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="formData.name" :disabled="isEdit" placeholder="请输入提示词名称" />
        </el-form-item>
        <el-form-item label="版本说明">
          <el-input
            v-model="formData.changelog"
            placeholder="请输入本次修改说明（选填）"
          />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="18"
            placeholder="请输入提示词内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="viewVisible" title="查看提示词" width="700px" destroy-on-close>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="名称">{{ viewData.name }}</el-descriptions-item>
        <el-descriptions-item label="版本">v{{ viewData.version }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ viewData.type === 'extraction' ? '抽取提示词' : '审核提示词' }}</el-descriptions-item>
        <el-descriptions-item label="内置">{{ viewData.is_builtin ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item v-if="viewData.changelog" label="版本说明" :span="2">{{ viewData.changelog }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 12px;">
        <el-input
          :model-value="viewData.content"
          type="textarea"
          :rows="18"
          readonly
        />
      </div>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 历史版本对话框 -->
    <el-dialog v-model="historyVisible" title="历史版本" width="700px" destroy-on-close>
      <el-table :data="historyList" stripe size="small" v-loading="historyLoading">
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="当前" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" type="success" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="changelog" label="说明" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openHistoryView(row)">查看</el-button>
            <el-button v-if="!row.is_current" link type="success" size="small" @click="handleActivate(row)">启用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="historyViewContent" style="margin-top: 12px;">
        <div style="margin-bottom: 6px; font-weight: 600;">版本 v{{ historyViewVersion }} 内容：</div>
        <el-input :model-value="historyViewContent" type="textarea" :rows="14" readonly />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPromptList, getPromptDetail, createPrompt, updatePrompt, deletePrompt, getPromptHistory, activatePrompt } from '@/api/prompt'

const props = defineProps({
  type: { type: String, required: true },
})

const prompts = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const searchText = ref('')

// 表单
const formVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formData = ref({ name: '', content: '' })
const submitting = ref(false)

// 查看
const viewVisible = ref(false)
const viewData = ref({})

// 历史
const historyVisible = ref(false)
const historyList = ref([])
const historyLoading = ref(false)
const historyViewContent = ref('')
const historyViewVersion = ref(null)

async function loadPrompts() {
  loading.value = true
  try {
    const res = await getPromptList({
      type: props.type,
      page: page.value,
      per_page: perPage,
      search: searchText.value,
    })
    prompts.value = res.data.items || []
    total.value = res.data.total || 0
  } catch {} finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadPrompts()
}

function handlePageChange(p) {
  page.value = p
  loadPrompts()
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  formData.value = { name: '', content: '', changelog: '' }
  formVisible.value = true
}

async function openEditDialog(row) {
  try {
    const res = await getPromptDetail(row.id)
    isEdit.value = true
    editId.value = row.id
    formData.value = { name: res.data.name, content: res.data.content, changelog: '' }
    formVisible.value = true
  } catch {}
}

async function openViewDialog(row) {
  try {
    const res = await getPromptDetail(row.id)
    viewData.value = res.data
    viewVisible.value = true
  } catch {}
}

async function handleSubmit() {
  if (!formData.value.name.trim() || !formData.value.content.trim()) {
    ElMessage.warning('名称和内容不能为空')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updatePrompt(editId.value, { content: formData.value.content, changelog: formData.value.changelog })
      ElMessage.success('更新成功（已创建新版本）')
    } else {
      await createPrompt({ name: formData.value.name, type: props.type, content: formData.value.content, changelog: formData.value.changelog })
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    loadPrompts()
  } catch {} finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除提示词「${row.name}」的所有版本？`, '确认删除', { type: 'warning' })
    await deletePrompt(row.id)
    ElMessage.success('删除成功')
    loadPrompts()
  } catch {}
}

async function openHistoryDialog(row) {
  historyViewContent.value = ''
  historyViewVersion.value = null
  historyVisible.value = true
  historyLoading.value = true
  try {
    const res = await getPromptHistory(row.name, { type: props.type })
    historyList.value = res.data || []
  } catch {} finally {
    historyLoading.value = false
  }
}

function openHistoryView(row) {
  historyViewContent.value = row.content
  historyViewVersion.value = row.version
}

async function handleActivate(row) {
  try {
    await ElMessageBox.confirm(`确定启用版本 v${row.version}？当前活跃版本将被替换。`, '确认启用', { type: 'info' })
    await activatePrompt(row.id)
    ElMessage.success(`已启用版本 v${row.version}`)
    // 刷新历史列表和主列表
    historyList.value = historyList.value.map(h => ({ ...h, is_current: h.id === row.id }))
    loadPrompts()
  } catch {}
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => loadPrompts())
</script>

<style scoped>
.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
