<template>
  <div class="analyze-visualization">
    <!-- 图层控制面板 -->
    <div class="layer-controls">
      <h4>图层控制 (可拖动排序)</h4>
      <!-- 使用 draggable 组件 -->
      <draggable 
        v-model="layers" 
        item-key="name" 
        handle=".drag-handle" 
        animation="200"
      >
        <template #item="{element: layer}">
          <div class="layer-item" :class="{ disabled: !analysisCompleted || isAnalyzing }">
            <i class="fas fa-grip-vertical drag-handle"></i> <!-- 拖拽手柄 -->
            <label>
              <input 
                type="checkbox" 
                v-model="layer.visible" 
                :disabled="!analysisCompleted || isAnalyzing"
              >
              <span class="layer-color-indicator" :style="{ backgroundColor: layer.color }"></span>
              {{ layer.label }}
            </label>
          </div>
        </template>
      </draggable>
    </div>

    <!-- 地图显示区域 -->
    <div class="map-display-area">
      <!-- 底图 -->
      <img 
        v-if="baseMapUrl" 
        :src="baseMapUrl" 
        alt="原始地图" 
        class="map-layer base-map"
        @load="handleImageLoad('base')"
        :class="{ loaded: imageLoaded.base, analyzing: isAnalyzing }"
      />
      
      <!-- 叠加图层 (现在根据 layers 数组的顺序渲染) -->
      <template v-if="analysisCompleted">
        <!-- 使用 v-for 遍历 layers，并用 z-index 控制堆叠顺序 -->
        <img 
          v-for="(layer, index) in layers" 
          :key="layer.name + '-img'" 
          v-show="layer.imageUrl" 
          :src="layer.imageUrl || ''" 
          :alt="layer.label" 
          class="map-layer overlay-map"
          :style="{ 
            opacity: layer.visible ? 1 : 0, 
            zIndex: index + 2 // 保证叠加层在底图之上，且顺序正确 
          }"
          @load="handleImageLoad(layer.name)"
          :class="{ loaded: imageLoaded[layer.name] }"
        />
      </template>

      <!-- 加载或分析状态指示器 -->
      <!-- <div v-if="isLoading || isAnalyzing" class="status-indicator">
        <i class="fas" :class="isLoading ? 'fa-spinner fa-spin' : 'fa-cogs'"></i> 
        {{ isLoading ? '加载图层中...' : '地图解析中...' }}
      </div> -->

       <!-- 分析时的视觉效果 -->
       <div v-if="isAnalyzing" class="analysis-effect-overlay"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
// @ts-ignore - 忽略 vuedraggable 的类型检查
import draggable from 'vuedraggable' // 导入 draggable

const emit = defineEmits<{
  (e: 'analyze-completed'): void
}>()

interface StageData {
    status: string
    progress?: number
}

interface Layer {
  name: string;
  label: string;
  color: string; // 用于图例
  visible: boolean;
  imageUrl: string | null;
}

const route = useRoute()
const taskId = parseInt(route.params.id as string)
const stageData = ref<StageData | null>(null)
const baseMapUrl = ref<string | null>(null)
const layers = ref<Layer[]>([
  { name: 'plants_layer', label: '绿地层', color: '#96CEB4', visible: false, imageUrl: null },
  { name: 'roads_layer', label: '道路层', color: '#FF6B6B', visible: false, imageUrl: null },
  
  { name: 'water_layer', label: '水体系', color: '#45B7D1', visible: false, imageUrl: null },
  { name: 'buildings_layer', label: '建筑层', color: '#FFA07A', visible: false, imageUrl: null },
])

// 保持所有图层的加载状态跟踪，即使它们可能不加载
const imageLoaded = reactive<Record<string, boolean>>({
  base: false,
  roads_layer: false,
  plants_layer: false,
  water_layer: false,
  buildings_layer: false,
})
const isLoading = ref(false)

// --- 新增分析状态和轮询器 ---
const isAnalyzing = ref(false) 
const analysisPollInterval = ref<number | null>(null) 

// --- 计算属性 ---
const analysisCompleted = computed(() => stageData.value?.status === 'completed')

// 计算实际需要加载的图片数量
const totalImagesToLoad = computed(() => 1 + layers.value.length)
const loadedImageCount = ref(0)

// --- 方法 ---

const getImageUrl = (layerName: string) => {
   // 使用原始地图的新端点
   if (layerName === 'original_map') {
       return `http://8.148.68.206:5000/api/tasks/${taskId}/original/original_map.png`;
   } else {
       return `http://8.148.68.206:5000/api/tasks/${taskId}/analysis/image/${layerName}.png`;
   }
}

