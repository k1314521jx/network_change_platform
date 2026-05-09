<template>
  <div class="module-e">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane name="extraction">
        <template #label><el-icon><EditPen /></el-icon> 抽取提示词</template>
        <PromptTab type="extraction" />
      </el-tab-pane>
      <el-tab-pane name="review">
        <template #label><el-icon><Document /></el-icon> 审核提示词</template>
        <PromptTab type="review" />
      </el-tab-pane>
      <el-tab-pane name="model">
        <template #label><el-icon><Setting /></el-icon> 模型配置</template>
        <ModelTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PromptTab from '@/components/module-e/PromptTab.vue'
import ModelTab from '@/components/module-e/ModelTab.vue'

const activeTab = ref('extraction')
</script>

<style scoped>
.module-e {
  padding: 4px;
}
</style>
