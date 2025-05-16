<template>
  <div class="stage-detail">
    <div class="panel-overlay" @click="$emit('close')"></div>
    <div class="panel-content">
      <div class="panel-header">
        <h3>设置阶段 - 选择模型与模式</h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="panel-body" v-loading="isLoadingInitialSettings">
        <div class="section">
          <h4>选择审查模型</h4>
          <el-select
            v-model="selectedModelId"
            placeholder="请选择模型"
            style="width: 100%"
            filterable
            :loading="isLoadingModels"
            @change="handleModelSelectionChange"
            :disabled="isLoadingInitialSettings"
          >
            <el-option-group key="my-models" label="我的微调模型">
              <el-option
                v-for="model in userModels"
                :key="model.id"
                :label="`${model.name} (微调)`"
                :value="model.id"
                :disabled="model.status !== 'ready'"
              >
                <span style="float: left">{{ model.name }}</span>
                <el-tag
                  v-if="model.status !== 'ready'"
                  type="warning"
                  size="small"
                  style="float: right; margin-left: 10px;"
                  effect="light"
                >
                  {{ formatStatus(model.status) }}
                </el-tag>
                 <span v-else style="float: right; color: var(--el-text-color-secondary); font-size: 13px;">
                    ID: {{ model.id }}
                 </span>
              </el-option>
               <el-option v-if="!isLoadingModels && userModels.length === 0" label="无可用微调模型" value="no-user-models" disabled />
            </el-option-group>

            <el-option-group key="base-models" label="基础模型">
              <el-option
                v-for="model in baseModels"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              >
                 <span style="float: left">{{ model.name }}</span>
                 <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px;">
                   基础
                 </span>
              </el-option>
               <el-option v-if="!isLoadingModels && baseModels.length === 0" label="无可用基础模型" value="no-base-models" disabled />
            </el-option-group>
          </el-select>
          <div v-if="selectedModelDescription" class="model-description">
             {{ selectedModelDescription }}
          </div>
           <div v-if="isLoadingModels && !isLoadingInitialSettings" class="loading-text">加载模型列表中...</div>
        </div>

        <div class="section">
          <h4>选择审查模式</h4>
          <el-radio-group v-model="reviewMode" @change="handleModeChange" :disabled="isLoadingInitialSettings">
            <el-radio-button label="fast">快速模式</el-radio-button>
            <el-radio-button label="standard">标准模式</el-radio-button>
            <el-radio-button label="strict">严格模式</el-radio-button>
          </el-radio-group>
           <div class="mode-description">
             {{ modeDescriptions[reviewMode] }}
           </div>
        </div>

        <div class="actions">
          <el-button
             type="primary"
             @click="handleConfirm"
             :disabled="!selectedModelId || isLoadingModels || isLoadingInitialSettings || isSaving"
             :loading="isSaving"
             >
             确认设置并进入下一阶段
             </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { ElMessage, ElSelect, ElOption, ElOptionGroup, ElRadioGroup, ElRadioButton, ElButton, ElTag } from 'element-plus';
import axios from 'axios';
import { useRoute } from 'vue-router';
// Assuming types are correctly defined in this path or globally
// If not, define them here or fix the import path
import type { Model } from '@/components/models/types';

