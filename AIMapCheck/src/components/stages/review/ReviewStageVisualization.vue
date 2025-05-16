<template>
    <div class="review-visualization">
      <!-- Map Display Area -->
      <div class="map-container" ref="mapContainerRef">
        <!-- Original map image (opacity changes during/after review) -->
        <img
          v-if="originalMapUrl"
          ref="originalMapImageRef"
          :src="originalMapUrl"
          alt="原始地图"
          class="original-map-image"
          :style="{ opacity: originalMapOpacity }"
          @load="onMapImageLoad"
        />
        <!-- Placeholder while loading initial state -->
        <div v-else-if="isLoading" class="empty-state map-placeholder">
           <i class="fas fa-spinner fa-spin"></i> 正在加载阶段信息...
        </div>
        <!-- Error message if map fails to load and not showing errors -->
        <div v-else-if="!originalMapUrl && !showErrorVisualization" class="empty-state map-placeholder error-text">
            <i class="fas fa-exclamation-triangle"></i> 无法加载原始地图。
        </div>
  
        <!-- Tile container (for sequential display) -->
        <!-- @vue-ignore -->
        <div
          v-if="isReviewing"
          class="tile-overlay-container"
          :style="tileOverlayStyle"
        >
           <!-- Render sequentially displayed tiles -->
           <!-- eslint-disable-next-line vue/valid-v-bind -->
           <!-- @vue-ignore -->
           <img
              v-for="tile in displayedTiles"
              :key="tile.key"
              :src="tile.url"
              class="review-tile-image"
              :style="calculateTileStyle(tile)"
           />
        </div>
  
        <!-- Error Visualization Overlay (Red Boxes) -->
        <!-- @vue-ignore -->
        <div
          v-if="showErrorVisualization"
          class="error-box-overlay-container"
          :style="tileOverlayStyle"
        >
           <!-- Render red boxes for errors -->
           <div
              v-for="error in displayedErrorList"
              :key="error.tileKey"
              class="error-box"
              :style="error.boxStyle"
           ></div>
        </div>
  
        <!-- Error Image Display Margin (Right) -->
        <!-- @vue-ignore -->
        <div
          v-if="showErrorVisualization && displayedErrorList.length > 0"
          class="error-image-margin"
          :style="errorMarginStyle"
        >
            <h4>检测到的错误瓦片:</h4>
            <div class="error-image-list">
               <!-- Display errors from displayedErrorList -->
               <div v-for="(error, index) in displayedErrorList" :key="error.tileKey" class="error-image-item">
                  <i :class="['fas', error.displaySide === 'left' ? 'fa-arrow-left' : 'fa-arrow-right', 'side-indicator']"></i>
                   <!-- Ensure click passes the whole 'error' object -->
                  <img
                     :src="error.imageUrl"
                     :alt="`错误瓦片 ${error.row}-${error.col}`"
                     @click="showErrorDetail(error)"
                     class="error-preview-image"
                  />
                  <span>{{ index + 1 }}. (行: {{error.row}}, 列: {{error.col}})</span>
               </div>
            </div>
        </div>
  
         <!-- Error Detail Display Margin (Left) -->
         <!-- @vue-ignore -->
         <div
           v-if="selectedErrorDetails"
           class="error-detail-margin"
           :style="errorDetailMarginStyle"
         >
            <button class="close-detail-btn" @click="hideErrorDetail">
               <i class="fas fa-times"></i> 关闭
            </button>
             <!-- Safely access properties using optional chaining -->
            <h4>错误瓦片详情 (行: {{selectedErrorDetails?.row}}, 列: {{selectedErrorDetails?.col}})</h4>
  
            <!-- Error Image -->
            <img
               :src="selectedErrorDetails?.imageUrl"
               :alt="`错误瓦片 ${selectedErrorDetails?.row}-${selectedErrorDetails?.col}`"
               class="detail-error-image"
            />
  
            <!-- Error Details Section -->
            <div class="error-details-content">
                <!-- Safely access properties using optional chaining -->
                <p v-if="selectedErrorDetails?.cls_name"><strong>类型:</strong> {{ selectedErrorDetails.cls_name }}</p>
               <p v-if="selectedErrorDetails?.category"><strong>类别:</strong> {{ selectedErrorDetails.category }}</p>
               <p v-if="selectedErrorDetails?.severity"><strong>严重性:</strong> {{ selectedErrorDetails.severity }}</p>
               <p v-if="selectedErrorDetails?.description"><strong>描述:</strong> {{ selectedErrorDetails.description }}</p>
               <p v-if="selectedErrorDetails?.solution"><strong>建议方案:</strong> {{ selectedErrorDetails.solution }}</p>
               <!-- Add other fields if needed -->
            </div>
         </div>
  
         <!-- Loading indicator for errors -->
         <div v-if="isLoadingErrors" class="loading-overlay simple-loading">
            <i class="fas fa-spinner fa-spin"></i> 正在加载错误信息...
         </div>
  
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted, computed, reactive, nextTick } from 'vue'
  import { ElMessage } from 'element-plus'
  import { useRoute } from 'vue-router'
  import axios from 'axios';
  
  const emit = defineEmits(['error_visualization_completed']);
  
  interface Tile { x: number; y: number; z: number; url: string; key: string; }
  
  // Updated ErrorInfo to include details
  interface ErrorInfo {
      row: number;
      col: number;
      tileKey: string;
      imageUrl: string;
      boxStyle: Record<string, string>;
      displaySide: 'left' | 'right';
      // Add detailed fields (match names from your error_examples if possible)
      cls_name?: string; // Original class name if available
      category?: string; // e.g., '道路断裂', '注记错误'
      severity?: string; // e.g., '严重', '一般', '提示'
      description?: string; // Description of the error type
      solution?: string; // Suggested solution
  }
  
  // Expected data structure from the /errors endpoint
  interface BackendErrorData {
      row: number;
      col: number;
      cls_name?: string;
      error_category?: string;
      severity?: string;
      description?: string;
      solution?: string;
  }
  
  // Fix for linter error: Define the expected structure for the stage data response
  interface StageApiResponse {
      stage: {
          status: string;
          // Add other potential fields from the stage endpoint if needed
      };
      // Include grid parameters if returned by this endpoint
      // grid_params?: { rows: number; cols: number; tile_size: number; overlap: number; format: string; };
  }
  
  const route = useRoute()
  const taskId = parseInt(route.params.id as string)
  
  // Use gridParams from loadErrorExamples if available, otherwise default
  // Assuming gridParams might be loaded dynamically later or is fixed
  let gridParams = reactive({ rows: 0, cols: 0, tileSize: 640, overlap: 0.20, format: 'jpg' }); // Start empty if dynamic
  
  
  // --- Component State ---
  const isLoading = ref(true);
  const isReviewing = ref(false);
  const isLoadingErrors = ref(false);
  const showErrorVisualization = ref(false);
  const originalMapUrl = ref<string | null>(null)
  const originalMapOpacity = ref(1.0);
  const mapContainerRef = ref<HTMLDivElement | null>(null);
  const originalMapImageRef = ref<HTMLImageElement | null>(null);
  const mapDisplaySize = reactive({ width: 0, height: 0 });
  const mapDisplayOffset = reactive({ top: 0, left: 0 });
  const marginWidth = ref(0);
  const gridScale = ref(1);
  const displayedTiles = reactive<Tile[]>([]);
  const displayedErrorList = reactive<ErrorInfo[]>([]);
  const rawBackendErrorData = ref<BackendErrorData[]>([]); // Store raw data from backend
  const currentTileIndex = ref(0);
  const tileDisplayInterval = ref<number | null>(null);
  const currentErrorIndex = ref(0);
  const errorDisplayInterval = ref<number | null>(null);
  const selectedErrorDetails = ref<ErrorInfo | null>(null); // Replaces selectedErrorImageUrl
  const TILE_DISPLAY_INTERVAL_MS = 100; // Keep tile interval potentially fast
  const ERROR_DISPLAY_INTERVAL_MS = 1000;
  
  // --- Computed Properties ---
  const totalTiles = computed(() => gridParams.rows * gridParams.cols);
  
  const unscaledGridSize = computed(() => {
      const { rows, cols, tileSize, overlap } = gridParams;
      if (rows <= 0 || cols <= 0 || tileSize <= 0) return { width: 0, height: 0 };
      // Ensure overlap is treated correctly (e.g., 0.2 means 20% overlap)
      const effectiveTileSize = tileSize * (1 - overlap);
      // Ensure effectiveTileSize is positive
      if (effectiveTileSize <= 0) {
          console.error("Invalid grid parameters: effective tile size is not positive.");
          return { width: 0, height: 0 };
      }
      const width = (cols - 1) * effectiveTileSize + tileSize;
      const height = (rows - 1) * effectiveTileSize + tileSize;
      return { width, height };
  });
  
  const tileOverlayStyle = computed(() => ({
      position: 'absolute',
      top: `${mapDisplayOffset.top}px`,
      left: `${mapDisplayOffset.left}px`,
      width: `${mapDisplaySize.width}px`,
      height: `${mapDisplaySize.height}px`,
      overflow: 'hidden',
      zIndex: 5,
      pointerEvents: 'none',
  }));
  
  const errorMarginStyle = computed(() => ({
      position: 'absolute',
      top: '0px',
      right: '0px',
      width: `${marginWidth.value}px`,
      height: '100%',
      backgroundColor: 'rgba(240, 240, 240, 0.9)',
      borderLeft: '1px solid #ccc',
      padding: '10px',
      boxSizing: 'border-box',
      overflowY: 'auto',
      zIndex: 10,
  }));
  
  const errorDetailMarginStyle = computed(() => ({
      position: 'absolute',
      top: '0px',
      left: '0px',
      width: `${marginWidth.value}px`,
      height: '100%',
      backgroundColor: 'rgba(220, 220, 220, 0.95)',
      borderRight: '1px solid #ccc',
      padding: '10px',
      boxSizing: 'border-box',
      overflowY: 'auto',
      zIndex: 15,
      display: 'flex',
      flexDirection: 'column',
  }));
  
  // --- API URLs ---
  const getStageDataUrl = () => `http://8.148.68.206:5000/api/tasks/${taskId}/stage/4`; // Assuming stage 4 is review
  const getOriginalMapUrl = () => `http://8.148.68.206:5000/api/tasks/${taskId}/original/original_map.png?t=${Date.now()}`;
  const getTileUrl = (row: number, col: number) => `http://8.148.68.206:5000/api/tasks/${taskId}/review/tiles/original_map_tiles/tile_${row}_${col}.${gridParams.format}`; // Assuming static path structure
  const getErrorTileUrl = (row: number, col: number) => `http://8.148.68.206:5000/api/tasks/${taskId}/review/error_tiles/error_tile_row${row}_col${col}.jpg`; // Assuming static path structure
  const getErrorListUrl = () => `http://8.148.68.206:5000/api/tasks/${taskId}/review/errors`; // Endpoint for detailed error list
  
  // --- Methods ---
  const calculateGridScale = () => {
      if (!mapContainerRef.value || mapDisplaySize.width <= 0 || mapDisplaySize.height <= 0 ||
          unscaledGridSize.value.width <= 0 || unscaledGridSize.value.height <= 0)
      { gridScale.value = 1; return; }
      const scaleX = mapDisplaySize.width / unscaledGridSize.value.width;
      const scaleY = mapDisplaySize.height / unscaledGridSize.value.height;
      gridScale.value = Math.min(scaleX, scaleY);
  };
  
  const onMapImageLoad = async () => {
      if (isLoading.value) {
          isLoading.value = false;
      }
      console.log("原始地图图像已加载。");
      await nextTick();
      if (originalMapImageRef.value && mapContainerRef.value) {
          mapDisplaySize.width = originalMapImageRef.value.clientWidth;
          mapDisplaySize.height = originalMapImageRef.value.clientHeight;
          const containerWidth = mapContainerRef.value.clientWidth;
          const containerHeight = mapContainerRef.value.clientHeight;
          mapDisplayOffset.left = Math.max(0, (containerWidth - mapDisplaySize.width) / 2); // Ensure non-negative
          mapDisplayOffset.top = Math.max(0, (containerHeight - mapDisplaySize.height) / 2); // Ensure non-negative
          marginWidth.value = Math.max(0, mapDisplayOffset.left);
          console.log(`Map loaded. Display: ${mapDisplaySize.width}x${mapDisplaySize.height}, Offset: T${mapDisplayOffset.top} L${mapDisplayOffset.left}, MarginW: ${marginWidth.value}`);
          calculateGridScale();
          // Recalculate error box styles if map loads after errors were processed
          if (showErrorVisualization.value && displayedErrorList.length > 0) {
               console.log("重新计算错误框样式...");
               recalculateErrorBoxStyles();
          }
          // Trigger interval if review process was waiting for map load
          if (isReviewing.value && !tileDisplayInterval.value && totalTiles.value > 0) {
               startTileInterval();
          }
      } else {
          console.error("无法获取图像或容器引用以计算尺寸/偏移量。");
          if (!isLoading.value && showErrorVisualization.value) {
              ElMessage.warning("无法计算地图尺寸，错误框可能定位不准。");
          }
      }
  }
  
  const loadMap = () => {
      console.log("加载原始地图 URL...");
      mapDisplaySize.width = 0;
      mapDisplaySize.height = 0;
      mapDisplayOffset.left = 0;
      mapDisplayOffset.top = 0;
      marginWidth.value = 0;
      gridScale.value = 1;
      selectedErrorDetails.value = null; // Use new state variable
      originalMapUrl.value = getOriginalMapUrl();
  }
  
  const stopDisplayIntervals = () => {
      if (tileDisplayInterval.value) {
          clearInterval(tileDisplayInterval.value);
          tileDisplayInterval.value = null;
      }
      if (errorDisplayInterval.value) {
          clearInterval(errorDisplayInterval.value);
          errorDisplayInterval.value = null;
      }
  };
  
  const calculateErrorBoxStyle = (row: number, col: number): Record<string, string> => {
      const { tileSize, overlap } = gridParams;
      const scale = gridScale.value;
      if (scale <= 0 || tileSize <= 0) return {};
      const effectiveTileSizeUnscaled = tileSize * (1 - overlap);
      if (effectiveTileSizeUnscaled <= 0) return {}; // Avoid division by zero or negative size
  
      const scaledEffectiveTileSize = effectiveTileSizeUnscaled * scale;
      const scaledTileSize = tileSize * scale;
      const left = col * scaledEffectiveTileSize;
      const top = row * scaledEffectiveTileSize;
      return {
          position: 'absolute',
          left: `${left}px`,
          top: `${top}px`,
          width: `${scaledTileSize}px`,
          height: `${scaledTileSize}px`,
          border: '2px solid red',
          boxSizing: 'border-box',
          pointerEvents: 'none',
          zIndex: '7'
      };
  }
  
  const recalculateErrorBoxStyles = () => {
      displayedErrorList.forEach(error => {
          error.boxStyle = calculateErrorBoxStyle(error.row, error.col);
      });
  };
  
  // Updated to process richer BackendErrorData into ErrorInfo
  const processAndAddError = (errorData: BackendErrorData, index: number) => {
      const { row, col } = errorData;
      const displaySide = (index % 2 === 0) ? 'left' : 'right';
      // Ensure gridParams are loaded before checking bounds
      if (gridParams.rows <= 0 || gridParams.cols <= 0) {
          console.error("Grid parameters not set before processing errors.");
          return; // Skip if grid size is unknown
      }
      if (row >= 0 && row < gridParams.rows && col >= 0 && col < gridParams.cols) {
          const errorInfo: ErrorInfo = {
              row: row, col: col, tileKey: `error-${row}-${col}`,
              imageUrl: getErrorTileUrl(row, col),
              boxStyle: calculateErrorBoxStyle(row, col),
              displaySide: displaySide,
              // Map fields from backend data
              cls_name: errorData.cls_name,
              category: errorData.error_category || errorData.cls_name, // Fallback category to cls_name
              severity: errorData.severity,
              description: errorData.description,
              solution: errorData.solution,
          };
          displayedErrorList.push(errorInfo);
      } else {
          console.warn(`跳过无效的错误坐标: row=${row}, col=${col} (Grid: ${gridParams.rows}x${gridParams.cols})`);
      }
  };
  
  const displayNextError = () => {
      if (currentErrorIndex.value >= rawBackendErrorData.value.length) {
          stopDisplayIntervals();
          emit('error_visualization_completed');
          ElMessage.success("错误可视化完成。");
          return;
      }
      const errorData = rawBackendErrorData.value[currentErrorIndex.value];
      processAndAddError(errorData, currentErrorIndex.value); // Use helper
      currentErrorIndex.value++;
  };
  
  // Fetches error list and stores it in rawBackendErrorData
  const fetchErrorList = async (): Promise<boolean> => {
      console.log("获取错误列表...");
      isLoadingErrors.value = true;
      rawBackendErrorData.value = []; // Clear previous raw data
      let success = false;
      try {
          // Expect the backend to return BackendErrorData[]
          const response = await axios.get<BackendErrorData[]>(getErrorListUrl());
          const errors = response.data;
          if (Array.isArray(errors)) {
              // IMPORTANT: Load Grid Params FIRST if dynamic
              if (gridParams.rows === 0 || gridParams.cols === 0) {
                  console.warn("Grid parameters not loaded before fetching errors. Attempting to use placeholders.");
                  // Fetch or set grid params here
                  // Example: await loadGridParams();
                  // If still zero, use placeholders or fail
                  if (gridParams.rows === 0 || gridParams.cols === 0) {
                       gridParams.rows = 12; // Placeholder
                       gridParams.cols = 17; // Placeholder
                       console.warn(`Using placeholder grid size: ${gridParams.rows}x${gridParams.cols}`);
                       // Recalculate scale based on potential new grid size and existing map display size
                       calculateGridScale();
                  }
              }
  
              rawBackendErrorData.value = errors; // Store raw data
              console.log(`获取到 ${errors.length} 个错误瓦片数据。`);
              success = true;
          } else {
               console.error("错误列表响应格式不正确:", errors);
               ElMessage.error("无法解析错误列表。");
          }
      } catch (error) {
          console.error("获取错误列表失败:", error);
          ElMessage.error("无法加载错误信息。");
      } finally {
          isLoadingErrors.value = false;
      }
      return success;
  };
  
  // Displays all errors from rawBackendErrorData immediately
  const displayAllErrorsImmediately = () => {
      console.log("立即显示所有错误...");
      stopDisplayIntervals();
      displayedErrorList.splice(0, displayedErrorList.length);
      if (rawBackendErrorData.value.length === 0) {
          console.log("无错误可显示。");
          showErrorVisualization.value = false; // Ensure overlay is hidden if no errors
          emit('error_visualization_completed'); // Still completed, just no errors
          return;
      }
  
      // Ensure grid params are set (might have been loaded in fetchErrorList)
      if (gridParams.rows === 0 || gridParams.cols === 0) {
          console.error("无法显示错误：Grid 参数未设置。");
          ElMessage.error("地图网格信息加载失败，无法显示错误。");
          return;
      }
  
      showErrorVisualization.value = true;
      rawBackendErrorData.value.forEach((errorData, index) => {
          processAndAddError(errorData, index); // Use helper
      });
      console.log(`${displayedErrorList.length} 个错误已添加到显示列表。`);
  
      // Ensure styles are correct after adding all errors and potential map load
      nextTick(() => {
          if (mapDisplaySize.width > 0 && mapDisplaySize.height > 0) {
              recalculateErrorBoxStyles();
          } else {
              console.warn("Map dimensions not ready, error boxes might be initially unstyled.");
          }
      });
      emit('error_visualization_completed'); // Emit completion as it's instant
  };
  
  
  const displayNextTile = () => {
      if (totalTiles.value <= 0 || currentTileIndex.value >= totalTiles.value) {
          stopDisplayIntervals();
          isReviewing.value = false;
          originalMapOpacity.value = 1.0;
          // Fetch errors and then start the *interval* display
          fetchErrorList().then(success => {
              if (success && rawBackendErrorData.value.length > 0) {
                  console.log("瓦片显示完成，开始逐个显示错误...");
                  showErrorVisualization.value = true;
                  currentErrorIndex.value = 0;
                  // Delay start slightly?
                  errorDisplayInterval.value = window.setInterval(displayNextError, ERROR_DISPLAY_INTERVAL_MS);
              } else if (success) {
                   ElMessage.info("未检测到错误瓦片。");
                   emit('error_visualization_completed');
              }
          });
          return;
      }
  
      const cols = gridParams.cols;
      const rowIndex = Math.floor(currentTileIndex.value / cols);
      const colIndex = currentTileIndex.value % cols;
      const tileUrl = getTileUrl(rowIndex, colIndex);
      const tileKey = `0-${rowIndex}-${colIndex}`;
      const newTile: Tile = { x: colIndex, y: rowIndex, z: 0, url: tileUrl, key: tileKey };
      displayedTiles.push(newTile);
      currentTileIndex.value++;
  };
  
  const startTileInterval = () => {
      if (mapDisplaySize.width <= 0 || mapDisplaySize.height <= 0) {
           console.warn("地图尺寸未就绪，延迟启动瓦片显示。");
          return; // Wait for map to load fully
      }
      if (tileDisplayInterval.value) return;
      if (totalTiles.value <= 0) {
          console.error("无法启动瓦片显示：总瓦片数为零或无效。");
          return;
      }
      tileDisplayInterval.value = window.setInterval(displayNextTile, TILE_DISPLAY_INTERVAL_MS);
  }
  
  const startSequentialTileDisplay = () => {
      console.log("开始顺序瓦片显示...");
      if (isReviewing.value || isLoadingErrors.value || errorDisplayInterval.value) {
          ElMessage.warning("请等待当前操作完成。");
          return;
      }
       // Ensure grid params are known before calculating totalTiles
      if (gridParams.rows <= 0 || gridParams.cols <= 0) {
          // TODO: Attempt to load grid params first
          ElMessage.error("地图网格信息未加载，无法开始审阅。");
          return;
      }
       if (totalTiles.value <= 0) {
          ElMessage.error("瓦片配置错误或数量为零。");
          return;
      }
  
      // Reset state
      stopDisplayIntervals();
      displayedTiles.splice(0, displayedTiles.length);
      displayedErrorList.splice(0, displayedErrorList.length);
      rawBackendErrorData.value = [];
      selectedErrorDetails.value = null;
      currentTileIndex.value = 0;
      currentErrorIndex.value = 0;
      showErrorVisualization.value = false;
      isReviewing.value = true;
      originalMapOpacity.value = 0.1;
      // Start interval only if map is already loaded, otherwise onMapImageLoad will start it
      if (mapDisplaySize.width > 0 && mapDisplaySize.height > 0) {
         // Delay start to allow opacity transition
         setTimeout(() => {
            startTileInterval();
         }, 12000); // 等待10秒后开始显示瓦片
      } else {
          console.log("地图尚未加载，将在加载后开始瓦片显示。");
      }
  };
  
  const calculateTileStyle = (tile: Tile) => {
      const { tileSize, overlap } = gridParams;
      const scale = gridScale.value;
      if (scale <= 0 || tileSize <= 0) return {};
      const effectiveTileSizeUnscaled = tileSize * (1 - overlap);
       if (effectiveTileSizeUnscaled <= 0) return {};
  
      const scaledEffectiveTileSize = effectiveTileSizeUnscaled * scale;
      const scaledTileSize = tileSize * scale;
      const left = tile.x * scaledEffectiveTileSize;
      const top = tile.y * scaledEffectiveTileSize;
      return {
          position: 'absolute',
          left: `${left}px`,
          top: `${top}px`,
          width: `${scaledTileSize}px`,
          height: `${scaledTileSize}px`,
          willChange: 'transform', // Optimization hint
          zIndex: '6'
      };
  }
  
  const onTileError = (tile: Tile) => {
      console.warn(`错误: 无法加载瓦片 ${tile.key} at ${tile.url}`);
      // Optionally remove the broken tile or show a placeholder
  }
  
  // Updated to accept and store the full ErrorInfo object
  const showErrorDetail = (error: ErrorInfo) => {
      selectedErrorDetails.value = error;
  };
  
  // Updated to clear the ErrorInfo object
  const hideErrorDetail = () => {
      selectedErrorDetails.value = null;
  };
  
  // Placeholder for loading grid parameters - replace with actual API call
  const loadGridParams = async () => {
      // Example: Fetch task details that include grid info
      // const taskDetailUrl = `http://8.148.68.206:5000/api/tasks/${taskId}/details`;
      // try {
      //     const response = await axios.get(taskDetailUrl);
      //     if (response.data && response.data.grid_params) {
      //         gridParams.rows = response.data.grid_params.rows;
      //         gridParams.cols = response.data.grid_params.cols;
      //         gridParams.tileSize = response.data.grid_params.tile_size || 640;
      //         gridParams.overlap = response.data.grid_params.overlap || 0.2;
      //         gridParams.format = response.data.grid_params.format || 'jpg';
      //         console.log("Grid parameters loaded:", gridParams);
      //         return true;
      //     } else {
      //          console.error("Failed to load grid parameters from task details.");
      //          return false;
      //     }
      // } catch (error) {
      //     console.error("Error fetching task details for grid params:", error);
      //     return false;
      // }
  
      // --- Using static values for now ---
      console.warn("Using static grid parameters. Implement dynamic loading.");
      gridParams.rows = 12;
      gridParams.cols = 17;
      gridParams.tileSize = 640;
      gridParams.overlap = 0.20;
      gridParams.format = 'jpg';
      return true;
  };
  
  
  // --- Component Initialization ---
  const initializeComponent = async () => {
      console.log("初始化审查可视化组件...");
      isLoading.value = true;
      stopDisplayIntervals(); // Ensure clean state
      // Reset relevant states
      isReviewing.value = false;
      showErrorVisualization.value = false;
      displayedTiles.splice(0, displayedTiles.length);
      displayedErrorList.splice(0, displayedErrorList.length);
      rawBackendErrorData.value = [];
      selectedErrorDetails.value = null;
      currentTileIndex.value = 0;
      currentErrorIndex.value = 0;
      originalMapOpacity.value = 1.0;
      // Reset gridParams if loaded dynamically
      gridParams.rows = 0;
      gridParams.cols = 0;
  
      // Load grid parameters first
      const gridParamsLoaded = await loadGridParams();
      if (!gridParamsLoaded) {
          ElMessage.error("无法加载地图网格信息，初始化失败。");
          isLoading.value = false;
          return;
      }
       // Recalculate scale after loading grid params
      calculateGridScale(); // Might be 1 if map not loaded yet
  
  
      try {
          // Correctly type the expected response structure
          const response = await axios.get<StageApiResponse>(getStageDataUrl());
          // Safely access status
          const status = response.data?.stage?.status;
          if (!status) {
               throw new Error("Stage status not found in API response.");
          }
          console.log("获取到初始阶段状态:", status);
  
          if (status === 'completed' || status === 'error') {
              console.log("状态为已完成/错误，直接显示错误结果。");
              originalMapOpacity.value = 1.0;
              loadMap(); // Load base map URL (triggers onMapImageLoad)
              // Fetch errors, then display them all at once
              const fetchSuccess = await fetchErrorList();
              if (fetchSuccess) {
                  // Errors will be displayed after map loads OR if map fails but errors loaded
                  displayAllErrorsImmediately();
              }
              // isLoading is handled by onMapImageLoad OR if map fails below
               if (!originalMapUrl.value && !isLoadingErrors.value) {
                   isLoading.value = false;
                   if (displayedErrorList.length > 0) {
                      ElMessage.warning("地图加载失败，错误框可能定位不准。");
                   } else if(!fetchSuccess) {
                       // No map, no errors loaded successfully
                        ElMessage.error("地图和错误信息均加载失败。");
                   }
              }
  
          } else {
              // For 'pending', 'in_progress', or other states, just show the map
              console.log("状态为待定/进行中，显示原始地图。");
              loadMap(); // Load base map URL (triggers onMapImageLoad)
              // isLoading will be set by onMapImageLoad
          }
  
      } catch (error) {
          console.error("初始化组件失败 (无法获取阶段状态):", error);
          ElMessage.error("无法加载阶段状态，请稍后重试。");
          isLoading.value = false; // Stop loading on error
      }
  };
  
  
  // --- Lifecycle Hooks ---
  onMounted(() => {
    initializeComponent(); // Call the init function which now loads grid params first
  })
  
  onUnmounted(() => {
    stopDisplayIntervals();
  })
  
  // Expose method to start the review process (e.g., called by parent)
  defineExpose({
    startSequentialTileDisplay
  })
  
  </script>
  
  <style scoped>
  .review-visualization {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f4f7fe;
    position: relative;
    overflow: hidden; /* Prevent potential scrollbars on main container */
  }
  
  .map-container {
    flex: 1;
    position: relative;
    min-height: 300px;
    background-color: #e9ecef; /* Slightly lighter grey */
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  
  .original-map-image {
      display: block;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      user-select: none;
      transition: opacity 0.5s ease-in-out;
      border: 1px solid #ccc; /* Add a border for clarity */
  }
  
  .tile-overlay-container, .error-box-overlay-container {
      pointer-events: none;
      overflow: hidden;
  }
  
  .review-tile-image {
      position: absolute; /* Ensure tiles are positioned absolutely */
      display: block;
      user-select: none;
      pointer-events: none;
      image-rendering: pixelated; /* Keep pixelated rendering for map tiles */
      background-color: rgba(200, 200, 200, 0.1); /* Faint background for unloaded tiles */
  }
  
  .error-box {
      position: absolute; /* Ensure error boxes are positioned absolutely */
      background-color: rgba(255, 0, 0, 0.1);
  }
  
  .error-image-margin {
      display: flex;
      flex-direction: column;
      box-shadow: -2px 0px 5px rgba(0,0,0,0.1);
      background-color: rgba(248, 249, 250, 0.95); /* Lighter background */
  
      h4 {
          margin: 0 0 10px 0;
          padding: 8px 10px; /* Add padding */
          border-bottom: 1px solid #dee2e6;
          font-size: 14px;
          color: #495057; /* Darker text */
          flex-shrink: 0;
          background-color: rgba(222, 226, 230, 0.8); /* Header background */
      }
  }
  
  .error-image-list {
      flex-grow: 1;
      overflow-y: auto;
      padding: 0 5px 5px 5px; /* Add padding around list items */
  }
  
  .error-image-item {
      display: flex;
      align-items: center;
      margin-bottom: 8px; /* Slightly reduced margin */
      padding: 6px;
      background-color: rgba(255, 255, 255, 0.8); /* More transparent background */
      border-radius: 4px;
      border: 1px solid #e9ecef; /* Light border */
      position: relative;
  
      .error-preview-image {
          width: 55px; /* Slightly smaller */
          height: 55px;
          object-fit: contain;
          margin-right: 8px;
          border: 1px solid #ced4da;
          background-color: #fff;
          cursor: pointer;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
          border-radius: 3px; /* Slight rounding */
      }
      .error-preview-image:hover {
          transform: scale(1.08);
          box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
      }
  
      span {
          font-size: 11px; /* Smaller text */
          color: #495057;
          flex-grow: 1;
          line-height: 1.3; /* Adjust line height */
      }
      .side-indicator {
          font-size: 1.1em;
          margin-right: 6px;
          color: #007bff;
          flex-shrink: 0; /* Prevent shrinking */
      }
  }
  
  .error-detail-margin {
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 2px 0px 5px rgba(0,0,0,0.1);
      background-color: rgba(233, 236, 239, 0.98); /* Slightly different background */
  
      h4 {
          margin: 0;
          padding: 8px 10px;
          border-bottom: 1px solid #ced4da;
          font-size: 14px;
          color: #343a40;
          width: 100%;
          text-align: center;
          flex-shrink: 0;
          box-sizing: border-box; /* Include padding in width */
          background-color: rgba(206, 212, 218, 0.8);
      }
  
      .detail-error-image {
          display: block;
          width: calc(100% - 10px); /* Padding consideration */
          max-height: 50%; /* Allow more space for details */
          object-fit: contain;
          border: 1px solid #adb5bd;
          background-color: #fff;
          margin: 5px auto; /* Center image with margin */
          flex-shrink: 0;
          border-radius: 3px;
      }
  
      .error-details-content {
          flex-grow: 1;
          overflow-y: auto;
          padding: 8px 10px; /* Consistent padding */
          background-color: rgba(255, 255, 255, 0.7);
          border-radius: 4px;
          font-size: 12px; /* Slightly smaller text */
          line-height: 1.5;
          color: #212529;
          margin: 0 5px 5px 5px; /* Add margin */
          border: 1px solid #dee2e6;
  
          p {
              margin: 0 0 6px 0; /* Tighter spacing */
              word-break: break-word; /* Allow breaking long words */
          }
          p strong {
              color: #0056b3; /* Stronger blue */
              margin-right: 5px;
              font-weight: 600; /* Make bold */
          }
          p:last-child {
              margin-bottom: 0;
          }
      }
  
      .close-detail-btn {
          background-color: #dc3545; /* Red for close */
          color: white;
          border: none;
          padding: 4px 8px; /* Smaller padding */
          border-radius: 4px;
          cursor: pointer;
          font-size: 11px;
          line-height: 1;
          position: absolute; /* Keep absolute for easy positioning */
          top: 6px; /* Adjust position */
          right: 6px;
          z-index: 16;
          opacity: 0.8;
          transition: opacity 0.2s ease;
      }
      .close-detail-btn:hover {
          background-color: #c82333; /* Darker red on hover */
          opacity: 1.0;
      }
      .close-detail-btn i {
          margin-right: 3px;
      }
  }
  
  /* Placeholder and Empty State Styles */
  .empty-state {
      position: absolute; /* Allow positioning within map container */
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      display: flex; flex-direction: column; align-items: center;
      justify-content: center; color: #6c757d; text-align: center; padding: 20px;
      user-select: none;
      background-color: rgba(248, 249, 250, 0.7); /* Slight background */
      border-radius: 5px;
      i { font-size: 24px; margin-bottom: 8px; } /* Smaller icon */
  }
  .empty-state.map-placeholder {
      background-color: transparent; /* No background for map loading */
  }
  .empty-state.map-placeholder i {
      margin-right: 8px;
      font-size: 1em;
      margin-bottom: 0;
  }
  .empty-state.error-text {
      color: #dc3545;
      background-color: rgba(255, 224, 227, 0.7); /* Light red background */
      border: 1px solid #f5c6cb;
  }
  
  /* Loading overlay style */
  .loading-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: rgba(255, 255, 255, 0.85); /* Slightly more opaque */
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 20;
      color: #495057;
      border-radius: 5px; /* Match empty state */
  }
  .loading-overlay.simple-loading {
      font-size: 0.9em; /* Slightly smaller text */
      background-color: rgba(248, 249, 250, 0.7);
  }
  .loading-overlay i {
      margin-right: 8px;
      font-size: 1.2em; /* Make spinner slightly larger */
  }
  </style>