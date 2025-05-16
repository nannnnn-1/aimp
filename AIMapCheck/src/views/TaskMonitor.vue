<template>
  <div class="task-monitor">
    <div class="header">
      <h2>任务监测</h2>
      <button class="refresh-btn" @click="refreshTaskData">
        <i class="fas fa-sync"></i>
        刷新
      </button>
    </div>

    <!-- <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      加载中...
    </div>

    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-circle"></i>
      {{ error }}
      <button @click="refreshTaskData">重试</button>
    </div> -->

    
      <div class="timeline">
        <div
          v-for="stage in stages"
          :key="stage.id"
          class="stage-item"
          :class="{
            'active': currentStage?.id === stage.id,
            [stage.status]: true
          }"
          @click="handleStageClick(stage)"
        >
          <div class="stage-number">{{ stage.number }}</div>
          <div class="stage-info">
            <span class="stage-name">{{ stage.name }}</span>
            <span class="stage-status">{{ getStatusText(stage.status) }}</span>
          </div>
        </div>
      </div>

      <div class="content">
        <div class="visualization-area">
          <component
            v-if="currentStage"
            :is="getVisualizationComponent(currentStage.type)"
            
            
            :model-type="currentModelSettings.modelType"
            :performance-data="currentModelSettings.performanceData"
            ref="analyzeVisualizationRef"
            @status-updated="handleActionExecuted"
            @analyze-completed="handleAnalyzeCompleted"
            @error_visualization_completed="handleErrorVisualizationCompleted"
            :selected-model-id="selectedModelIdForTask"
            :review-mode="reviewModeForTask"
          />
        </div>

        <Transition name="slide">
          <component
            v-if="showDetail && currentStage"
            :is="getDetailComponent(currentStage.type)"
            :stage-data="currentStage"
            
            :initial-model="currentModelSettings.modelType"
            :initial-mode="currentModelSettings.mode"
            @close="showDetail = false"
            @action-executed="handleActionExecuted"
            @upload-completed="handleUploadCompleted"
            @start-analysis="handleStartAnalysis"
            @start-review="handleStartReview"
            @result_confirmed="handleResultConfirmed"
            @start-report="handleStartReport"
            @feedback_submitted="handleFeedbackSubmitted"
            @feedback_completed="handleFeedbackCompleted"
            @update:selected-model-id="updateSelectedModel"
            @update:review-mode="updateModeForTask"
            @settings-saved="handleSettingsSaved"
          />
        </Transition>
      </div>
    
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import UploadStageDetail from '@/components/stages/upload/UploadStageDetail.vue'
import UploadStageVisualization from '@/components/stages/upload/UploadStageVisualization.vue'
import SettingsStageDetail from '@/components/stages/settings/SettingsStageDetail.vue'
import SettingsStageVisualization from '@/components/stages/settings/SettingsStageVisualization.vue'
import AnalyzeStageDetail from '@/components/stages/analyze/AnalyzeStageDetail.vue'
import AnalyzeStageVisualization from '@/components/stages/analyze/AnalyzeStageVisualization.vue'
import ReviewStageDetail from '@/components/stages/review/ReviewStageDetail.vue'
import ReviewStageVisualization from '@/components/stages/review/ReviewStageVisualization.vue'
import ResultStageDetail from '@/components/stages/result/ResultStageDetail.vue'
import ResultStageVisualization from '@/components/stages/result/ResultStageVisualization.vue'
import ReportStageDetail from '@/components/stages/report/ReportStageDetail.vue'
import ReportStageVisualization from '@/components/stages/report/ReportStageVisualization.vue'
import FeedbackStageDetail from '@/components/stages/feedback/FeedbackStageDetail.vue'
import FeedbackStageVisualization from '@/components/stages/feedback/FeedbackStageVisualization.vue'
import { ElMessage } from 'element-plus'

interface Stage {
  id: number
  number: number
  type: string
  name: string
  status: string
  progress?: number
}


interface PerformanceData {
  elementCoverage: number
  responseSpeed: number
  errorDetection: number
  complexStructure: number
  ruleCompatibility: number
  resourceConsumption: number
}

interface ModelSettings {
  modelType: string
  performanceData: PerformanceData | null
  mode: string
}
type ReviewMode = 'fast' | 'standard' | 'strict'; // Define type in parent as well
const route = useRoute()
const taskId = parseInt(route.params.id as string)
const currentStage = ref<Stage | null>(null)
const showDetail = ref(false)

const currentModelSettings = ref<ModelSettings>({
  modelType: 'model1',
  performanceData: null,
  mode: 'standard'
})

const analyzeVisualizationRef = ref<{

  startSequentialTileDisplay: () => void
  startMapDisplay: () => void
  fetchReportStatus: () => void
  getStageData: () => void
  triggerAnalysisStart: () => void
} | null>(null)

// const stages = computed(() => taskData.value.stages)
const stages = ref<Stage[]>([])
const statusMap: Record<string, string> = {
  'pending': '待处理',
  'in_progress': '处理中',
  'completed': '已完成',
  'error': '错误'
}

