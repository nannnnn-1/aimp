<template>
    <div class="model-library">
      <!-- Toolbar -->
      <div class="toolbar">
        <el-button type="primary" @click="refreshModels" :loading="isLoading" :icon="Refresh">
          刷新列表
        </el-button>
      </div>

      <!-- Table -->
      <el-table
        :data="models"
        v-loading="isLoading"
        style="width: 100%"
        height="100%"
        empty-text="您还没有微调的模型"
        highlight-current-row
        class="model-table"
      >
        <!-- Columns (Name, Base Model) -->
        <el-table-column prop="name" label="模型名称" min-width="180" sortable show-overflow-tooltip />
        <el-table-column prop="base_model_id" label="基础模型" width="180" sortable show-overflow-tooltip />

        <!-- Status Column -->
        <el-table-column prop="status" label="状态" width="180" sortable>
          <template #default="scope">
            <!-- Status cell content (Tag, Progress) -->
             <div class="status-cell">
              <el-tag
                :type="getDisplayStatusTagType(scope.row.id, scope.row.status)"
                size="small"
                effect="plain"
                class="status-tag"
              >
                <el-icon
                  v-if="isSimulating(scope.row.id) || isLoadingStatus(scope.row.status)"
                  class="is-loading status-loading-icon"
                  :class="{ 'pulsing': getSimulationStage(scope.row.id) === 'training' }"
                >
                  <Loading />
                </el-icon>
                {{ getDisplayStatusText(scope.row.id, scope.row.status) }}
              </el-tag>
              <el-progress
                v-if="isSimulating(scope.row.id)"
                :percentage="getSimulationProgress(scope.row.id)"
                :stroke-width="5"
                :text-inside="false"
                striped striped-flow
                :status="getSimulationProgressStatus(scope.row.id)"
                class="status-progress"
              />
            </div>
          </template>
        </el-table-column>

        <!-- Timestamp Columns -->
        <el-table-column prop="creation_timestamp" label="创建时间" width="180" sortable>
           <template #default="scope">{{ formatTimestamp(scope.row.creation_timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="completion_timestamp" label="完成时间" width="180" sortable>
           <template #default="scope">{{ formatTimestamp(scope.row.completion_timestamp) }}</template>
        </el-table-column>

        <!-- Actions Column -->
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
             <el-tooltip content="查看详情" placement="top">
               <el-button link type="primary" size="small" @click.stop="handleViewDetails(scope.row)">详情</el-button>
             </el-tooltip>
             <el-tooltip content="删除模型" placement="top">
               <el-button link type="danger" size="small" @click.stop="handleDelete(scope.row)" :disabled="isSimulating(scope.row.id) || isLoadingStatus(scope.row.status)">删除</el-button>
             </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- Details Dialog -->
      <el-dialog
        v-model="isDetailDialogVisible"
        :title="selectedModelDetails ? `模型详情: ${selectedModelDetails.name}` : '模型详情'"
        width="70%"
        top="5vh"
        append-to-body
        destroy-on-close
      >
        <div v-if="isLoadingDetails" class="dialog-loading">加载中...</div>
        <div v-else-if="detailError" class="dialog-error">加载详情失败: {{ detailError }}</div>
        <div v-else-if="selectedModelDetails" class="model-details-content">

          <!-- *** Integrate FineTuneVisualizer here *** -->
          <FineTuneVisualizer
            v-if="isSimulating(selectedModelDetails.id) && simulationStates[selectedModelDetails.id]"
            :model-id="selectedModelDetails.id"
            :simulation-state="simulationStates[selectedModelDetails.id]"
            style="margin-bottom: 25px;"
          />
          <!-- ***************************************** -->
          <FineTuneResultComparer
          v-if="selectedModelDetails.status === 'ready'"
          :fine-tuned-model="selectedModelDetails"
          :base-model-id="selectedModelDetails.base_model_id"
          style="margin-bottom: 25px;"
            />

            <!-- Separator -->
            <el-divider v-if="isSimulating(selectedModelDetails.id) || selectedModelDetails.status === 'ready'"><el-icon><InfoFilled /></el-icon> 基础信息</el-divider>


          <!-- Original Details Descriptions -->
          <!-- <el-descriptions :column="2" border>
             <el-descriptions-item label="模型名称">{{ selectedModelDetails.name }}</el-descriptions-item>
             <el-descriptions-item label="模型 ID">{{ selectedModelDetails.id }}</el-descriptions-item>
             <el-descriptions-item label="最终状态">
                 <el-tag :type="getStatusTagType(selectedModelDetails.status)" size="small">
                      {{ formatStatus(selectedModelDetails.status) }}
                  </el-tag>
             </el-descriptions-item>
             <el-descriptions-item label="基础模型">{{ selectedModelDetails.base_model_id }}</el-descriptions-item>
             <el-descriptions-item label="创建时间">{{ formatTimestamp(selectedModelDetails.creation_timestamp) }}</el-descriptions-item>
             <el-descriptions-item label="完成时间">{{ formatTimestamp(selectedModelDetails.completion_timestamp) }}</el-descriptions-item>
             <el-descriptions-item label="描述" :span="2">{{ selectedModelDetails.description || '-' }}</el-descriptions-item>
             <el-descriptions-item label="样本数据引用" :span="2">{{ selectedModelDetails.sample_data_ref || '-' }}</el-descriptions-item>
             <el-descriptions-item label="模型文件路径" :span="2">{{ selectedModelDetails.model_path || '-' }}</el-descriptions-item>
             <el-descriptions-item label="评估指标" :span="2">
                 <pre v-if="selectedModelDetails.metrics">{{ formatMetricsForDisplay(selectedModelDetails.metrics) }}</pre>
                 <span v-else>-</span>
             </el-descriptions-item>
          </el-descriptions> -->
          <ModelDetailsDisplay :model="selectedModelDetails" />
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="isDetailDialogVisible = false">关闭</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
</template>

