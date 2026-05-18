<template>
  <el-card shadow="hover" class="upload-card">
    <template #header>
      <div class="card-header">
        <el-icon :size="22" color="#409eff"><UploadFilled /></el-icon>
        <span class="card-title">历史变更文件上传</span>
      </div>
    </template>

    <div class="upload-toolbar">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        accept=".xlsx,.xls"
        :multiple="true"
        :limit="30"
        :on-change="onFileChange"
        :on-exceed="onExceed"
        :on-remove="onRemove"
        :file-list="fileList"
        class="upload-inline"
      >
        <el-button type="primary" :icon="FolderOpened">选择文件</el-button>
      </el-upload>
      <span class="upload-tip">支持 .xlsx / .xls 格式，最多 10 个文件</span>
    </div>

    <el-table
      v-if="fileList.length > 0"
      :data="fileList"
      border
      size="small"
      class="file-table"
      max-height="240"
    >
      <el-table-column type="index" label="#" width="50" align="center" />
      <el-table-column prop="name" label="文件名" min-width="200" show-overflow-tooltip />
      <el-table-column label="大小" width="100" align="center">
        <template #default="{ row }">
          {{ formatSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row._status === 'success'" type="success" size="small">成功</el-tag>
          <el-tag v-else-if="row._status === 'failed'" type="danger" size="small">失败</el-tag>
          <el-tag v-else-if="row._status === 'uploading'" type="warning" size="small">上传中</el-tag>
          <el-tag v-else type="info" size="small">待上传</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" align="center">
        <template #default="{ $index }">
          <el-button
            type="danger"
            link
            size="small"
            :disabled="uploading"
            @click="removeFile($index)"
          >
            移除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-progress
      v-if="uploading"
      :percentage="uploadProgress"
      :stroke-width="6"
      :format="progressFormat"
      class="upload-progress"
    />

    <el-button
      type="primary"
      :loading="uploading"
      :disabled="fileList.length === 0"
      class="upload-btn"
      @click="submitUpload"
    >
      {{ uploading ? uploadBtnText : '开始上传' }}
    </el-button>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, FolderOpened } from '@element-plus/icons-vue'
import { uploadExcel } from '@/api/rule'

const emit = defineEmits(['uploaded'])

const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadedCount = ref(0)

const uploadBtnText = computed(() => {
  if (!uploading.value) return '开始上传'
  return `上传中 (${uploadedCount.value}/${fileList.value.length})`
})

function onFileChange(uploadFile, uploadFiles) {
  const raw = uploadFile.raw
  const validTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
  ]
  const isExcel = validTypes.includes(raw.type) || raw.name.endsWith('.xlsx') || raw.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error(`文件 "${uploadFile.name}" 不是 Excel 格式，已忽略`)
    uploadRef.value?.handleRemove(uploadFile)
    return
  }
  uploadFile._status = 'pending'
  fileList.value = uploadFiles.map(f => ({ ...f, _status: f._status || 'pending' }))
}

function onExceed() {
  ElMessage.warning('最多同时上传 10 个文件')
}

function onRemove(uploadFile, uploadFiles) {
  fileList.value = uploadFiles.map(f => ({ ...f, _status: f._status || 'pending' }))
}

function removeFile(index) {
  fileList.value.splice(index, 1)
  if (uploadRef.value) {
    uploadRef.value.uploadFiles.splice(index, 1)
  }
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function progressFormat(percentage) {
  return percentage === 100 ? '完成' : `${percentage}%`
}

async function submitUpload() {
  if (fileList.value.length === 0) return

  uploading.value = true
  uploadProgress.value = 0
  uploadedCount.value = 0

  const total = fileList.value.length
  let successCount = 0
  let failCount = 0

  for (let i = 0; i < total; i++) {
    const file = fileList.value[i]
    file._status = 'uploading'

    const formData = new FormData()
    formData.append('file', file.raw)

    try {
      await uploadExcel(formData)
      file._status = 'success'
      successCount++
    } catch {
      file._status = 'failed'
      failCount++
    }

    uploadedCount.value = i + 1
    uploadProgress.value = Math.round(((i + 1) / total) * 100)
  }

  if (successCount > 0) {
    ElMessage.success(`${successCount} 个文件上传成功${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    emit('uploaded')
  } else {
    ElMessage.error('所有文件上传失败')
  }

  setTimeout(() => {
    uploading.value = false
    uploadProgress.value = 0
    fileList.value = []
    uploadRef.value?.clearFiles()
  }, 800)
}
</script>

<style scoped>
.upload-card {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.upload-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.upload-inline :deep(.el-upload-list) {
  display: none;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
}
.file-table {
  margin-top: 12px;
}
.upload-progress {
  margin-top: 12px;
}
.upload-btn {
  width: auto;
  margin-top: 12px;
}
</style>
