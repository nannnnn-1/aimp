<template>
  <div class="map-processor">
    <!-- 保留开始检测按钮 -->
    <div class="upload-section">
      <button 
        @click="startProcessing" 
        :disabled="isProcessing"
        class="process-btn"
      >
        {{ processingStatus }}
      </button>
    </div>

    <!-- 处理面板 -->
    <div class="processing-panel">
      <!-- 步骤追踪 -->
      <div class="step-tracker">
        <transition-group name="step-fade" tag="div">
          <div 
            v-for="(step, index) in processingSteps" 
            :key="step.name"
            :class="['step-item', step.status]"
          >
            <div class="step-header">
              <span class="step-index">{{ index + 1 }}</span>
              {{ step.name }}
              <span v-if="step.status === 'done'" class="status-icon">✓</span>
              <span v-else-if="step.status === 'processing'" class="status-icon">⌛</span>
            </div>
            <transition name="preview-fade">
              <div class="step-preview" v-if="step.previewUrl">
                <img 
                  :src="step.previewUrl" 
                  alt="处理预览" 
                  @error="handleImageError"
                />
                <div class="progress-bar" v-if="step.status === 'processing'">
                  <div class="progress" :style="{ width: step.progress + '%' }"></div>
                </div>
              </div>
            </transition>
          </div>
        </transition-group>
      </div>

      <!-- 结果展示 -->
      <div class="result-display">
        <canvas ref="canvas"></canvas>
        <div 
          class="layer-controls draggable-resizable"
          ref="layerControlsRef"
          @mousedown="onDragMouseDown"
        >
          <transition-group name="layer-fade" tag="div">
            <div 
              v-for="(layer, idx) in availableLayers" 
              :key="layer.name"
              class="layer-control"
            >
              <label>
                <input 
                  type="checkbox" 
                  v-model="activeLayers" 
                  :value="layer.name" 
                  class="layer-checkbox"
                />
                {{ layer.name }}
              </label>
              <div 
                class="layer-preview" 
                :style="{ backgroundColor: layer.color }"
              ></div>
            </div>
          </transition-group>
          <!-- 用于拉伸大小的Handler -->
          <div class="resize-handle" @mousedown.stop="onResizeMouseDown"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import axios from 'axios'

/**
 * [CONFIG] 固定的 API配置 与 处理步骤配置
 * 如果后端接口地址或名称需要变更，可在此处修改
 */
const apiConfig = {
  uploadUrl: 'http://8.148.68.206:5000/api/upload', // [CONFIG] 上传接口
  progressUrl: 'http://8.148.68.206:5000/api/progress/' // [CONFIG] 轮询进度接口
}

/**
 * [CONFIG] 轮询间隙(毫秒) 配置
 * 方便随时调整和优化体验
 */
const pollInterval = 100

/**
 * [CONFIG] 处理步骤配置
 * 可在此处添加或移除处理步骤
 */
const fixedProcessingStepsConfig = [
  { name: '文字层提取', color: '#FF6B6B' },
  { name: '建筑层提取', color: '#4ECDC4' },
  { name: '道路层提取', color: '#45B7D1' },
  { name: '绿地层提取', color: '#96CEB4' },
  { name: '图层整合', color: '#FFD700' }
]

// 响应式状态
const processingSteps = reactive([])
const availableLayers = reactive([])
const activeLayers = ref([])
const canvas = ref(null)
const ctx = ref(null)
const currentTaskId = ref(null)
const isProcessing = ref(false)
const processingStatus = ref('开始检测')
const nowPic = ref(null)
const taskCompleted = ref(false)

/**
 * 初始化Canvas，并将画布设置为更大尺寸
 */
const initCanvas = () => {
  if (canvas.value) {
    ctx.value = canvas.value.getContext('2d')
    canvas.value.width = 1200 // [CONFIG] 可修改为更适合需要的分辨率
    canvas.value.height = 800
  }
}

/**
 * 将当前应用状态存入本地存储
 */
const saveToLocalStorage = () => {
  const dataToStore = {
    availableLayers: JSON.parse(JSON.stringify(availableLayers)),
    activeLayers: activeLayers.value,
    taskCompleted: taskCompleted.value,
    processingSteps: JSON.parse(JSON.stringify(processingSteps))
  }
  localStorage.setItem('map-processor-state', JSON.stringify(dataToStore))
}

/**
 * 从本地存储读取应用状态
 */
const loadFromLocalStorage = () => {
  const storedData = localStorage.getItem('map-processor-state')
  if (storedData) {
    const parsed = JSON.parse(storedData)
    if (Array.isArray(parsed.availableLayers)) {
      availableLayers.splice(0)
      parsed.availableLayers.forEach((layer) => {
        availableLayers.push(layer)
      })
    }
    if (Array.isArray(parsed.activeLayers)) {
      activeLayers.value = parsed.activeLayers
    }
    if (typeof parsed.taskCompleted === 'boolean') {
      taskCompleted.value = parsed.taskCompleted
    }
    if (Array.isArray(parsed.processingSteps)) {
      processingSteps.splice(0)
      parsed.processingSteps.forEach((step) => {
        processingSteps.push(step)
      })
    }
  }
}

