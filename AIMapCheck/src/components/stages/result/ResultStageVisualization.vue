<template>
  <div class="result-visualization">
    <div class="view-toggle">
      <el-switch
        v-model="showChart"
        active-text="图表视图"
        inactive-text="图片视图"
        @change="handleViewChange"
      />
    </div>

    <!-- 图片视图 -->
    <div v-if="!showChart" class="image-view">
      <div class="page-control">
        <el-button :disabled="currentPage === 1" @click="prevPage">上一页</el-button>
        <span>第 {{ currentPage }} 页</span>
        <el-button :disabled="currentPage === totalPages" @click="nextPage">下一页</el-button>
      </div>

      <div class="image-grid">
        <div v-for="(image, index) in currentImages" :key="index" class="image-item">
          <img :src="image" :alt="`结果图片 ${index + 1}`" />
        </div>
      </div>
    </div>

    <!-- 图表视图 -->
    <div v-else class="chart-view">
      <el-tabs v-model="activeChart">
        <el-tab-pane label="综合评分" name="radar">
          <div class="chart-container" ref="radarChartRef"></div>
        </el-tab-pane>
        <el-tab-pane label="问题分布" name="pie">
          <div class="chart-container" ref="pieChartRef"></div>
        </el-tab-pane>
        <el-tab-pane label="区域分析" name="bar">
          <div class="chart-container" ref="barChartRef"></div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { useRoute } from 'vue-router'
import axios from 'axios'
interface StageData {
    status: string
    progress?: number
}
const route = useRoute()
// 获取任务Id
const taskId = parseInt(route.params.id as string)
// 获取任务阶段数据
const stageData = ref<StageData | null>(null)
const getStageData = async () => {
  const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/5`)
  stageData.value = response.data.stage
}

onMounted(async () => {
  await getStageData()
})

// 视图控制
const showChart = ref(false)
const activeChart = ref('radar')

// 图片分页
const currentPage = ref(1)
const totalPages = ref(1)
const currentImages = ref<string[]>([])

// 图表实例
let radarChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

const radarChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
const barChartRef = ref<HTMLElement | null>(null)

// 加载图片
const loadImages = async (page: number) => {
  try {
    const response = await fetch(`http://8.148.68.206:5000/api/tasks/${taskId}/result/images/${page}`)
    const data = await response.json()
    currentImages.value = data.images.map((name: string) => 
      `http://8.148.68.206:5000/api/tasks/${taskId}/result/${name}`
    )
    totalPages.value = data.totalPages
  } catch (error) {
    ElMessage.error('加载图片失败')
    console.error('加载图片错误:', error)
  }
}

// 页面控制
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadImages(currentPage.value)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadImages(currentPage.value)
  }
}

// 视图切换
const handleViewChange = (value: boolean) => {
  showChart.value = value
  if (value) {
    // 切换到图表视图时初始化图表
    setTimeout(() => {
      initCharts()
    }, 0)
  }
}

// 初始化图表
const initCharts = async () => {
  try {
    const response = await fetch(`http://8.148.68.206:5000/api/tasks/${taskId}/result/statistics`)
    const data = await response.json()
    
    // 雷达图
    if (radarChartRef.value) {
      radarChart = echarts.init(radarChartRef.value)
      const radarOption: EChartsOption = {
        title: {
          text: '地图质量评分',
          left: 'center'
        },
        radar: {
          indicator: [
            { name: '完整性', max: 100 },
            { name: '准确性', max: 100 },
            { name: '规范性', max: 100 },
            { name: '图层质量', max: 100 },
            { name: '符号化', max: 100 },
            { name: '协调性', max: 100 }
          ]
        },
        series: [{
          type: 'radar',
          data: [{
            value: [
              data.dimensions.completeness,
              data.dimensions.accuracy,
              data.dimensions.standardization,
              data.dimensions.layerQuality,
              data.dimensions.symbolization,
              data.dimensions.coordination
            ],
            name: '评分',
            areaStyle: {
              color: 'rgba(67, 24, 255, 0.2)'
            },
            lineStyle: {
              color: '#4318FF'
            },
            itemStyle: {
              color: '#4318FF'
            }
          }]
        }]
      }
      radarChart.setOption(radarOption)
    }

    // 饼图
    if (pieChartRef.value) {
      pieChart = echarts.init(pieChartRef.value)
      const pieOption: EChartsOption = {
        title: {
          text: '问题类型分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        series: [{
          type: 'pie',
          radius: '70%',
          data: Object.entries(data.issueTypes).map(([name, value]) => ({
            name: name,
            value: value
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      pieChart.setOption(pieOption)
    }

    // 柱状图
    if (barChartRef.value) {
      barChart = echarts.init(barChartRef.value)
      const barOption: EChartsOption = {
        title: {
          text: '区域问题分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: Object.keys(data.regionAnalysis)
        },
        yAxis: {
          type: 'value',
          name: '问题数量'
        },
        series: [{
          type: 'bar',
          data: Object.values(data.regionAnalysis),
          itemStyle: {
            color: '#4318FF'
          }
        }]
      }
      barChart.setOption(barOption)
    }
  } catch (error) {
    ElMessage.error('加载统计数据失败')
    console.error('加载统计数据错误:', error)
  }
}

// 监听窗口大小变化
const handleResize = () => {
  radarChart?.resize()
  pieChart?.resize()
  barChart?.resize()
}

// 组件挂载时加载第一页图片
onMounted(() => {
  loadImages(1)
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
})

// 切换图表时重新渲染
watch(activeChart, () => {
  if (showChart.value) {
    setTimeout(() => {
      handleResize()
    }, 0)
  }
})
</script>

<style scoped>
.result-visualization {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: #f4f7fe;
}

.view-toggle {
  display: flex;
  justify-content: flex-end;
  padding: 0 20px;
}

.image-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.page-control {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 20px;
  flex: 1;
}

.image-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
  }
}

.chart-view {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.chart-container {
  height: 400px;
  width: 100%;
}

:deep(.el-tabs__content) {
  height: calc(100% - 55px);
  
  .el-tab-pane {
    height: 100%;
  }
}
</style> 