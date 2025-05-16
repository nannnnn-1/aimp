<template>
  <div class="stage-detail">
    <div class="panel-overlay" @click="$emit('close')"></div>
    <div class="panel-content">
      <div class="panel-header">
        <h3>地图审查</h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="panel-body">
        <div class="status-section">
          <div class="status-badge" :class="stageData?.status">
            {{ getStatusText(stageData?.status || '') }}
          </div>
          <div v-if="stageData?.progress !== undefined" class="progress-bar">
            <div class="progress-fill" :style="{ width: `${stageData.progress}%` }"></div>
            <span class="progress-text">{{ stageData.progress }}%</span>
          </div>
        </div>

        <div class="description-section">
          <p>在此阶段，系统将对地图进行全面审查。审查内容包括：</p>
          <ul>
            <li>地图要素完整性检查</li>
            <li>图层关系正确性验证</li>
            <li>地理坐标准确性核实</li>
            <li>符号使用规范性检查</li>
          </ul>
          <p>审查过程将逐步展示发现的问题，请仔细查看每个问题点。</p>
        </div>

        <div class="actions">
          <button 
            class="start-btn" 
            :disabled="stageData?.status === 'completed' || stageData?.status === 'in_progress'"
            @click="handleStartReview"
          >
            <i class="fas fa-search"></i>
            开始审查
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRoute } from 'vue-router'

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
  const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/4`)
  stageData.value = response.data.stage
}
onMounted(async () => {
  await getStageData()
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'start-review'): void
}>()

const statusMap: Record<string, string> = {
  'pending': '待处理',
  'in_progress': '处理中',
  'completed': '已完成',
  'error': '错误'
}

const getStatusText = (status: string) => {
  return statusMap[status] || status
}

const handleStartReview = async () => {
  try {
    // 发送开始审查请求
    await axios.post(`http://8.148.68.206:5000/api/tasks/${taskId}/review/start`)
    
    // 通知visualization组件开始显示结果
    emit('start-review')
    
  } catch (error) {
    ElMessage.error('开始审查失败')
    console.error('开始审查错误:', error)
  }
}
</script>

<style scoped>
.stage-detail {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.panel-content {
  position: relative;
  width: 400px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #e0e5f2;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 20px;
  color: #2b3674;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #707eae;
  cursor: pointer;
  padding: 4px;
  
  &:hover {
    color: #2b3674;
  }
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-badge {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  align-self: flex-start;
  
  &.pending {
    background: #f4f7fe;
    color: #a3aed0;
  }
  
  &.in_progress {
    background: #e9f7ff;
    color: #009ef7;
  }
  
  &.completed {
    background: #e6f6f4;
    color: #05cd99;
  }
  
  &.error {
    background: #ffe2e5;
    color: #f1416c;
  }
}

.progress-bar {
  height: 8px;
  background: #f4f7fe;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #4318FF;
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  right: 0;
  top: -20px;
  font-size: 12px;
  color: #707eae;
}

.description-section {
  color: #2b3674;
  
  p {
    margin: 0 0 12px;
    font-size: 14px;
    line-height: 1.6;
  }
  
  ul {
    margin: 0 0 12px;
    padding-left: 20px;
    
    li {
      font-size: 14px;
      line-height: 1.6;
      margin-bottom: 8px;
    }
  }
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #4318ff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 14px;
  cursor: pointer;
  
  i {
    font-size: 14px;
  }
  
  &:hover {
    background: #3311cc;
  }
  
  &:disabled {
    background: #e0e5f2;
    cursor: not-allowed;
  }
}
</style> 