<script setup lang="ts">
// Import FineTuneVisualizer
import FineTuneVisualizer from './FineTuneVisualizer.vue';
import FineTuneResultComparer from './FineTuneResultComparer.vue'; // New
import ModelDetailsDisplay from './ModelDetailsDisplay.vue'; // <-- Import new component
// Other imports remain the same
import { InfoFilled } from '@element-plus/icons-vue'; // Icon for divider
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import axios from 'axios';
import {
  ElTable, ElTableColumn, ElButton, ElTag, ElIcon, ElTooltip,
  ElMessageBox, ElMessage, ElDialog, ElDescriptions, ElDescriptionsItem,
  ElProgress, ElDivider
} from 'element-plus';
import { Refresh, Loading } from '@element-plus/icons-vue';
import type { Model, SimulationState, SimulationStage } from './types'; // Assuming types are externalized
// --- Type definitions (Consider moving to a separate types.ts file) ---
interface BaseModel { 
    id: string; 
    name: string; 
    description?: string; 
    metrics?: Record<string, any>; 
}
interface Model {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  base_model_id: string;
  status: 'creating' | 'fine-tuning' | 'ready' | 'failed';
  model_path?: string;
  sample_data_ref?: string;
  creation_timestamp: string;
  completion_timestamp?: string;
  metrics?: Record<string, any>;
}

type SimulationStage =
  | 'queued'
  | 'preparing_data'
  | 'initializing'
  | 'training'
  | 'saving_model'
  | 'evaluating'
  | 'finished'
  | 'error';

interface SimulationState {
  modelId: number;
  currentStage: SimulationStage;
  progress: number;
  timerId?: number;
  simulatedStatus: 'ready' | 'failed';
}
// --- End of Type definitions ---


