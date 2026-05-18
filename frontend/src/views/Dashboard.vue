<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card" v-for="item in statCards" :key="item.key">
        <div class="stat-icon" :style="{ background: item.bgColor }">
          <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ item.value }}</div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- 折线图区 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">规则化 & 图谱生成趋势</div>
        <div ref="trendChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">规则审核趋势</div>
        <div ref="validationChartRef" class="chart-body"></div>
      </div>
    </div>

    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">规则审核违规占比（首次验证）</div>
        <div ref="violationChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">AI 审核评分（按图谱转换模型）</div>
        <div ref="aiScoreChartRef" class="chart-body"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, markRaw } from 'vue'
import { UploadFilled, Cpu, CircleCheck, MagicStick, User } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getDashboardOverview, getDashboardDailyTrend, getDashboardAiScoreByModel, getDashboardViolationRateByModel } from '@/api/dashboard'

const loading = ref(false)
const overview = reactive({
  rule_success: 0,
  triple_success: 0,
  validation_passed: 0,
  ai_review_done: 0,
  human_review_done: 0,
})

const statCards = computed(() => [
  { key: 'rule', label: '方案规则化成功', value: overview.rule_success, icon: markRaw(UploadFilled), color: '#409EFF', bgColor: '#ECF5FF' },
  { key: 'triple', label: '图谱生成成功', value: overview.triple_success, icon: markRaw(Cpu), color: '#67C23A', bgColor: '#F0F9EB' },
  { key: 'validation', label: '规则审核通过', value: overview.validation_passed, icon: markRaw(CircleCheck), color: '#E6A23C', bgColor: '#FDF6EC' },
  { key: 'ai', label: 'AI 审核完成', value: overview.ai_review_done, icon: markRaw(MagicStick), color: '#F56C6C', bgColor: '#FEF0F0' },
  { key: 'human', label: '人工审核完成', value: overview.human_review_done, icon: markRaw(User), color: '#909399', bgColor: '#F4F4F5' },
])

// 图表 refs
const trendChartRef = ref(null)
const validationChartRef = ref(null)
const aiScoreChartRef = ref(null)
const violationChartRef = ref(null)

let trendChart = null
let validationChart = null
let aiScoreChart = null
let violationChart = null

function initCharts() {
  trendChart = echarts.init(trendChartRef.value)
  validationChart = echarts.init(validationChartRef.value)
  aiScoreChart = echarts.init(aiScoreChartRef.value)
  violationChart = echarts.init(violationChartRef.value)
}

function renderTrendChart(data) {
  if (!trendChart) return
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['规则化成功', '规则化失败', '图谱生成成功', '图谱生成失败'], bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: data.days, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '规则化成功', type: 'line', data: data.rule.success, smooth: true, symbol: 'circle', symbolSize: 6 },
      { name: '规则化失败', type: 'line', data: data.rule.failed, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { type: 'dashed' } },
      { name: '图谱生成成功', type: 'line', data: data.triple.success, smooth: true, symbol: 'circle', symbolSize: 6 },
      { name: '图谱生成失败', type: 'line', data: data.triple.failed, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { type: 'dashed' } },
    ],
  })
}

function renderValidationChart(data) {
  if (!validationChart) return
  validationChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['审核通过', '不合格'], bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: data.days, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '审核通过', type: 'line', data: data.validation.passed, smooth: true, symbol: 'circle', symbolSize: 6, itemStyle: { color: '#67C23A' } },
      { name: '不合格', type: 'line', data: data.validation.unqualified, smooth: true, symbol: 'circle', symbolSize: 6, itemStyle: { color: '#F56C6C' } },
    ],
  })
}

function renderAiScoreChart(data) {
  if (!aiScoreChart) return
  const series = data.series.map(s => ({
    name: s.model,
    type: 'line',
    data: s.scores,
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    connectNulls: true,
  }))
  aiScoreChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: data.series.map(s => s.model), bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: data.days, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}' } },
    series,
  })
}

const VIOLATION_COLORS = ['#F56C6C', '#FF9800', '#E6A23C', '#409EFF', '#67C23A']
const VIOLATION_LABELS = ['规则1: 结构缺失', '规则2: 孤立实体', '规则3: 未引用参数', '规则4: 角色不匹配', '规则5: 缺失校验AU']

function renderViolationChart(data) {
  if (!violationChart) return
  if (!data.length) {
    violationChart.setOption({
      title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14, fontWeight: 400 } },
    })
    return
  }
  const models = data.map(d => d.model)
  const series = []
  for (let i = 1; i <= 5; i++) {
    series.push({
      name: VIOLATION_LABELS[i - 1],
      type: 'bar',
      stack: 'total',
      data: data.map(d => d[`rule${i}`]),
      itemStyle: { color: VIOLATION_COLORS[i - 1] },
    })
  }
  violationChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: violationTooltipFormatter(data) },
    legend: { data: VIOLATION_LABELS, bottom: 0, type: 'scroll' },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: models, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' }, max: 100 },
    series,
  })
}

function violationTooltipFormatter(data) {
  return (params) => {
    const modelIdx = params[0].dataIndex
    const total = data[modelIdx].total
    let tip = `<b>${data[modelIdx].model}</b> (共${total}次不合格)<br/>`
    for (const p of params) {
      tip += `${p.marker} ${p.seriesName}: ${p.value}%<br/>`
    }
    return tip
  }
}

function handleResize() {
  trendChart?.resize()
  validationChart?.resize()
  aiScoreChart?.resize()
  violationChart?.resize()
}

async function loadData() {
  loading.value = true
  try {
    const [ovRes, trendRes, aiRes, violRes] = await Promise.all([
      getDashboardOverview(),
      getDashboardDailyTrend(),
      getDashboardAiScoreByModel(),
      getDashboardViolationRateByModel(),
    ])
    Object.assign(overview, ovRes.data)
    renderTrendChart(trendRes.data)
    renderValidationChart(trendRes.data)
    renderAiScoreChart(aiRes.data)
    renderViolationChart(violRes.data)
  } catch {} finally {
    loading.value = false
  }
}

onMounted(async () => {
  await nextTick()
  initCharts()
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  validationChart?.dispose()
  aiScoreChart?.dispose()
  violationChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 16px;
  height: calc(100vh - 100px);
  overflow-y: auto;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.chart-body {
  height: 320px;
}
</style>
