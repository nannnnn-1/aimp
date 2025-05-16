<template>
  <div class="settings-visualization">
    <div class="visualization-container">
      <div class="model-preview">
        <h4>模型详情预览</h4>
        <div v-if="isLoadingDetails" class="loading-placeholder">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>加载模型信息...</span>
        </div>
        <div v-else-if="detailError" class="error-placeholder">
            <el-icon><Warning /></el-icon>
           <span>加载失败: {{ detailError }}</span>
        </div>
        <ModelDetailsDisplay v-else-if="currentModelDetails" :model="currentModelDetails" class="preview-details"/>
         <div v-else class="loading-placeholder">请在左侧选择一个模型</div>
      </div>

      <div class="performance-chart">
        <h4>性能指标分析 (基于所选模型)</h4>
         <!-- <div v-if="isLoadingDetails" class="loading-placeholder">
             <el-icon class="is-loading" :size="20"><Loading /></el-icon>
             <span>加载指标...</span>
         </div>
         <div v-else-if="!currentModelDetails && !isLoadingDetails" class="loading-placeholder">
             选择模型以查看指标
         </div>
         <div v-else-if="detailError" class="error-placeholder">
             <el-icon><Warning /></el-icon>
            <span>无法加载性能指标</span>
         </div>
          <div v-else-if="!modelMetrics || Object.keys(modelMetrics).length === 0" class="error-placeholder">
             <el-icon><Warning /></el-icon>
            <span>所选模型暂无可用性能指标数据。</span>
         </div> -->
         <div class="radar-chart" ref="radarChartRef"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ModelDetailsDisplay from '@/components/models/ModelDetailsDisplay.vue'
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'; // Import nextTick
import axios from 'axios';
// Assuming types are correctly defined in this path or globally
import type { Model } from '@/components/models/types';
import { ElIcon, ElTag, ElDescriptions, ElDescriptionsItem } from 'element-plus';
import { Files, Loading, Warning } from '@element-plus/icons-vue';
import * as echarts from 'echarts/core'; // Import echarts core
import { RadarChart } from 'echarts/charts'; // Import Radar chart type
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'; // Import necessary components
import { CanvasRenderer } from 'echarts/renderers'; // Use Canvas renderer
import type { EChartsType, ComposeOption, RadarSeriesOption } from 'echarts/core'; // Core types
import type { TitleComponentOption, TooltipComponentOption, LegendComponentOption, RadarComponentOption } from 'echarts/components'; // Component option types
// --- Interfaces ---
interface BaseModel {
  id: string;
  name: string;
  description?: string;
  metrics?: Record<string, number>;
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
type ReviewMode = 'fast' | 'standard' | 'strict';
// Register necessary ECharts components
echarts.use([ TitleComponent, TooltipComponent, LegendComponent, RadarChart, CanvasRenderer ]);
type EChartsOption = ComposeOption< TitleComponentOption | TooltipComponentOption | LegendComponentOption | RadarComponentOption | RadarSeriesOption >;

// --- Props ---
const props = defineProps<{
  selectedModelId: number | string | null; // Receive the ID from parent
  reviewMode: ReviewMode | null; // <-- Add reviewMode prop
}>();

// --- State ---
const radarChartRef = ref<HTMLElement | null>(null);
let chart: EChartsType | null = null;
// Use a more specific type that covers both possibilities
const currentModelDetails = ref<Partial<Model> & Partial<BaseModel> | null>(null);
const isLoadingDetails = ref(false);
const detailError = ref<string | null>(null);
const isLoadingChartData = ref(false);
const chartError = ref<string|null>(null);
// --- Computed ---
const isBaseModel = computed(() => {
    return typeof props.selectedModelId === 'string';
});
const reviewModeText = computed(() => {
    if (!props.reviewMode) return '未选择模式';
    const map: Record<ReviewMode, string> = { fast: '快速模式', standard: '标准模式', strict: '严格模式' };
    return map[props.reviewMode] || '未知模式';
});
const modelMetrics = computed(() => {
    return currentModelDetails.value?.metrics || null;
});

// --- Methods ---
// TODO: Replace with API call if needed later
const modePerformanceData: Record<ReviewMode, Record<string, number>> = {
    fast: { elementCoverage: 75, responseSpeed: 90, errorDetection: 70, complexStructure: 65, ruleCompatibility: 80, resourceConsumption: 40 }, // Lower resource consumption is better
    standard: { elementCoverage: 85, responseSpeed: 80, errorDetection: 85, complexStructure: 75, ruleCompatibility: 85, resourceConsumption: 60 },
    strict: { elementCoverage: 95, responseSpeed: 70, errorDetection: 95, complexStructure: 90, ruleCompatibility: 95, resourceConsumption: 80 }
};
// Fetch details based on ID
const fetchModelDetails = async (modelId: number | string | null) => {
    if (modelId === null || modelId === undefined) { // Handle null/undefined explicitly
        currentModelDetails.value = null;
        detailError.value = null;
        chart?.clear();
        return;
    }

    isLoadingDetails.value = true;
    detailError.value = null;
    // Don't clear currentModelDetails immediately to avoid flicker, clear on success/error
    // chart?.clear(); // Clear chart only when new data is loaded or error occurs

    const isBase = typeof modelId === 'string';
    // Use relative URLs or environment variables for API paths
    const apiUrl = isBase ? `http://8.148.68.206:5000/api/base-models/${modelId}` : `http://8.148.68.206:5000/api/models/${modelId}`;

    try {
        console.log(`Fetching details from: ${apiUrl}`);
        const token = localStorage.getItem('token');
        const headers = isBase ? {} : { 'Authorization': `Bearer ${token}` };

        // --- Make the actual API call ---
        const response = await axios.get<Model | BaseModel>(apiUrl, { headers });
        // --- Remove Simulation ---

        if (response.data) {
            currentModelDetails.value = response.data; // Assign fetched data
            console.log("Fetched details:", currentModelDetails.value);
            // Update chart only after details are successfully fetched
             await nextTick(); // Ensure DOM is ready for chart init/update
             initOrUpdateChart();
        } else {
             throw new Error("API did not return valid model data.");
        }

    } catch (error: any) {
        console.error(`获取模型 ${modelId} 详情失败:`, error);
        const message = error.response?.data?.message || error.message || '加载模型信息失败';
        detailError.value = message; // Set error state
        currentModelDetails.value = null; // Clear details on error
        chart?.clear(); // Clear chart on error
    } finally {
        isLoadingDetails.value = false;
    }
};

// Initialize or update Radar Chart
const initOrUpdateChart = () => {
    if (!radarChartRef.value) { console.warn("Radar chart ref not available yet."); return; }
    if (!props.reviewMode) { chart?.clear(); return; } // Clear chart if no mode selected

    const metrics = modePerformanceData[props.reviewMode];

    if (!metrics || Object.keys(metrics).length === 0) {
        console.log(`模式 ${props.reviewMode} 无可用指标数据。`);
        chart?.clear();
        chartError.value = `模式 ${reviewModeText.value} 无可用性能指标数据。`; // Set error message
        return;
    }
    chartError.value = null; // Clear previous error

    if (!chart) {
        try {
            chart = echarts.init(radarChartRef.value);
            window.addEventListener('resize', handleResize);
        } catch (e) { console.error("初始化ECharts失败:", e); chartError.value = "初始化图表失败"; return; }
    }

    const indicatorDefs = [
        { key: 'elementCoverage', name: '元素覆盖', max: 100 },
        { key: 'responseSpeed', name: '响应速度', max: 100 },
        { key: 'errorDetection', name: '错误检出', max: 100 },
        { key: 'complexStructure', name: '复杂结构', max: 100 },
        { key: 'ruleCompatibility', name: '规则兼容', max: 100 },
        { key: 'resourceConsumption', name: '资源消耗', max: 100 }, // Invert display logic or label needed
    ];
    const indicators = indicatorDefs.map(ind => ({ name: ind.name, max: ind.max }));
     // Invert resource consumption for visual: higher score = lower consumption
    const resourceConsumptionScore = 100 - (metrics['resourceConsumption'] ?? 0);
    const chartData = [
        metrics['elementCoverage'] ?? 0,
        metrics['responseSpeed'] ?? 0,
        metrics['errorDetection'] ?? 0,
        metrics['complexStructure'] ?? 0,
        metrics['ruleCompatibility'] ?? 0,
        resourceConsumptionScore, // Use inverted score
    ];

    const option: EChartsOption = {
        tooltip: { trigger: 'item' },
        radar: {
            indicator: indicators,
            radius: '65%', center: ['50%', '55%'],
            axisName: { color: '#666', fontSize: 11 }
        },
        series: [{
            type: 'radar',
            data: [{
                value: chartData,
                name: reviewModeText.value, // Use mode name
                areaStyle: { color: 'rgba(84, 112, 198, 0.2)' },
                lineStyle: { color: '#5470C6' },
                itemStyle: { color: '#5470C6' }
            }]
        }]
    };
    chart.setOption(option, true);
};

// Helper to format timestamp
const formatTimestamp = (timestamp: string | undefined | null): string => {
    if (!timestamp) return 'N/A';
    try {
        const date = new Date(timestamp);
        return isNaN(date.getTime()) ? '无效日期' : date.toLocaleString();
    } catch (e) { return '日期格式错误'; }
};

// --- Watchers ---
watch(() => props.selectedModelId, (newId, oldId) => {
    // Avoid fetching if ID hasn't actually changed (can happen on initial prop set)
    if (newId !== oldId) {
       console.log(`Visualization: Watched model ID changed to ${newId}`);
       fetchModelDetails(newId);
    }
});
// Watch reviewMode for the chart section
watch(() => props.reviewMode, (newMode, oldMode) => {
    if (newMode !== oldMode) {
        console.log(`Visualization: reviewMode changed to ${newMode}, updating chart.`);
        // Update chart directly when mode changes
        initOrUpdateChart();
    }
}, { immediate: true }); // Update chart immediately when component loads with a mode
// --- Lifecycle ---
const handleResize = () => { chart?.resize(); };

onMounted(() => {
  console.log("Visualization onMounted: Initializing...");
    // Fetch initial data only if an ID is already provided when mounted
    if (props.selectedModelId !== null && props.selectedModelId !== undefined) {
        console.log(`Visualization onMounted: Fetching initial details for ID ${props.selectedModelId}`);
        // Call fetch, which will call initOrUpdateChart after data arrives and nextTick
        fetchModelDetails(props.selectedModelId);
    } else {
        console.log("Visualization onMounted: No initial model ID selected.");
         // Ensure chart ref is available before trying to init/clear, though likely not needed here
        //  if (radarChartRef.value && !chart) { initOrUpdateChart(); } // Or just wait for selection
    }
    // Resize listener moved to be added *after* successful init
    // window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
    console.log("Visualization onBeforeUnmount: Cleaning up chart and listener.");
    window.removeEventListener('resize', handleResize);
    chart?.dispose(); // Dispose ECharts instance
    chart = null; // Clear the reference
});
</script>

<style scoped>
/* Styles remain largely the same */
.settings-visualization { height: 100%; padding: 15px; background: #f8f9fa; }
.visualization-container { height: 100%; display: flex; gap: 15px; }
.model-preview, .performance-chart { flex: 1; background: white; border-radius: 6px; padding: 18px; box-shadow: 0 1px 8px rgba(0, 0, 0, 0.07); display: flex; flex-direction: column; }
h4 { margin: 0 0 15px 0; color: #343a40; font-size: 1.05em; font-weight: 600; padding-bottom: 8px; border-bottom: 1px solid #eee; }
.model-info-display { flex-grow: 1; text-align: center; padding-top: 10px; }
.model-info-display h5 { font-size: 1.1em; margin-bottom: 8px; color: #0d6efd; }
.model-info-display .el-tag { margin-left: 8px; vertical-align: middle; }
.model-info-display .description { font-size: 0.9em; color: #6c757d; margin-bottom: 15px; line-height: 1.5; }
.model-info-display .el-descriptions { margin-top: 15px; text-align: left; }
.model-info-display .base-model-note { font-size: 0.9em; color: #6c757d; margin-top: 15px; font-style: italic; }
.radar-chart { flex: 1; min-height: 320px; }
.loading-placeholder, .error-placeholder { flex-grow: 1; display: flex; align-items: center; justify-content: center; text-align: center; color: #adb5bd; font-size: 0.95em; gap: 8px; /* Add gap for icon and text */ }
.error-placeholder { color: #dc3545; }
.loading-placeholder .el-icon { font-size: 1.2em; } /* Make loading icon slightly larger */
.error-placeholder .el-icon { font-size: 1.2em; } /* Make error icon slightly larger */
.is-loading { animation: rotating 1.5s linear infinite; } /* Add rotation animation */
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>