// --- State ---
const models = ref<Model[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const isDetailDialogVisible = ref(false);
const selectedModelDetails = ref<Model | null>(null);
const isLoadingDetails = ref(false);
const detailError = ref<string | null>(null);
const simulationStates = ref<Record<number, SimulationState>>({});

// --- Simulation Config ---
const simulationConfig: Record<SimulationStage, { duration: number; next: SimulationStage | null; text: string; progressRange: [number, number] }> = {
  queued:           { duration: 1500, next: 'preparing_data', text: '排队等待资源', progressRange: [0, 5] },
  preparing_data:   { duration: 2500, next: 'initializing',   text: '准备数据中...', progressRange: [5, 20] },
  initializing:     { duration: 2000, next: 'training',       text: '初始化模型...', progressRange: [20, 30] },
  training:         { duration: 7000, next: 'saving_model',   text: '模型训练中...', progressRange: [30, 85] },
  saving_model:     { duration: 3000, next: 'evaluating',     text: '保存模型中...', progressRange: [85, 95] },
  evaluating:       { duration: 1500, next: 'finished',       text: '评估结果中...', progressRange: [95, 100] },
  finished:         { duration: 0,    next: null,             text: '已完成',       progressRange: [100, 100] },
  error:            { duration: 0,    next: null,             text: '失败',         progressRange: [0, 0] },
};


// --- API ---
const fetchModels = async () => {
    isLoading.value = true;
    error.value = null;
    stopAllSimulations(); // Stop previous simulations before fetching
    simulationStates.value = {}; // Clear simulation states
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('用户未登录');
        }
        const response = await axios.get<Model[] | { message?: string }>('http://8.148.68.206:5000/api/models', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (Array.isArray(response.data)) {
            models.value = response.data;
            // Start simulation for models in 'creating' or 'fine-tuning' state
            models.value.forEach(model => {
                // Only start if backend status indicates processing AND not already simulating
                if ((model.status === 'creating' || model.status === 'fine-tuning') && !simulationStates.value[model.id]) {
                    startFineTuneSimulation(model);
                }
            });
        } else {
            const errorMessage = (typeof response.data === 'object' && response.data?.message) ? response.data.message : '无效的响应格式';
            throw new Error(`获取模型列表失败: ${errorMessage}`);
        }
    } catch (err: any) {
        console.error('获取模型列表失败:', err);
        error.value = err.message || '获取模型列表失败';
        ElMessage.error(error.value);
        models.value = []; // Clear models on error
    } finally {
        isLoading.value = false;
    }
};