// --- Interfaces ---
interface BaseModel {
  id: string;
  name: string;
  description?: string;
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

// --- Emits ---
const emit = defineEmits<{
  (e: 'update:selectedModelId', modelId: number | string | null): void, // Still needed for parent->visualization update
  (e: 'update:reviewMode', mode: ReviewMode): void, // <-- Add emit for reviewMode
  (e: 'settingsSaved'): void, // Notify parent that save was successful (to trigger next stage logic)
  (e: 'close'): void
}>();

// --- State ---
const route = useRoute();
const taskId = computed(() => parseInt(route.params.id as string)); // Make taskId computed

type ReviewMode = 'fast' | 'standard' | 'strict';

const userModels = ref<Model[]>([]);
const baseModels = ref<BaseModel[]>([]);
const isLoadingModels = ref(false);
const isLoadingInitialSettings = ref(true); // New loading state for initial settings
const isSaving = ref(false); // Loading state for save button

const selectedModelId = ref<number | string | null>(null); // Initialize as null
const reviewMode = ref<ReviewMode>('standard'); // Default mode

const modeDescriptions: Record<string, string> = {
  fast: '快速审查 - 优先速度，检查核心问题。',
  standard: '标准审查 - 平衡速度与全面性，检查常见问题。',
  strict: '严格审查 - 最全面，检查所有潜在问题和规范。'
};

// Compute description for the selected model
const selectedModelDescription = computed(() => {
    if (!selectedModelId.value) return '';
    // Combine both lists to find the selected model
    const allModels: (BaseModel | Model)[] = [...baseModels.value, ...userModels.value];
    const selected = allModels.find(m => m.id === selectedModelId.value);
    return selected?.description || (selected ? `模型: ${selected.name}` : '');
});

// --- Methods ---

// Fetch saved settings for the current task
const loadCurrentSettings = async () => {
    isLoadingInitialSettings.value = true;
    try {
        console.log(`Loading settings for task ${taskId.value}`);
        const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId.value}/settings`, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (response.data && response.data.settings) {
             const settings = response.data.settings;
             console.log("Loaded settings:", settings);
             // Set the initial values based on fetched data
             // Ensure correct type comparison/assignment if needed
             selectedModelId.value = settings.selected_model_id ?? null;
             reviewMode.value = settings.review_mode ?? 'standard';

             // Emit the loaded model ID so the visualization updates
             emit('update:selectedModelId', selectedModelId.value);
        } else {
            console.log("No previous settings found for this task or invalid response.");
             // Keep defaults, but still emit the initial (likely null) model ID
             emit('update:selectedModelId', selectedModelId.value);
        }
    } catch (error: any) {
        console.error('加载任务设置失败:', error);
        // Don't show error message on initial load failure, just use defaults
        // ElMessage.error('加载当前任务设置失败');
        // Emit null so visualization knows nothing is selected
        emit('update:selectedModelId', null);
    } finally {
        isLoadingInitialSettings.value = false;
    }
};

// Fetch models from backend
const fetchAllModels = async () => {
    isLoadingModels.value = true;
    try {
        const token = localStorage.getItem('token');
        const requests = [
            axios.get<BaseModel[]>('http://8.148.68.206:5000/api/base-models') // Use relative URL or env var
        ];
        if (token) {
            requests.push(axios.get<Model[]>('http://8.148.68.206:5000/api/models', { // Use relative URL or env var
                headers: { 'Authorization': `Bearer ${token}` }
            }));
        }

        const [baseResponse, userResponse] = await Promise.allSettled(requests);

        if (baseResponse.status === 'fulfilled' && Array.isArray(baseResponse.value.data)) {
             baseModels.value = baseResponse.value.data;
        } else {
             console.error('获取基础模型失败:', baseResponse.status === 'rejected' ? baseResponse.reason : 'Invalid data');
             ElMessage.error('加载基础模型列表失败');
        }

        if (userResponse?.status === 'fulfilled' && Array.isArray(userResponse.value.data)) {
             userModels.value = userResponse.value.data;
        } else if (token) { // Only error if logged in and failed
             console.error('获取用户模型失败:', userResponse?.status === 'rejected' ? userResponse.reason : 'Invalid data');
             ElMessage.error('加载您的微调模型列表失败');
        } else {
             userModels.value = []; // Ensure empty if not logged in
        }

         // If after loading models, still no model is selected (e.g., saved one was deleted or first load)
         // Set a default selection logic here if needed, *after* settings load attempt in onMounted
         if (!selectedModelId.value) {
             setDefaultModelSelection();
             // Emit the default selection if it changed
             emit('update:selectedModelId', selectedModelId.value);
         }

    } catch (error) {
        console.error("Model fetching combined error:", error);
    } finally {
        isLoadingModels.value = false;
    }
};

// Set default model selection (e.g., first base model)
const setDefaultModelSelection = () => {
     if (baseModels.value.length > 0) {
        selectedModelId.value = baseModels.value[0].id;
        console.log("Defaulting selection to first base model:", selectedModelId.value);
     } else {
        const firstReadyUserModel = userModels.value.find(m => m.status === 'ready');
        if (firstReadyUserModel) {
            selectedModelId.value = firstReadyUserModel.id;
            console.log("Defaulting selection to first ready user model:", selectedModelId.value);
        } else {
            console.log("No available models to select by default.");
            selectedModelId.value = null; // Explicitly set to null if none available
        }
     }
};

// Emit changes when model selection changes
const handleModelSelectionChange = (newModelId: number | string | null) => {
  emit('update:selectedModelId', newModelId);
};

const handleModeChange = (newMode: ReviewMode) => {
  // This change is local until confirmed
  emit('update:reviewMode', newMode);
};

// Save settings to backend
const handleConfirm = async () => {
  if (!selectedModelId.value) {
    ElMessage.warning('请先选择一个审查模型');
    return;
  }
  isSaving.value = true;
  try {
    const settingsData = {
      selected_model_id: selectedModelId.value,
      review_mode: reviewMode.value,
      timestamp: new Date().toISOString()
    };

    const response = await axios.post(
      `http://8.148.68.206:5000/api/tasks/${taskId.value}/settings`,
      settingsData,
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );

