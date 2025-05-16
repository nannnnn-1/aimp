<!-- src/components/misc/FloatingNotes.vue -->
<template>
    <div
      ref="notesWidgetRef"
      class="floating-notes-widget"
      :class="{ 'is-expanded': isExpanded }"
      :style="{ top: position.y + 'px', left: position.x + 'px' }"
      @mousedown="startDrag"
    >
      <div v-if="!isExpanded" class="collapsed-ball" @click.stop="toggleExpand">
        <el-icon><EditPen /></el-icon>
      </div>
      <div v-else class="expanded-window">
        <div class="notes-header" @mousedown="startDrag">
          <span>任务笔记</span>
          <el-icon class="close-icon" @click.stop="toggleExpand"><Close /></el-icon>
        </div>
        <div class="notes-body">
          <el-input
            v-model="notesContent"
            type="textarea"
            :rows="10"
            placeholder="在此记录笔记..."
            resize="none"
            @input="handleInput"
          />
        </div>
        <!-- <div class="notes-footer">
          <el-button size="small" @click="saveNotes">保存</el-button>
          <el-button size="small" @click="clearNotes">清空</el-button>
        </div> -->
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, watch, nextTick , computed, onBeforeUnmount} from 'vue';
  import { ElIcon, ElInput, ElButton } from 'element-plus';
  import { EditPen, Close } from '@element-plus/icons-vue';
  
  const props = defineProps<{
    taskId: number | string; // Pass task ID to scope notes
  }>();
  
  const isExpanded = ref(false);
  const notesContent = ref('');
  const notesWidgetRef = ref<HTMLElement | null>(null);
  
  // --- Position & Dragging ---
  const position = ref({ x: window.innerWidth - 100, y: window.innerHeight - 100 }); // Initial position bottom-right
  const dragging = ref(false);
  const offset = ref({ x: 0, y: 0 });
  
  const startDrag = (event: MouseEvent) => {
    // Prevent drag start on textarea or close button itself maybe?
    if ((event.target as HTMLElement).closest('.notes-body') || (event.target as HTMLElement).closest('.close-icon')) {
       return;
    }
    dragging.value = true;
    offset.value.x = event.clientX - position.value.x;
    offset.value.y = event.clientY - position.value.y;
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', stopDrag);
  };
  
  const handleDrag = (event: MouseEvent) => {
    if (!dragging.value) return;
    event.preventDefault(); // Prevent text selection during drag
    position.value.x = event.clientX - offset.value.x;
    position.value.y = event.clientY - offset.value.y;
  
    // Optional: Keep widget within bounds
    keepWithinBounds();
  };
  
  const stopDrag = () => {
    if (!dragging.value) return;
    dragging.value = false;
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', stopDrag);
    // Save position after drag ends
    savePosition();
  };
  
  const keepWithinBounds = () => {
      if (!notesWidgetRef.value) return;
      const widgetRect = notesWidgetRef.value.getBoundingClientRect();
      const maxX = window.innerWidth - widgetRect.width;
      const maxY = window.innerHeight - widgetRect.height;
  
      position.value.x = Math.max(0, Math.min(position.value.x, maxX));
      position.value.y = Math.max(0, Math.min(position.value.y, maxY));
  };
  
  // --- Notes Persistence (using Local Storage for simplicity) ---
  const storageKey = computed(() => `task_${props.taskId}_notes`);
  const positionStorageKey = computed(() => `task_notes_widget_position`);
  
  const saveNotes = () => {
    localStorage.setItem(storageKey.value, notesContent.value);
  };
  
  const loadNotes = () => {
    notesContent.value = localStorage.getItem(storageKey.value) || '';
  };
  
  const savePosition = () => {
      localStorage.setItem(positionStorageKey.value, JSON.stringify(position.value));
  };
  
  const loadPosition = () => {
      const savedPos = localStorage.getItem(positionStorageKey.value);
      if (savedPos) {
          try {
              position.value = JSON.parse(savedPos);
              // Ensure loaded position is valid after potential screen resize
               nextTick(keepWithinBounds);
          } catch (e) {
              console.error("Failed to parse saved position", e);
              // Use default if parsing fails
              position.value = { x: window.innerWidth - 100, y: window.innerHeight - 100 };
          }
      } else {
           // Use default if nothing saved
           position.value = { x: window.innerWidth - 100, y: window.innerHeight - 100 };
      }
  };
  
  
  // Auto-save on input (debounced might be better for performance)
  let debounceTimer: number | undefined;
  const handleInput = () => {
      clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(() => {
          saveNotes();
      }, 500); // Save 500ms after user stops typing
  };
  
  // --- Toggle ---
  const toggleExpand = () => {
    isExpanded.value = !isExpanded.value;
     // Adjust position slightly when collapsing/expanding if needed, or ensure bounds check
     nextTick(keepWithinBounds);
  };
  
  // --- Lifecycle ---
  onMounted(() => {
    loadNotes();
    loadPosition();
    // Adjust bounds check on window resize
    window.addEventListener('resize', keepWithinBounds);
  });
  
  onBeforeUnmount(() => {
    window.removeEventListener('resize', keepWithinBounds);
    // Clear timeout if component is unmounted
    clearTimeout(debounceTimer);
  });
  
  </script>
  
  <style scoped>
  .floating-notes-widget {
    position: fixed;
    z-index: 1000;
    cursor: grab;
    transition: width 0.3s ease, height 0.3s ease, border-radius 0.3s ease;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  }
  
  .floating-notes-widget:active {
    cursor: grabbing;
  }
  
  .collapsed-ball {
    width: 50px;
    height: 50px;
    background-color: #4318FF; /* Theme color */
    color: white;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 24px;
    cursor: pointer; /* Change cursor for the ball itself */
    transition: background-color 0.2s;
  }
  .collapsed-ball:hover {
     background-color: #3311cc;
  }
  
  .expanded-window {
    width: 350px; /* Adjust width */
    height: 400px; /* Adjust height */
    background-color: white;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Contain children */
  }
  
  .notes-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background-color: #f8f9fc;
    border-bottom: 1px solid #e0e5f2;
    font-weight: bold;
    color: #2b3674;
    cursor: grab; /* Header is draggable */
  }
  
  .notes-header span {
      flex-grow: 1; /* Allow title to take space */
  }
  
  .close-icon {
    cursor: pointer;
    color: #a3aed0;
    font-size: 18px;
  }
  .close-icon:hover {
    color: #f1416c;
  }
  
  .notes-body {
    flex-grow: 1;
    padding: 5px; /* Minimal padding around textarea */
    display: flex; /* Make textarea fill */
  }
  
  .notes-body .el-textarea {
     flex-grow: 1; /* Textarea fills body */
     height: 100%; /* Fill vertically */
  }
  .notes-body :deep(.el-textarea__inner) {
     height: 100% !important;
     border: none;
     box-shadow: none;
     padding: 8px; /* Internal padding */
     font-size: 14px;
  }
  
  /* Optional Footer */
  /* .notes-footer {
    padding: 8px 12px;
    border-top: 1px solid #e0e5f2;
    text-align: right;
  } */
  </style>