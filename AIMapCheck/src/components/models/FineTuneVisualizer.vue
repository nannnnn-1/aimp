<template>
    <div class="fine-tune-visualizer">
      <h4>微调进度可视化</h4>
  
      <div class="visual-stage-info">
        <div class="stage-icon">
          <el-icon :size="30">
            <component :is="currentStageIcon" :class="iconAnimationClass" />
          </el-icon>
        </div>
        <div class="stage-details">
          <div class="stage-name">{{ currentStageText }}</div>
          <el-progress
            :percentage="progress"
            :stroke-width="10"
            striped
            striped-flow
            :status="progressStatus"
            :text-inside="false"
            style="margin-top: 5px;"
          />
        </div>
      </div>
  
      <div class="dynamic-info">
        <el-row :gutter="20">
          <!-- Simulated Metrics -->
          <el-col :span="12">
            <el-card shadow="never" class="metric-card">
              <template #header>
                <div class="card-header">
                  <span><el-icon><DataLine /></el-icon> 模拟训练指标</span>
                </div>
              </template>
              <div class="metric-item" v-if="showMetrics">
                <span>损失 (Loss):</span>
                <span class="metric-value loss">{{ simulatedLoss }}</span>
              </div>
              <div class="metric-item" v-if="showMetrics">
                <span>准确率 (Accuracy):</span>
                <span class="metric-value accuracy">{{ simulatedAccuracy }}%</span>
              </div>
               <div v-if="!showMetrics" class="metric-placeholder">
                 等待训练开始...
               </div>
            </el-card>
          </el-col>
  
          <!-- Simulated Logs -->
          <el-col :span="12">
            <el-card shadow="never" class="log-card">
               <template #header>
                <div class="card-header">
                  <span><el-icon><Document /></el-icon> 模拟日志输出</span>
                </div>
              </template>
              <div class="log-output" ref="logOutputRef">
                <p v-for="(log, index) in simulatedLogs" :key="index" :class="log.type">
                  <span class="log-timestamp">[{{ log.timestamp }}]</span> {{ log.message }}
                </p>
                 <p v-if="simulatedLogs.length === 0" class="log-placeholder">...</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch, nextTick, onUnmounted } from 'vue';
  import { ElProgress, ElIcon, ElCard, ElRow, ElCol } from 'element-plus';
  import {
    Loading,
    Clock,
    Files,
    Cpu,
    Platform, // Using Platform for Training
    UploadFilled, // Using for Saving
    Finished,
    CircleCheck,
    CircleClose,
    DataLine,
    Document
  } from '@element-plus/icons-vue';
  import type { SimulationState, SimulationStage } from './types'; // Assuming types are externalized or defined here
  
  // Props definition - Receive simulation state from parent
  const props = defineProps<{
    modelId: number;
    simulationState: SimulationState | undefined; // Can be undefined if simulation hasn't started or ended
  }>();
  
  // Refs for dynamic content
  const simulatedLoss = ref<string>('N/A');
  const simulatedAccuracy = ref<string>('N/A');
  const simulatedLogs = ref<{ timestamp: string; message: string; type: 'info' | 'warn' | 'error' | 'success' }[]>([]);
  const logOutputRef = ref<HTMLElement | null>(null);
  let metricInterval: number | undefined = undefined;
  let logInterval: number | undefined = undefined;
  
  // --- Computed properties based on simulationState prop ---
  
  const currentStage = computed<SimulationStage>(() => props.simulationState?.currentStage ?? 'queued'); // Default to queued if no state
  const progress = computed<number>(() => props.simulationState?.progress ?? 0);
  const simulatedStatus = computed<'ready' | 'failed' | undefined>(() => props.simulationState?.simulatedStatus);
  
  const stageTextMap: Record<SimulationStage, string> = {
    queued:           '排队等待资源',
    preparing_data:   '准备样本数据中...',
    initializing:     '初始化基础模型...',
    training:         '模型训练进行中...',
    saving_model:     '保存微调模型...',
    evaluating:       '模型评估中...',
    finished:         '处理完成',
    error:            '处理失败',
  };
  const currentStageText = computed<string>(() => {
       // If finished, show text based on success/failure
       if (currentStage.value === 'finished') {
           return simulatedStatus.value === 'ready' ? '微调成功完成！' : '微调失败。';
       }
       if (currentStage.value === 'error') { // Should generally transition to finished/failed
          return '处理出错';
       }
       return stageTextMap[currentStage.value] ?? '未知阶段';
  });
  
  const stageIconMap: Record<SimulationStage, any> = {
    queued:           Clock,
    preparing_data:   Files,
    initializing:     Cpu,
    training:         Platform, // Changed Training icon
    saving_model:     UploadFilled, // Changed Saving icon
    evaluating:       Finished,
    finished:         CircleCheck, // Default finished icon (success)
    error:            CircleClose,
  };
  const currentStageIcon = computed(() => {
      if (currentStage.value === 'finished') {
          return simulatedStatus.value === 'ready' ? CircleCheck : CircleClose;
      }
       if (currentStage.value === 'error') {
          return CircleClose;
       }
      return stageIconMap[currentStage.value] ?? Loading; // Default to Loading if unknown
  });
  
  const iconAnimationClass = computed(() => {
    const stage = currentStage.value;
    if (['preparing_data', 'initializing', 'training', 'saving_model', 'evaluating'].includes(stage)) {
      return 'is-loading rotating'; // Standard rotation for active stages
    }
    if (stage === 'training') {
         // return 'is-loading pulsing'; // Keep pulsing for training? Or just rotating? Let's try rotating first.
    }
    return ''; // No animation for queued, finished, error
  });
  
  const progressStatus = computed<"" | "success" | "warning" | "exception">(() => {
      if (!props.simulationState) return ""; // No progress bar if no simulation
      if (currentStage.value === 'error' || simulatedStatus.value === 'failed') return 'exception';
      if (currentStage.value === 'finished' && simulatedStatus.value === 'ready') return 'success';
      // Maybe add 'warning' for specific stages if needed
      return ""; // Default blue active progress
  });
  
  // Show metrics only during relevant stages
  const showMetrics = computed(() => {
      const stage = currentStage.value;
      return ['training', 'evaluating', 'finished'].includes(stage);
  });
  
  // --- Simulation Effects (Metrics & Logs) ---
  
  const updateSimulatedMetrics = () => {
    if (currentStage.value === 'training' || currentStage.value === 'evaluating') {
      // Simulate decreasing loss
      let currentLoss = parseFloat(simulatedLoss.value) || 0.8; // Start high
      currentLoss -= Math.random() * 0.05; // Decrease randomly
      simulatedLoss.value = Math.max(0.05, currentLoss).toFixed(3); // Ensure minimum loss
  
      // Simulate increasing accuracy
      let currentAcc = parseFloat(simulatedAccuracy.value) || 60; // Start lower
      currentAcc += Math.random() * 2; // Increase randomly
      simulatedAccuracy.value = Math.min(98, currentAcc).toFixed(2); // Cap accuracy
    }
  };
  
  const addSimulatedLog = () => {
    const now = new Date();
    const timestamp = now.toLocaleTimeString();
    let message = '';
    let type: 'info' | 'warn' | 'success' | 'error' = 'info';
  
    const stage = currentStage.value;
  
    // Generate stage-specific log messages
    switch (stage) {
      case 'queued':
          message = '任务已提交，正在等待可用计算资源...'; break;
      case 'preparing_data':
          const prepStep = ['解压数据包', '验证文件格式', '开始数据预处理'][Math.floor(Math.random()*3)];
          message = `数据准备：${prepStep}`; break;
      case 'initializing':
          message = `初始化：加载基础模型 ${props.simulationState?.simulatedStatus === 'ready' ? '成功' : '结构'}...`; break; // Fake success/structure based on final outcome
      case 'training':
          const epoch = Math.round((progress.value - 30) / (85 - 30) * 10) + 1; // Estimate epoch based on progress
          message = `训练：Epoch ${epoch}/10 - Loss: ${simulatedLoss.value}, Acc: ${simulatedAccuracy.value}%`; break;
      case 'saving_model':
          message = '训练完成，正在保存模型权重...'; break;
      case 'evaluating':
          message = '模型已保存，开始最终评估...'; break;
      case 'finished':
          if (simulatedStatus.value === 'ready') {
              message = `评估完成。最终准确率: ${simulatedAccuracy.value}%. 微调成功！`;
              type = 'success';
          } else {
              message = '评估过程中发现问题，微调失败。';
              type = 'error';
          }
          // Stop adding logs once finished
          if(logInterval) clearInterval(logInterval);
          break;
       case 'error':
           message = '发生内部错误，处理中断。';
           type = 'error';
           if(logInterval) clearInterval(logInterval);
           break;
    }
  
    if (message && simulatedLogs.value.length < 50) { // Limit log length
        simulatedLogs.value.push({ timestamp, message, type });
        // Auto-scroll to bottom
        nextTick(() => {
            if (logOutputRef.value) {
                logOutputRef.value.scrollTop = logOutputRef.value.scrollHeight;
            }
        });
    }
  };
  
  // Watch the simulation stage to control metric/log generation
  watch(() => props.simulationState?.currentStage, (newStage, oldStage) => {
    // Clear previous intervals when stage changes
    if (metricInterval) clearInterval(metricInterval);
    if (logInterval) clearInterval(logInterval);
    simulatedLogs.value = []; // Clear logs on stage change? Or keep accumulating? Let's clear for now.
  
    if (newStage === 'training' || newStage === 'evaluating') {
        // Start updating metrics during training/evaluating
        simulatedLoss.value = '0.850'; // Reset loss
        simulatedAccuracy.value = '65.00'; // Reset accuracy
        updateSimulatedMetrics(); // Update once immediately
        metricInterval = window.setInterval(updateSimulatedMetrics, 1500); // Update every 1.5s
  
        // Start adding logs more frequently during active stages
        addSimulatedLog(); // Add once immediately
        logInterval = window.setInterval(addSimulatedLog, 2000); // Add log every 2s
    } else if (newStage === 'finished' || newStage === 'error') {
        // Ensure final log message is added
         addSimulatedLog();
         // Potentially set final metric values based on success/failure
         if(simulatedStatus.value === 'ready'){
             simulatedAccuracy.value = (90 + Math.random() * 8).toFixed(2); // Higher final accuracy
             simulatedLoss.value = (0.05 + Math.random() * 0.05).toFixed(3); // Lower final loss
         } else {
             // Keep last known metrics or set to N/A
         }
  
    } else if (newStage) {
         // Add logs less frequently for other stages
         addSimulatedLog();
         logInterval = window.setInterval(addSimulatedLog, 3000); // Add log every 3s
    }
  });
  
  // Cleanup intervals when the component is unmounted or simulation state disappears
  onUnmounted(() => {
    if (metricInterval) clearInterval(metricInterval);
    if (logInterval) clearInterval(logInterval);
  });
  watch(() => props.simulationState, (newState) => {
      if(!newState){ // If simulation state is removed (e.g. model deleted)
          if (metricInterval) clearInterval(metricInterval);
          if (logInterval) clearInterval(logInterval);
      }
  })
  
  </script>
  
  <style scoped>
  .fine-tune-visualizer {
    padding: 15px;
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
  }
  
  .fine-tune-visualizer h4 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #495057;
      font-weight: 600;
      border-bottom: 1px solid #dee2e6;
      padding-bottom: 10px;
  }
  
  .visual-stage-info {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
  }
  
  .stage-icon {
    flex-shrink: 0;
    color: var(--el-color-primary); /* Use Element Plus primary color */
  }
  
  .stage-details {
    flex-grow: 1;
  }
  
  .stage-name {
    font-weight: 500;
    color: #343a40;
    margin-bottom: 5px;
  }
  
  .dynamic-info {
    margin-top: 15px;
  }
  
  .metric-card, .log-card {
    height: 200px; /* Fixed height for consistency */
    display: flex;
    flex-direction: column;
  }
  
  .metric-card :deep(.el-card__body),
  .log-card :deep(.el-card__body) {
      flex-grow: 1;
      overflow-y: auto; /* Allow scrolling if content exceeds height */
      padding: 10px 15px; /* Adjust padding */
  }
  
  .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.95em;
      color: #495057;
  }
  .card-header .el-icon {
      margin-right: 5px;
      vertical-align: middle;
  }
  
  
  .metric-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 0.9em;
  }
  
  .metric-value {
    font-weight: bold;
  }
  .metric-value.loss {
      color: #dc3545; /* Red for loss */
  }
  .metric-value.accuracy {
      color: #28a745; /* Green for accuracy */
  }
  .metric-placeholder, .log-placeholder {
      color: #adb5bd;
      font-style: italic;
      text-align: center;
      margin-top: 20px;
  }
  
  
  .log-output {
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.85em;
    line-height: 1.6;
    color: #495057;
    height: 100%; /* Ensure it tries to fill the card body */
    overflow-y: auto;
  }
  .log-output p {
    margin: 2px 0;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .log-timestamp {
      color: #6c757d;
      margin-right: 5px;
  }
  .log-output .warn { color: #ffc107; }
  .log-output .error { color: #dc3545; }
  .log-output .success { color: #28a745; }
  
  
  /* Loading icon animations */
  .is-loading.rotating {
    animation: rotating 2s linear infinite;
  }
  .is-loading.pulsing {
    animation: rotating 1.5s linear infinite, pulse 1s infinite alternate;
  }
  
  @keyframes rotating {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  @keyframes pulse {
    from { opacity: 1; }
    to { opacity: 0.6; }
  }
  </style>