    if (response.data && response.data.success) {
      ElMessage.success('设置已成功保存');
      emit('settingsSaved'); // Notify parent
      emit('close');
    } else {
       ElMessage.error(response.data?.message || '保存设置失败');
    }
  } catch (error: any) {
    console.error('保存设置失败:', error);
    ElMessage.error(`保存设置失败: ${error.response?.data?.message || error.message}`);
  } finally {
    isSaving.value = false;
  }
};

// Helper to format status
const formatStatus = (status: Model['status']): string => {
    const map: Record<Model['status'], string> = { 'creating': '创建中', 'fine-tuning': '处理中', 'ready': '准备就绪', 'failed': '失败' };
    return map[status] || status;
};

// --- Lifecycle ---
onMounted(async () => {
  // First, try to load any existing settings
  await loadCurrentSettings();
  // Then, load all available models for the dropdown
  await fetchAllModels();
  // The default selection logic inside fetchAllModels handles setting a default
  // if loadCurrentSettings didn't provide a valid initial ID.
});

</script>

<style scoped>
/* Styles remain largely the same */
.stage-detail { position: fixed; top: 0; right: 0; bottom: 0; width: 100%; z-index: 1000; display: flex; justify-content: flex-end; }
.panel-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); }
.panel-content { position: relative; width: 450px; height: 100%; background: white; box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1); display: flex; flex-direction: column; z-index: 1; }
.panel-header { padding: 20px; border-bottom: 1px solid #e0e5f2; display: flex; justify-content: space-between; align-items: center; }
.panel-header h3 { margin: 0; font-size: 18px; color: #2b3674; }
.close-btn { background: none; border: none; font-size: 18px; color: #707eae; cursor: pointer; padding: 4px; }
.close-btn:hover { color: #2b3674; }
.panel-body { flex: 1; padding: 25px; overflow-y: auto; }
.section { margin-bottom: 35px; }
.section h4 { margin-bottom: 15px; color: #333; font-size: 1.1em; }
.model-description, .mode-description { font-size: 0.85em; color: #6c757d; /* Bootstrap secondary color */ margin-top: 8px; padding-left: 5px; line-height: 1.4; }
.loading-text { font-size: 0.9em; color: #909399; margin-top: 10px; }
.actions { margin-top: 40px; text-align: right; border-top: 1px solid #eee; padding-top: 20px; }
</style>