<template>
  <div class="model-tab">
    <!-- 顶部操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>新增模型
      </el-button>
    </div>

    <!-- 模型表格 -->
    <el-table :data="models" stripe size="small" v-loading="loading" style="margin-top: 12px;">
      <el-table-column prop="name" label="名称" width="120" />
      <el-table-column prop="model" label="模型ID" width="160" />
      <el-table-column prop="base_url" label="Base URL" show-overflow-tooltip />
      <el-table-column prop="api_key" label="API Key" width="140" show-overflow-tooltip />
      <el-table-column label="启用" width="70">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openViewDialog(row)">查看</el-button>
          <el-button link type="warning" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button link type="success" size="small" @click="handleTest(row)">验证</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="formVisible" :title="isEdit ? '编辑模型' : '新增模型'" width="600px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="formData.name" :disabled="isEdit" placeholder="如 deepseek、GLM、qwen" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="formData.base_url" placeholder="如 https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="formData.api_key" placeholder="请输入 API Key" show-password />
        </el-form-item>
        <el-form-item label="模型ID">
          <el-input v-model="formData.model" placeholder="如 deepseek-v4-pro" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" :loading="testing" @click="handleTestForm">验证连接</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="viewVisible" title="查看模型" width="600px" destroy-on-close>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="名称">{{ viewData.name }}</el-descriptions-item>
        <el-descriptions-item label="模型ID">{{ viewData.model }}</el-descriptions-item>
        <el-descriptions-item label="Base URL">{{ viewData.base_url }}</el-descriptions-item>
        <el-descriptions-item label="API Key">{{ viewData.api_key }}</el-descriptions-item>
        <el-descriptions-item label="启用">{{ viewData.is_active ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getModelList, getModelDetail, createModel, updateModel, deleteModel, testModelConnection } from '@/api/model'

const models = ref([])
const loading = ref(false)

// 表单
const formVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formData = ref({ name: '', api_key: '', base_url: '', model: '', is_active: true })
const submitting = ref(false)
const testing = ref(false)

// 查看
const viewVisible = ref(false)
const viewData = ref({})

async function loadModels() {
  loading.value = true
  try {
    const res = await getModelList()
    models.value = res.data || []
  } catch {} finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  formData.value = { name: '', api_key: '', base_url: '', model: '', is_active: true }
  formVisible.value = true
}

async function openEditDialog(row) {
  try {
    const res = await getModelDetail(row.id)
    isEdit.value = true
    editId.value = row.id
    formData.value = {
      name: res.data.name,
      api_key: res.data.api_key,
      base_url: res.data.base_url,
      model: res.data.model,
      is_active: res.data.is_active,
    }
    formVisible.value = true
  } catch {}
}

async function openViewDialog(row) {
  try {
    const res = await getModelDetail(row.id)
    viewData.value = res.data
    viewVisible.value = true
  } catch {}
}

async function handleSubmit() {
  const { name, api_key, base_url, model } = formData.value
  if (!name.trim() || !api_key.trim() || !base_url.trim() || !model.trim()) {
    ElMessage.warning('所有字段不能为空')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateModel(editId.value, formData.value)
      ElMessage.success('更新成功')
    } else {
      await createModel(formData.value)
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    loadModels()
  } catch {} finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除模型「${row.name}」？`, '确认删除', { type: 'warning' })
    await deleteModel(row.id)
    ElMessage.success('删除成功')
    loadModels()
  } catch {}
}

async function handleTest(row) {
  try {
    const res = await getModelDetail(row.id)
    const d = res.data
    const r = await testModelConnection({ api_key: d.api_key, base_url: d.base_url, model: d.model })
    ElMessage.success(r.message)
  } catch {}
}

async function handleTestForm() {
  const { api_key, base_url, model } = formData.value
  if (!api_key.trim() || !base_url.trim() || !model.trim()) {
    ElMessage.warning('请先填写 Base URL、API Key 和模型ID')
    return
  }
  testing.value = true
  try {
    const r = await testModelConnection({ api_key, base_url, model })
    ElMessage.success(r.message)
  } catch {} finally {
    testing.value = false
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => loadModels())
</script>

<style scoped>
.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