/**
 * 开始检测——模拟上传并开始进度轮询
 */
const startProcessing = async () => {
  try {
    isProcessing.value = true
    taskCompleted.value = false
    processingStatus.value = '检测中...'
    initializeSteps()

    const formData = new FormData()
    formData.append('map', 'fake_content')

    const response = await axios.post(apiConfig.uploadUrl, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.taskId) {
      currentTaskId.value = response.data.taskId
      startProgressPolling()
    } else {
      console.warn('后端未返回taskId，检测流程无法继续')
      isProcessing.value = false
      processingStatus.value = '开始检测'
    }
  } catch (error) {
    console.error('模拟上传失败:', error)
    alert('检测失败，请检查控制台')
    isProcessing.value = false
    processingStatus.value = '开始检测'
  }
}

/**
 * 初始化处理步骤
 */
const initializeSteps = () => {
  processingSteps.splice(0)
  fixedProcessingStepsConfig.forEach((step, index) => {
    processingSteps.push({
      ...step,
      status: index === 0 ? 'processing' : 'pending',
      progress: 0,
      previewUrl: null
    })
  })
  availableLayers.splice(0)
  nowPic.value = null
  activeLayers.value = []
}

/**
 * 轮询处理进度
 */
const startProgressPolling = () => {
  const poll = async () => {
    if (!currentTaskId.value) return
    try {
      const response = await axios.get(
        `${apiConfig.progressUrl}${currentTaskId.value}`
      )
      updateProcessingState(response.data)

      if (response.data.status !== 'completed') {
        setTimeout(poll, pollInterval)
      } else {
        currentTaskId.value = null
        taskCompleted.value = true
        isProcessing.value = false
        nowPic.value = null
        activeLayers.value = availableLayers.map((l) => l.name)
        redrawCanvas()
        processingStatus.value = '开始检测'
      }
    } catch (error) {
      console.error('获取进度失败:', error)
    }
  }
  poll()
}

/**
 * 更新处理状态
 */
const updateProcessingState = (data) => {
  processingSteps.splice(
    0,
    processingSteps.length,
    ...data.steps.map((step, index) => ({
      ...step,
      color: fixedProcessingStepsConfig[index]?.color || '#ccc'
    }))
  )

  // 实时预览
  if (data.now_pic && data.status !== 'completed') {
    if (data.now_pic.startsWith('http')) {
      nowPic.value = data.now_pic
    } else {
      nowPic.value = `${apiConfig.progressUrl}../${data.now_pic}`
    }
  }

  // 更新可用图层
  if (data.availableLayers) {
    availableLayers.splice(
      0,
      availableLayers.length,
      ...data.availableLayers.map(layer => ({
        ...layer,
        previewUrl: layer.previewUrl.startsWith('http')
          ? layer.previewUrl
          : `${apiConfig.progressUrl}../${layer.previewUrl}`
      }))
    )
  }
  redrawCanvas()
}

/**
 * 重绘逻辑（各图层按指定顺序覆盖）
 */
const redrawCanvas = async () => {
  if (!canvas.value || !ctx.value) return

  const offscreenCanvas = document.createElement('canvas')
  offscreenCanvas.width = canvas.value.width
  offscreenCanvas.height = canvas.value.height
  const offscreenCtx = offscreenCanvas.getContext('2d')
  offscreenCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height)

  if (isProcessing.value && nowPic.value) {
    await drawImageToContext(offscreenCtx, nowPic.value)
  } else if (taskCompleted.value) {
    for (let i = availableLayers.length - 1; i >= 0; i--) {
      const layer = availableLayers[i]
      if (activeLayers.value.includes(layer.name)) {
        await drawImageToContext(offscreenCtx, layer.previewUrl)
      }
    }
  }

  ctx.value.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height)
  ctx.value.drawImage(offscreenCanvas, 0, 0)
}

/**
 * 通用绘图方法
 */
const drawImageToContext = (targetCtx, imageUrl) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.src = imageUrl
    img.onload = () => {
      const { width: canvasWidth, height: canvasHeight } = targetCtx.canvas
      const scale = Math.min(canvasWidth / img.width, canvasHeight / img.height)
      const x = (canvasWidth - img.width * scale) / 2
      const y = (canvasHeight - img.height * scale) / 2
      targetCtx.globalCompositeOperation = 'source-over'
      targetCtx.drawImage(img, x, y, img.width * scale, img.height * scale)
      resolve()
    }
    img.onerror = reject
  })
}

/**
 * 图片加载失败处理
 */
const handleImageError = (e) => {
  e.target.style.display = 'none'
  console.error('图片加载失败:', e.target.src)
}

/**
 * 监听图层、预览变化并重绘，同时保持到本地
 */
watch([activeLayers, nowPic, taskCompleted, processingSteps], () => {
  redrawCanvas()
  saveToLocalStorage()
})