const deleteModel = async (modelId: number) => {
    try {
        stopSimulation(modelId); // Stop simulation before deleting
        const token = localStorage.getItem('token');
        if (!token) throw new Error('用户未登录');
        await axios.delete(`http://8.148.68.206:5000/api/models/${modelId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        ElMessage.success('模型删除成功');
        // Close details dialog if the deleted model was being viewed
        if(selectedModelDetails.value?.id === modelId){
            isDetailDialogVisible.value = false;
            selectedModelDetails.value = null;
        }
        // Remove from local list
        models.value = models.value.filter(m => m.id !== modelId);
    } catch (err: any) {
        console.error(`删除模型 ${modelId} 失败:`, err);
        const message = err.response?.data?.message || err.message || '未知错误';
        ElMessage.error(`删除模型失败: ${message}`);
    }
};

// --- Simulation Logic ---
const startFineTuneSimulation = (model: Model) => {
  if (simulationStates.value[model.id]) {
      console.warn(`模型 ${model.id} 已在模拟中，跳过启动。`);
      return;
  }
  console.log(`启动模型 ${model.id} (${model.name}) 的微调过程模拟...`);
  const shouldSucceed = Math.random() < 0.8;
  const finalStatus = shouldSucceed ? 'ready' : 'failed';

  simulationStates.value[model.id] = {
    modelId: model.id,
    currentStage: 'queued',
    progress: 0,
    timerId: undefined,
    simulatedStatus: finalStatus
  };
  scheduleNextStage(model.id, 'queued');
};

const scheduleNextStage = (modelId: number, stage: SimulationStage) => {
  const currentState = simulationStates.value[modelId];
  if (!currentState || currentState.currentStage === 'finished' || currentState.currentStage === 'error') {
      return;
  }
  const config = simulationConfig[stage];
  if (!config) {
      console.error(`未找到模型 ${modelId} 阶段 ${stage} 的模拟配置。`);
      stopSimulation(modelId);
      return;
  }

  const duration = config.duration;
  const [startProgress, endProgress] = config.progressRange;

  currentState.currentStage = stage;
  currentState.progress = startProgress;

   let progressIntervalId: number | undefined = undefined;
   if (duration > 0 && startProgress < endProgress) {
       const steps = 10;
       const stepDuration = Math.max(50, duration / steps);
       const progressIncrement = (endProgress - startProgress) / steps;
       let currentStep = 0;
       const updateProgress = () => {
           const state = simulationStates.value[modelId];
           if (state && currentStep < steps) {
               state.progress = Math.min(endProgress, Math.round(startProgress + (currentStep + 1) * progressIncrement));
               currentStep++;
               progressIntervalId = window.setTimeout(updateProgress, stepDuration);
           } else { if(progressIntervalId) clearTimeout(progressIntervalId); }
       };
       progressIntervalId = window.setTimeout(updateProgress, stepDuration);
   } else {
       currentState.progress = endProgress;
   }

  const timerId = window.setTimeout(() => {
    if (progressIntervalId) clearTimeout(progressIntervalId);
    const stateAfterTimeout = simulationStates.value[modelId];
    if (!stateAfterTimeout) return;
    stateAfterTimeout.progress = endProgress;
    if (config.next) {
      scheduleNextStage(modelId, config.next);
    } else {
      handleSimulationEnd(modelId);
    }
  }, duration);
  currentState.timerId = timerId;
};

const handleSimulationEnd = (modelId: number) => {
    const finalState = simulationStates.value[modelId];
    if (!finalState) return;
    const modelIndex = models.value.findIndex(m => m.id === modelId);
    if (modelIndex !== -1) {
        const updatedModelData = { ...models.value[modelIndex] };
        updatedModelData.status = finalState.simulatedStatus;
        updatedModelData.completion_timestamp = new Date().toISOString();
        if (finalState.simulatedStatus === 'ready') {
             updatedModelData.metrics = { accuracy: +(Math.random() * 0.2 + 0.75).toFixed(2), loss: +(Math.random() * 0.2 + 0.05).toFixed(2) };
             updatedModelData.model_path = `model_${modelId}_weights_simulated.h5`;
             setTimeout(() => ElMessage.success(`模型 "${updatedModelData.name}" 模拟微调完成！`), 300);
        } else {
             updatedModelData.metrics = undefined;
             updatedModelData.model_path = undefined;
             setTimeout(() => ElMessage.error(`模型 "${updatedModelData.name}" 模拟微调失败。`), 300);
        }
        models.value[modelIndex] = updatedModelData;
         if (isDetailDialogVisible.value && selectedModelDetails.value?.id === modelId) {
             selectedModelDetails.value = { ...updatedModelData };
         }
    }
    delete simulationStates.value[modelId];
     console.log(`Simulation state removed for model ${modelId}.`);
};

const stopSimulation = (modelId: number) => {
    const state = simulationStates.value[modelId];
    if (state) { if (state.timerId) clearTimeout(state.timerId); delete simulationStates.value[modelId]; console.log(`已手动停止模型 ${modelId} 的模拟。`); }
};

const stopAllSimulations = () => {
    Object.keys(simulationStates.value).forEach(idStr => stopSimulation(parseInt(idStr, 10)));
    simulationStates.value = {};
};

// --- Computed / Helpers for Display ---
const isSimulating = (modelId: number): boolean => !!simulationStates.value[modelId];
const getSimulationProgress = (modelId: number): number => simulationStates.value[modelId]?.progress ?? 0;
const getSimulationStage = (modelId: number): SimulationStage | undefined => simulationStates.value[modelId]?.currentStage;
const getDisplayStatusText = (modelId: number, backendStatus: Model['status']): string => {
  const sim = simulationStates.value[modelId];
  return sim ? (simulationConfig[sim.currentStage]?.text ?? formatStatus(backendStatus)) : formatStatus(backendStatus);
};
const getDisplayStatusTagType = (modelId: number, backendStatus: Model['status']): 'primary' | 'warning' | 'success' | 'danger' | 'info' => {
    const sim = simulationStates.value[modelId];
    if (sim) {
        if (sim.currentStage === 'finished') return getStatusTagType(sim.simulatedStatus);
        if (sim.currentStage === 'error') return 'danger';
        if (['training', 'saving_model', 'evaluating'].includes(sim.currentStage)) return 'warning';
        return 'primary';
    } return getStatusTagType(backendStatus);
};
const getSimulationProgressStatus = (modelId: number): "" | "success" | "warning" | "exception" => {
    const sim = simulationStates.value[modelId];
    if(sim){
        if(sim.currentStage === 'error' || sim.simulatedStatus === 'failed') return 'exception';
        if(sim.currentStage === 'finished' && sim.simulatedStatus === 'ready') return 'success';
    } return "";
};
const formatTimestamp = (timestamp: string | undefined | null): string => {
  if (!timestamp) return '-';
  try { const date = new Date(timestamp); return isNaN(date.getTime()) ? '无效日期' : date.toLocaleString(); }
  catch (e) { return '日期格式错误'; }
};
const formatStatus = (status: Model['status']): string => {
    const map: Record<Model['status'], string> = { 'creating': '创建中', 'fine-tuning': '处理中', 'ready': '准备就绪', 'failed': '失败' }; return map[status] || status;
};
const getStatusTagType = (status: Model['status']): 'primary' | 'warning' | 'success' | 'danger' | 'info' => {
     const map: Record<Model['status'], 'primary' | 'warning' | 'success' | 'danger' | 'info'> = { 'creating': 'primary', 'fine-tuning': 'warning', 'ready': 'success', 'failed': 'danger' }; return map[status] || 'info';
};
const isLoadingStatus = (status: Model['status']): boolean => status === 'creating' || status === 'fine-tuning';
const formatMetricsForDisplay = (metrics: Record<string, any> | undefined | null): string => {
    if (!metrics || Object.keys(metrics).length === 0) return '-'; try { return JSON.stringify(metrics, null, 2); } catch { return '无法解析指标'; }
};


// --- Methods ---
const refreshModels = async () => {
  console.log('刷新我的模型库列表...');
  await fetchModels();
};

const handleDelete = async (model: Model) => {
    if (isSimulating(model.id)) { ElMessage.warning('模型正在模拟处理中，请稍后删除。'); return; }
    if (isLoadingStatus(model.status)) { ElMessage.warning('模型状态未定，无法删除。'); return; }
    try { await ElMessageBox.confirm(`确定删除模型 "${model.name}"?`, '确认删除', { type: 'warning' }); await deleteModel(model.id); }
    catch (action) { if (action === 'cancel') ElMessage.info('已取消删除'); }
};

const handleViewDetails = async (model: Model | null) => {
    console.log('handleViewDetails called with model:', model);
    if (!model) { console.error("handleViewDetails called with null model."); return; }
    selectedModelDetails.value = null; detailError.value = null; isLoadingDetails.value = true; isDetailDialogVisible.value = true;
    try {
        console.log(`Fetching details for model ID: ${model.id}`);
        const token = localStorage.getItem('token'); if (!token) throw new Error('用户未登录');
        const response = await axios.get<Model>(`http://8.148.68.206:5000/api/models/${model.id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        await nextTick();
        selectedModelDetails.value = response.data;
        console.log('Details fetched successfully:', selectedModelDetails.value);
    } catch (err: any) {
        console.error(`获取模型 ${model.id} 详情失败:`, err);
        const message = err.response?.data?.message || err.message || '加载失败'; detailError.value = message;
        ElMessage.error(`加载模型详情失败: ${detailError.value}`);
    } finally { isLoadingDetails.value = false; }
};

// --- Lifecycle ---
onMounted(() => { fetchModels(); });
onUnmounted(() => { stopAllSimulations(); });

// --- Expose ---
defineExpose({
  refreshModels,
  triggerSimulationForModel: (modelId: number) => {
      const model = models.value.find(m => m.id === modelId);
      if (model) { if(model.status === 'ready' || model.status === 'failed') { console.log(`模型 ${modelId} 状态已为 ${model.status}，不启动模拟。`); return; } if (!isSimulating(modelId)) startFineTuneSimulation(model); else console.warn(`模型 ${modelId} 已在模拟中。`); }
      else { console.error(`无法为不存在的模型 ${modelId} 触发模拟。`); ElMessage.error(`无法为模型 ${modelId} 启动模拟，请刷新列表重试。`); }
  },
  openDetailsForModel: async (modelId: number) => {
      console.log(`Exposed method openDetailsForModel called for ID: ${modelId}`);
      const model = models.value.find(m => m.id === modelId);
      if (model) { console.log(`Model ${modelId} found in list, calling handleViewDetails...`); await handleViewDetails(model); }
      else { console.warn(`无法自动打开详情：模型 ${modelId} 在当前列表中未找到。`); try { await handleViewDetails({ id: modelId } as Model); } catch (e) { console.error(`尝试直接获取模型 ${modelId} 详情失败:`, e); ElMessage.error(`无法打开模型 ${modelId} 的详情，请尝试刷新列表。`); } }
  }
});
</script>

<style scoped>
.model-library { 
    display: flex; 
    flex-direction: column; 
    height: 100%; 
    gap: 15px; 
}
.toolbar { 
    flex-shrink: 0; 
    margin-bottom: 10px; 
}
.el-table { 
    flex-grow: 1; 
    border: 1px solid #ebeef5; 
    border-radius: 4px; 
}
:deep(.el-table th.el-table__cell), :deep(.el-table td.el-table__cell) { 
        padding: 10px 0; 
    }
.status-cell { 
    display: flex; 
    flex-direction: column; 
    justify-content: center; 
    gap: 5px; 
    min-height: 32px; 
}
.status-tag { 
    width: fit-content; 
}
.status-progress { 
    width: 100%; 
}
.status-progress :deep(.el-progress-bar__outer) { 
    background-color: #e9ecef; 
}
.status-loading-icon { 
    margin-right: 4px; 
    vertical-align: middle; 
}
.el-tag .el-icon.is-loading { 
    animation: rotating 1.8s linear infinite; 
}
.status-loading-icon.pulsing { 
    animation: rotating 1.5s linear infinite, pulse 1.2s infinite alternate; 
}
@keyframes pulse { from { opacity: 1; transform: scale(1); } to { opacity: 0.6; transform: scale(1.1); } }
.el-table-column--operation .el-button + .el-button { 
    margin-left: 8px; 
}
.model-details-content { 
    max-height: calc(80vh - 120px); 
    overflow-y: auto; 
    padding: 0 10px 10px 0; 
}
.model-details-content .el-descriptions { 
    margin-top: 10px; 
}
.model-details-content pre { 
    white-space: pre-wrap; 
    word-wrap: break-word; 
    background-color: #f8f9fa; 
    padding: 10px 15px; 
    border-radius: 4px; 
    border: 1px solid #dee2e6; 
    font-family: 'Courier New', Courier, monospace; 
    font-size: 0.85em; 
    line-height: 1.6; 
    max-height: 200px; 
    overflow-y: auto; 
}
/* Keep simulation info styles if needed for fallback, but visualizer handles it now */
/* .simulation-info-dialog { margin-bottom: 20px; padding: 15px; background-color: #f0f9eb; border: 1px solid #e1f3d8; border-radius: 4px; } */
/* .simulation-info-dialog.is-failed { background-color: #fef0f0; border-color: #fde2e2; } */
/* .simulation-info-dialog .el-descriptions { background-color: transparent; border: none; } */
/* .simulation-info-dialog :deep(.el-descriptions__label) { font-weight: normal; color: #555; } */
/* .simulation-info-dialog :deep(.el-descriptions__content) { font-weight: bold; } */
.dialog-loading, .dialog-error { 
    text-align: center; 
    padding: 40px 20px; 
    color: #6c757d; 
    font-size: 1.1em; 
}
.dialog-error { 
    color: #dc3545; 
}
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>