// 加载地图图片
const loadMapLayers = async () => {
  // 确保不在分析中且已完成后才加载图层
  if (isAnalyzing.value || !analysisCompleted.value) return;

  isLoading.value = true
  loadedImageCount.value = 0
  // 重置所有加载状态
  Object.keys(imageLoaded).forEach(key => imageLoaded[key] = false)
  
  // 始终尝试加载底图 (如果 URL 尚未设置)
  if (!baseMapUrl.value) {
      baseMapUrl.value = getImageUrl('original_map');
      console.log("设置底图 URL:", baseMapUrl.value);
  }
  
  // 仅在分析完成后加载叠加图层
  if (analysisCompleted.value) {
      console.log("分析已完成，加载叠加图层...");
      layers.value.forEach(layer => {
          layer.imageUrl = getImageUrl(layer.name);
          console.log(`设置图层 ${layer.name} URL:`, layer.imageUrl);
      });
  } else {
      console.log("分析未完成，不加载叠加图层。");
      // 确保叠加图层 URL 为空
      layers.value.forEach(layer => {
          layer.imageUrl = null;
      });
  }
}

// 处理图片加载完成事件
const handleImageLoad = (layerName: string) => {
  if (!imageLoaded[layerName]) { // 防止重复计数
      console.log(`图片加载完成: ${layerName}`);
      imageLoaded[layerName] = true
      loadedImageCount.value++
      console.log(`已加载 ${loadedImageCount.value} / ${totalImagesToLoad.value} 张图片`);
      // 检查是否所有 *需要* 加载的图片都已完成
      if (loadedImageCount.value >= totalImagesToLoad.value) {
          console.log("所需图片加载完毕");
          isLoading.value = false
      }
  }
}

// --- 轮询逻辑 ---
const stopAnalysisPolling = () => {
  if (analysisPollInterval.value) {
    clearInterval(analysisPollInterval.value)
    analysisPollInterval.value = null
    console.log("停止分析状态轮询")
  }
}

