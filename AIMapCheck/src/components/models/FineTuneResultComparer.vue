<template>
    <div class="fine-tune-result-comparer">
      <h4>模型效果对比</h4>
  
      <el-row :gutter="20">
        <!-- 指标对比 -->
        <el-col :span="12">
          <el-card shadow="never" class="comparison-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><DataAnalysis /></el-icon> 关键指标对比</span>
              </div>
            </template>
            <div v-if="isLoadingMetrics" class="loading-placeholder">正在加载指标...</div>
            <div v-else-if="metricsError" class="error-placeholder">加载指标失败: {{ metricsError }}</div>
            <div v-else class="metrics-comparison">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item v-for="metric in comparableMetrics" :key="metric.key" :label="metric.label">
                  <div class="metric-row">
                     <el-tag type="info" size="small" effect="light" class="metric-tag">基础模型</el-tag>
                     <span>{{ baseMetrics[metric.key] ?? 'N/A' }}</span>
                     <el-icon v-if="getMetricChangeIcon(metric.key)" :color="getMetricChangeColor(metric.key)">
                       <component :is="getMetricChangeIcon(metric.key)" />
                     </el-icon>
                     <el-tag type="success" size="small" effect="dark" class="metric-tag">微调模型</el-tag>
                     <span :style="{ color: getMetricChangeColor(metric.key), fontWeight: 'bold' }">
                         {{ fineTunedMetrics[metric.key] ?? 'N/A' }}
                     </span>
                  </div>
                </el-descriptions-item>
              </el-descriptions>
               <p v-if="comparableMetrics.length === 0" class="no-metrics">暂无可对比的指标。</p>
               <!-- TODO: 未来可加入指标对比图表 (如雷达图) -->
            </div>
          </el-card>
        </el-col>
  
        <!-- Side-by-Side 推理对比 -->
        <el-col :span="12">
          <el-card shadow="never" class="comparison-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><View /></el-icon> 推理效果对比 (示例)</span>
              </div>
            </template>
            <div class="inference-section">
              <div class="inference-input">
                <label>选择或上传测试样本:</label>
                <!-- TODO: 实现样本选择或上传逻辑 -->
                <el-select v-model="selectedSample" placeholder="选择预设样本" size="small" style="width: 150px; margin: 0 10px;">
                  <el-option label="样本 A" value="sample_a.jpg"></el-option>
                  <el-option label="样本 B" value="sample_b.png"></el-option>
                </el-select>
                <el-button @click="runInferenceComparison" :loading="isInferring" size="small" type="primary">运行对比</el-button>
              </div>
  
              <div v-if="isInferring" class="loading-placeholder">正在运行推理...</div>
              <div v-else-if="inferenceError" class="error-placeholder">推理失败: {{ inferenceError }}</div>
              <div v-else class="inference-results">
                <el-row :gutter="10">
                  <el-col :span="12">
                    <h5>基础模型输出</h5>
                    <div class="result-display placeholder">
                        <!-- TODO: 根据任务类型展示推理结果 (图片/文本等) -->
                       基础模型结果展示区域
                       <div v-if="baseModelResult"> {{ baseModelResult }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <h5>微调模型输出</h5>
                    <div class="result-display placeholder">
                         <!-- TODO: 根据任务类型展示推理结果 (图片/文本等) -->
                         微调模型结果展示区域
                         <div v-if="fineTunedModelResult"> {{ fineTunedModelResult }}</div>
                         <!-- TODO: 添加差异高亮逻辑 -->
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted, PropType, watch } from 'vue';
  import axios from 'axios';
  import { ElRow, ElCol, ElCard, ElIcon, ElDescriptions, ElDescriptionsItem, ElTag, ElSelect, ElOption, ElButton } from 'element-plus';
  import { DataAnalysis, View, Loading, CaretTop, CaretBottom, Warning } from '@element-plus/icons-vue';
  import type { Model } from './types'; // 假设 Model 类型定义在外部
  
  // --- Props ---
  const props = defineProps({
    fineTunedModel: {
      type: Object as PropType<Model>,
      required: true,
    },
    baseModelId: {
      type: String,
      required: true,
    }
  });
  
  // --- State ---
  const baseMetrics = ref<Record<string, any>>({}); // 基础模型的指标
  const fineTunedMetrics = computed(() => props.fineTunedModel.metrics || {}); // 微调模型的指标
  const isLoadingMetrics = ref(false);
  const metricsError = ref<string | null>(null);
  
  const selectedSample = ref<string | null>(null); // 当前选择的测试样本
  const isInferring = ref(false);
  const inferenceError = ref<string | null>(null);
  const baseModelResult = ref<any>(null); // 基础模型推理结果
  const fineTunedModelResult = ref<any>(null); // 微调模型推理结果
  
  // --- Metrics Comparison Logic ---
  
  // 定义哪些指标需要对比，以及它们的显示名称和优化方向
  const comparableMetricsConfig = [
      { key: 'accuracy', label: '准确率', higherIsBetter: true },
      { key: 'loss', label: '损失值', higherIsBetter: false },
      { key: 'precision', label: '精确率', higherIsBetter: true },
      { key: 'recall', label: '召回率', higherIsBetter: true },
      { key: 'f1_score', label: 'F1 分数', higherIsBetter: true },
      // 可以根据需要添加更多指标
  ];
  
  // 计算实际存在的、可对比的指标
  const comparableMetrics = computed(() => {
      return comparableMetricsConfig.filter(metricConf =>
          metricConf.key in fineTunedMetrics.value || metricConf.key in baseMetrics.value
      );
  });
  
  // 获取基础模型指标的API (模拟)
  const fetchBaseModelMetrics = async (baseId: string) => {
    isLoadingMetrics.value = true;
    metricsError.value = null;
    baseMetrics.value = {}; // Clear previous
    try {
      console.log(`Fetching metrics for base model: ${baseId}`);
      // ** TODO: 替换为真实的 API 调用 **
      // const response = await axios.get(`/api/base-models/${baseId}/metrics`);
      // baseMetrics.value = response.data;
  
      // --- 模拟 API 调用 ---
      await new Promise(resolve => setTimeout(resolve, 1200)); // Simulate network delay
      // 模拟一些基础模型的指标数据
      if (baseId === 'generic-map-v1') {
          baseMetrics.value = { accuracy: 0.78, loss: 0.25, f1_score: 0.75 };
      } else if (baseId === 'building-dense-v1.2') {
           baseMetrics.value = { accuracy: 0.85, loss: 0.18, precision: 0.82, recall: 0.88 };
      } else {
           baseMetrics.value = { accuracy: Math.random() * 0.1 + 0.7, loss: Math.random() * 0.1 + 0.2 }; // Fallback random
      }
      // --- 结束模拟 ---
  
    } catch (error: any) {
      console.error(`获取基础模型 ${baseId} 指标失败:`, error);
      metricsError.value = error.message || '无法加载基础模型指标';
    } finally {
      isLoadingMetrics.value = false;
    }
  };
  
  // 根据指标变化返回图标
  const getMetricChangeIcon = (metricKey: string): any => {
      const config = comparableMetricsConfig.find(m => m.key === metricKey);
      if (!config) return null;
      const baseValue = baseMetrics.value[metricKey];
      const tunedValue = fineTunedMetrics.value[metricKey];
      if (baseValue == null || tunedValue == null || baseValue == tunedValue) return null; // 无变化或数据不全
  
      const improved = config.higherIsBetter ? tunedValue > baseValue : tunedValue < baseValue;
      return improved ? CaretTop : CaretBottom;
  };
  
  // 根据指标变化返回颜色
  const getMetricChangeColor = (metricKey: string): string | null => {
      const config = comparableMetricsConfig.find(m => m.key === metricKey);
      if (!config) return null;
      const baseValue = baseMetrics.value[metricKey];
      const tunedValue = fineTunedMetrics.value[metricKey];
  
      if (baseValue == null || tunedValue == null || baseValue == tunedValue) return null;
  
      const improved = config.higherIsBetter ? tunedValue > baseValue : tunedValue < baseValue;
      return improved ? '#67c23a' : '#f56c6c'; // Element Plus success/danger colors
  };
  
  
  // --- Side-by-Side Inference Logic (Placeholder) ---
  
  const runInferenceComparison = async () => {
    if (!selectedSample.value) {
      alert("请先选择一个测试样本");
      return;
    }
    isInferring.value = true;
    inferenceError.value = null;
    baseModelResult.value = null;
    fineTunedModelResult.value = null;
  
    try {
      console.log(`Running inference comparison for sample: ${selectedSample.value}`);
      console.log(`Base model: ${props.baseModelId}, Fine-tuned model: ${props.fineTunedModel.id}`);
  
      // ** TODO: 实现真实的 API 调用以进行推理 **
      // 1. 调用基础模型推理 API
      // const baseResponse = await axios.post(`/api/infer?model_id=${props.baseModelId}`, { sample: selectedSample.value });
      // baseModelResult.value = baseResponse.data.result; // 根据后端返回结构调整
  
      // 2. 调用微调模型推理 API
      // const tunedResponse = await axios.post(`/api/infer?model_id=${props.fineTunedModel.id}`, { sample: selectedSample.value });
      // fineTunedModelResult.value = tunedResponse.data.result; // 根据后端返回结构调整
  
      // --- 模拟 API 调用 ---
      await new Promise(resolve => setTimeout(resolve, 2500)); // Simulate inference time
      baseModelResult.value = `基础模型 (${props.baseModelId}) 对 ${selectedSample.value} 的模拟输出结果：检测到 3 个低风险问题。`;
      fineTunedModelResult.value = `微调模型 (${props.fineTunedModel.id}) 对 ${selectedSample.value} 的模拟输出结果：检测到 1 个低风险问题，精度更高。`;
      // --- 结束模拟 ---
  
    } catch (error: any) {
      console.error('推理对比失败:', error);
      inferenceError.value = error.message || '推理过程中发生错误';
    } finally {
      isInferring.value = false;
    }
  };
  
  // --- Lifecycle ---
  onMounted(() => {
    fetchBaseModelMetrics(props.baseModelId);
  });
  
  // Watch for model changes (e.g., if the dialog stays open while list refreshes)
  watch(() => props.baseModelId, (newId) => {
      fetchBaseModelMetrics(newId);
      // Reset inference state if base model changes
      selectedSample.value = null;
      baseModelResult.value = null;
      fineTunedModelResult.value = null;
      inferenceError.value = null;
  });
  
  </script>
  
  <style scoped>
  .fine-tune-result-comparer h4 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #495057;
    font-weight: 600;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 10px;
  }
  
  .comparison-card {
    height: 350px; /* Adjust height as needed */
    display: flex;
    flex-direction: column;
  }
  
  .comparison-card :deep(.el-card__body) {
    flex-grow: 1;
    overflow-y: auto;
  }
  
  .card-header {
    display: flex;
    align-items: center;
    font-size: 0.95em;
  }
  .card-header .el-icon {
    margin-right: 6px;
  }
  
  .loading-placeholder, .error-placeholder {
    text-align: center;
    color: #909399;
    padding: 20px;
  }
  .error-placeholder {
    color: #f56c6c;
  }
  .no-metrics {
    text-align: center;
    color: #909399;
    margin-top: 15px;
  }
  
  .metrics-comparison .el-descriptions {
      margin-top: 10px;
  }
  
  .metric-row {
      display: flex;
      align-items: center;
      gap: 8px; /* Space between elements */
      font-size: 0.9em;
  }
  .metric-row .el-icon {
      margin-left: 4px; /* Space before icon */
  }
  .metric-tag {
      flex-shrink: 0; /* Prevent tags from shrinking */
  }
  
  
  .inference-section {
      display: flex;
      flex-direction: column;
      height: 100%; /* Make section fill card body */
  }
  .inference-input {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
      flex-shrink: 0; /* Prevent input area from shrinking */
      font-size: 0.9em;
  }
  .inference-input label {
      margin-right: 5px;
  }
  
  .inference-results {
      flex-grow: 1; /* Allow results area to take remaining space */
      overflow-y: auto; /* Scroll if results are long */
  }
  
  .result-display {
    border: 1px dashed #dcdfe6;
    padding: 15px;
    min-height: 150px; /* Minimum height for display area */
    border-radius: 4px;
    background-color: #fafafa;
    font-size: 0.9em;
    overflow: auto; /* Scroll if content inside overflows */
  }
  .result-display.placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #c0c4cc;
  }
  
  .inference-results h5 {
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 0.95em;
      color: #606266;
      text-align: center;
  }
  </style>