const selectedModelIdForTask = ref<number | string | null>(null);
const reviewModeForTask = ref<ReviewMode>('standard'); // Default mode in parent
const updateSelectedModel = (modelId: number | string | null) => {
  selectedModelIdForTask.value = modelId;
};
const updateModeForTask = (mode: ReviewMode) => {
  reviewModeForTask.value = mode
}

const handleSettingsSaved = () => {
    // Optionally reload task data or trigger next stage logic
    console.log("Settings saved, potentially move to next stage");
    // closeSettingsPanel();
    // Maybe reload settings to confirm, or just trust the save
    //  loadTaskSettings();
    refreshTaskData()
};
const getStatusText = (status: string) => {
  return statusMap[status] || status
}

const getDetailComponent = (type: string) => {
  const componentMap: Record<string, any> = {
    'upload': UploadStageDetail,
    'settings': SettingsStageDetail,
    'analyze': AnalyzeStageDetail,
    'review': ReviewStageDetail,
    'report': ReportStageDetail,
    'feedback': FeedbackStageDetail
  }
  return componentMap[type]
}

const getVisualizationComponent = (type: string) => {
  const componentMap: Record<string, any> = {
    'upload': UploadStageVisualization,
    'settings': SettingsStageVisualization,
    'analyze': AnalyzeStageVisualization,
    'review': ReviewStageVisualization,
    'report': ReportStageVisualization,
    'feedback': FeedbackStageVisualization
  }
  return componentMap[type]
}

const handleStageClick = (stage: Stage) => {
  currentStage.value = stage
  showDetail.value = true
}

const handleActionExecuted = async () => {
  // 更新后端状态为已完成
  try {
    await refreshTaskData()
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
  }
}

const handleSettingsChange = (settings: {
  model: string,
  mode: string,
  performanceData: {
    elementCoverage: number,
    responseSpeed: number,
    errorDetection: number,
    complexStructure: number,
    ruleCompatibility: number,
    resourceConsumption: number
  }
}) => {
  currentModelSettings.value = {
    modelType: settings.model,
    performanceData: settings.performanceData,
    mode: settings.mode
  }
}

const handleStartAnalysis = () => {
  refreshTaskData()
  analyzeVisualizationRef.value?.triggerAnalysisStart()
}

const handleAnalyzeCompleted = () => {
  refreshTaskData()
}

const handleStartReview = () => {
  refreshTaskData()
  analyzeVisualizationRef.value?.startSequentialTileDisplay()
}

const handleErrorVisualizationCompleted = () => {
  refreshTaskData()
}


const handleUploadCompleted = () => {
  analyzeVisualizationRef.value?.getStageData()
  refreshTaskData()
}

const handleStartReport = () => {
  analyzeVisualizationRef.value?.fetchReportStatus()
  refreshTaskData()
}


const handleResultConfirmed = () => {
  refreshTaskData()
}

const handleFeedbackSubmitted = () => {
  refreshTaskData()
}

const handleFeedbackCompleted = () => {
  refreshTaskData()
}

const refreshTaskData = async () => {
  try {
    const response = await axios.get(
      `http://8.148.68.206:5000/api/tasks/${route.params.id}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )


    stages.value = response.data.stages.map((stage: any) => ({
      id: stage.stage_number,
      number: stage.stage_number,
      type: getStageType(stage.stage_number),
      name: stage.stage_name,
      status: stage.status,
      progress: stage.progress
    }))

    
  } catch (err: any) {
    console.error('获取任务数据失败:', err)
  } finally {
  }
}

// 添加获取阶段类型的辅助函数
const getStageType = (stageNumber: number): string => {
  const stageTypes = {
    1: 'upload',
    2: 'settings',
    3: 'analyze',
    4: 'review',
    5: 'report',
    6: 'feedback'
  }
  return stageTypes[stageNumber as keyof typeof stageTypes] || 'unknown'
}

// 初始加载
refreshTaskData()
</script>

<style scoped>
.task-monitor {
  padding: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h2 {
    margin: 0;
    color: #2b3674;
  }
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #4318ff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  
  &:hover {
    background: #3311cc;
  }
  
  i {
    font-size: 14px;
  }
}

.loading-state,
.error-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #a3aed0;
  
  i {
    font-size: 24px;
  }
  
  button {
    margin-left: 12px;
    padding: 4px 12px;
    background: #4318ff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    
    &:hover {
      background: #3311cc;
    }
  }
}

.error-state {
  color: #f1416c;
}

.timeline {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    background: #f4f7fe;
  }
  
  &.active {
    background: #e9f7ff;
  }
  
  &.pending {
    .stage-number {
      background: #f4f7fe;
      color: #a3aed0;
    }
  }
  
  &.in_progress {
    .stage-number {
      background: #e9f7ff;
      color: #009ef7;
    }
  }
  
  &.completed {
    .stage-number {
      background: #e6f6f4;
      color: #05cd99;
    }
  }
  
  &.error {
    .stage-number {
      background: #ffe2e5;
      color: #f1416c;
    }
  }
}

.stage-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
}

.stage-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-name {
  font-size: 14px;
  color: #2b3674;
  font-weight: 500;
}

.stage-status {
  font-size: 12px;
  color: #a3aed0;
}

.content {
  flex: 1;
  position: relative;
  display: flex;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.visualization-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style> 