const startAnalysisPolling = () => {
  stopAnalysisPolling() 
  isAnalyzing.value = true 
  console.log("开始轮询分析状态...")

  analysisPollInterval.value = window.setInterval(async () => {
    try {
      // *** 调用后端状态查询接口 ***
      const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/3`)
      const backendStatus = response.data.stage.status
      console.log(`轮询状态: ${backendStatus}`) 

      if (backendStatus === 'completed') {
        stopAnalysisPolling()
        isAnalyzing.value = false
        ElMessage.success('地图解析完成！')
        emit('analyze-completed')
        await getStageData() // 刷新数据和状态，会触发 watch 加载图层
      } else if (backendStatus === 'error') {
        stopAnalysisPolling()
        isAnalyzing.value = false
        ElMessage.error(response.data.message || '地图解析失败')
         await getStageData() // 刷新以显示错误状态
      } else {
        isAnalyzing.value = true // 保持分析中状态
      }
    } catch (error) {
      console.error('轮询分析状态失败:', error)
      stopAnalysisPolling()
      isAnalyzing.value = false // 出错停止分析状态
      ElMessage.error('无法获取解析状态')
    }
  }, 3000) // 每 3 秒查询一次
}

// --- 暴露给父组件的方法 ---
const triggerAnalysisStart = () => {
  // 确保不在分析中才能开始
  if (!isAnalyzing.value && stageData.value?.status !== 'completed') { 
      console.log("触发分析流程...")
      isAnalyzing.value = true; // 立即显示分析中效果
      // 调用 start polling, 但可能后端接口还没把状态改成 in_progress, 
      // 所以轮询会处理
      startAnalysisPolling()
  } else {
       console.warn("无法开始分析，当前状态:", stageData.value?.status, " 或正在分析中:", isAnalyzing.value)
  }
}

// --- 生命周期和侦听器 ---
const getStageData = async () => {
  try {
    console.log("获取分析阶段数据...");
    const response = await axios.get(`http://8.148.68.206:5000/api/tasks/${taskId}/stage/3`)
    const newData = response.data.stage
    const oldStatus = stageData.value?.status;
    stageData.value = newData;
    console.log("获取到阶段状态:", stageData.value?.status);
    
    // 根据新状态决定操作
    if (stageData.value?.status === 'completed') {
        stopAnalysisPolling(); // 确保停止轮询
        isAnalyzing.value = false; // 确保不在分析状态
        if (oldStatus !== 'completed') {
            await loadMapLayers(); // 只有在状态刚变为 completed 时加载
        }
    } else if (stageData.value?.status === 'in_progress') {
        if (!analysisPollInterval.value) { // 如果不在轮询中，则开始
            startAnalysisPolling();
        }
        isAnalyzing.value = true; // 确保显示分析中
    } else { // pending or error
        stopAnalysisPolling();
        isAnalyzing.value = false;
    }

    // 确保底图总是尝试加载
     if (!baseMapUrl.value) {
      baseMapUrl.value = getImageUrl('original_map');
    }

  } catch (error) {
    console.error("获取阶段数据失败:", error)
  }
}

onMounted(async () => {
  console.log("AnalyzeStageVisualization mounted.");
  await getStageData(); // 初始加载数据并根据状态执行操作
})

onUnmounted(() => {
  console.log("AnalyzeStageVisualization unmounted.");
  // 清理 blob URLs（如果使用了的话）
  if (baseMapUrl.value && baseMapUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(baseMapUrl.value)
  }
  layers.value.forEach(layer => {
    if (layer.imageUrl && layer.imageUrl.startsWith('blob:')) {
      URL.revokeObjectURL(layer.imageUrl)
     }
  })
  stopAnalysisPolling() // 组件卸载时停止轮询
})

defineExpose({
  getStageData,
  triggerAnalysisStart // 暴露给 TaskMonitor
})
</script>

<style scoped>
.analyze-visualization {
  display: flex;
  height: 100%;
  background: #f4f7fe;
  overflow: hidden; /* 防止子元素溢出 */
}

.layer-controls {
  width: 200px;
  padding: 20px;
  background: white;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  z-index: 10;
  overflow-y: auto;
  border-right: 1px solid #e0e5f2;
}

.layer-controls h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #2b3674;
  font-size: 16px;
}

.layer-item {
  display: flex; /* 使手柄和 label 在一行 */
  align-items: center;
  margin-bottom: 12px;
  /* 可以在这里添加一些边框或背景，让拖拽项更明显 */
}

.layer-item label {
  flex-grow: 1; /* 让 label 占据剩余空间 */
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: color 0.3s ease;
}

/* 禁用状态样式 */
.layer-item.disabled label {
    color: #aaa;
    cursor: not-allowed;
}
.layer-item.disabled input[type="checkbox"] {
    cursor: not-allowed;
}

.layer-item input[type="checkbox"] {
  margin-right: 8px;
}

.layer-color-indicator {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  margin-right: 8px;
  border: 1px solid rgba(0,0,0,0.1);
}

.map-display-area {
  flex: 1;
  position: relative; /* 重要：作为绝对定位子元素的容器 */
  display: flex; /* 用于居中加载指示器 */
  align-items: center;
  justify-content: center;
  overflow: hidden; /* 隐藏可能溢出的部分 */
  background-color: #e8e8e8; /* 背景色，图片未加载时显示 */
}

.map-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain; /* 保持图片比例，完整显示 */
  transition: opacity 0.5s ease-in-out; /* 平滑过渡效果 */
  opacity: 0; /* 初始不可见，加载后通过 class 控制 */
}

.map-layer.base-map {
  opacity: 0; /* 底图初始也透明，加载后显示 */
  z-index: 1; /* 底图在最下面 */
}

.map-layer.overlay-map {
  z-index: 2; /* 叠加图层在底图之上 */
}

.map-layer.loaded {
    opacity: 1; /* 图片加载完成后显示 */
}

/* 特别处理叠加层，只有在 visible 为 true 时才应用 loaded 后的 opacity: 1 */
.map-layer.overlay-map.loaded {
    opacity: 0; /* 默认加载完还是透明 */
}

/* 分析时给底图加效果 */
.map-layer.base-map.analyzing {
    /* animation: pulse 1.5s infinite ease-in-out; */ /* 脉冲可能太干扰，换个效果 */
    filter: grayscale(50%) brightness(90%); /* 灰度+稍暗 */
}

/* 加载/分析状态指示器共享样式 */
.status-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

/* 分析效果遮罩 (可选，淡蓝色扫描线) */
.analysis-effect-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(to right, 
      transparent 0%, 
      rgba(67, 24, 255, 0.1) 48%, 
      rgba(67, 24, 255, 0.3) 50%, 
      rgba(67, 24, 255, 0.1) 52%, 
      transparent 100%
    );
    background-size: 200% 100%; /* 使渐变可以移动 */
    animation: scan-horizontal 2s linear infinite;
    z-index: 5; 
    pointer-events: none; 
}

/* 动画定义 */
/* @keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
} */

@keyframes scan-horizontal {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 为拖拽手柄添加样式 */
.drag-handle {
  cursor: grab;
  margin-right: 8px;
  color: #ccc;
}

/* 拖拽时的占位符样式 (可选) */
.sortable-ghost {
  opacity: 0.4;
  background-color: #eef;
}
</style> 