onMounted(() => {
  initCanvas()
  loadFromLocalStorage()
  redrawCanvas()
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
})

/**
 * 拖拽及缩放相关
 */
let isDragging = false
let dragStartX = 0
let dragStartY = 0
let startLeft = 0
let startTop = 0
let isResizing = false
let startWidth = 0
let startHeight = 0

const layerControlsRef = ref(null)

const onDragMouseDown = (e) => {
  if (e.target.classList.contains('resize-handle')) return
  isDragging = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  const layerControlsEl = layerControlsRef.value
  const rect = layerControlsEl.getBoundingClientRect()
  startLeft = rect.left
  startTop = rect.top
}

const onMouseMove = (e) => {
  if (isDragging) {
    const layerControlsEl = layerControlsRef.value
    const dx = e.clientX - dragStartX
    const dy = e.clientY - dragStartY
    layerControlsEl.style.left = `${startLeft + dx}px`
    layerControlsEl.style.top = `${startTop + dy}px`
  } else if (isResizing) {
    const layerControlsEl = layerControlsRef.value
    const dx = e.clientX - dragStartX
    const dy = e.clientY - dragStartY
    layerControlsEl.style.width = `${startWidth + dx}px`
    layerControlsEl.style.height = `${startHeight + dy}px`
  }
}

const onMouseUp = () => {
  isDragging = false
  isResizing = false
}

const onResizeMouseDown = (e) => {
  isResizing = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  const layerControlsEl = layerControlsRef.value
  const rect = layerControlsEl.getBoundingClientRect()
  startWidth = rect.width
  startHeight = rect.height
}
</script>

<style scoped lang="scss">
/* 动画过渡 */
.step-fade-enter-active, .step-fade-leave-active {
  transition: all 0.3s ease;
}
.step-fade-enter, .step-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.preview-fade-enter-active, .preview-fade-leave-active {
  transition: all 0.3s ease;
}
.preview-fade-enter, .preview-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

.layer-fade-enter-active, .layer-fade-leave-active {
  transition: all 0.3s ease;
}
.layer-fade-enter, .layer-fade-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

.map-processor {
  display: grid;
  gap: 1rem;
  max-width: 1200px;
  margin: 0 ;
  padding: 1rem;

  .upload-section {
    display: flex;
    gap: 1rem;
    align-items: center;
    
    .process-btn {
      padding: 0.5rem 1.5rem;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.2s ease;

      &:disabled {
        background: #6c757d;
        cursor: not-allowed;
        transform: none;
      }
      
      &:not(:disabled):hover {
        background: #0056b3;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
      }
      
      &:active {
        transform: translateY(0);
        box-shadow: none;
      }
    }
  }

  .processing-panel {
    display: grid;
    grid-template-columns: 300px 2fr;
    gap: 1rem;
    height: 70vh;
    min-height: 500px;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 1rem;
    background: white;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);

    .step-tracker {
      border-right: 1px solid #eee;
      padding-right: 1rem;
      overflow-y: auto;
      max-height: calc(70vh - 100px);

      .step-item {
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 8px;
        background: #f8f9fa;
        transition: all 0.3s ease;

        &:hover {
          transform: scale(1.01);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        &.processing {
          background: #e3f2fd;
          box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
        }

        &.done {
          background: #e8f5e9;
          opacity: 0.9;
        }

        .step-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
          margin-bottom: 0.5rem;
          color: #2c3e50;

          .step-index {
            width: 24px;
            height: 24px;
            background: #007bff;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
          }

          .status-icon {
            margin-left: auto;
            font-size: 1.2rem;
          }
        }

        .step-preview {
          img {
            width: 100%;
            max-height: 150px;
            object-fit: contain;
            border-radius: 4px;
            margin-top: 0.5rem;
            border: 1px solid #eee;
          }

          .progress-bar {
            height: 4px;
            background: #eee;
            border-radius: 2px;
            margin-top: 0.5rem;
            overflow: hidden;

            .progress {
              height: 100%;
              background: #007bff;
              border-radius: 2px;
              transition: width 0.3s ease;
            }
          }
        }
      }
    }

    .result-display {
      position: relative;
      background: #f8f9fa;
      border-radius: 8px;

      canvas {
        display: block;
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        background: white;
        border: 1px solid #eee;
      }

      .layer-controls {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(255, 255, 255, 0.95);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

        max-height: 200px;
        overflow-y: auto;
        width: 250px;
        height: auto;
        cursor: move;

        .layer-control {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
          transition: transform 0.2s ease;

          &:hover {
            transform: scale(1.02);
          }

          label {
            color: #333;
          }

          .layer-checkbox {
            margin-right: 0.5rem;
          }

          .layer-preview {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid rgba(0, 0, 0, 0.1);
          }
        }

        .resize-handle {
          position: absolute;
          bottom: 0;
          right: 0;
          width: 12px;
          height: 12px;
          background: #ccc;
          cursor: se-resize;
          border-radius: 2px;
        }
      }

      .draggable-resizable {
        touch-action: none;
      }
    }
  }
}
</style>