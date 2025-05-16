<template>
  <div class="dialog-overlay" v-if="modelValue" @click="closeDialog">
    <div class="dialog-content" @click.stop>
      <div class="dialog-header">
        <h3>新建任务</h3>
        <button class="close-btn" @click="closeDialog">
          <i class="icon-close">×</i>
        </button>
      </div>
      
      <div class="dialog-body">
        <div class="form-group">
          <label>任务名称</label>
          <input 
            type="text" 
            v-model="taskName"
            placeholder="请输入任务名称"
            @keyup.enter="createTask"
          />
        </div>
      </div>
      
      <div class="dialog-footer">
        <button class="btn-cancel" @click="closeDialog">取消</button>
        <button 
          class="btn-confirm" 
          :disabled="!taskName.trim()"
          @click="createTask"
        >
          创建
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'create', taskName: string): void
}>()

const taskName = ref('')

const closeDialog = () => {
  emit('update:modelValue', false)
  taskName.value = ''
}

const createTask = () => {
  if (taskName.value.trim()) {
    emit('create', taskName.value.trim())
    closeDialog()
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  background: white;
  border-radius: 16px;
  width: 400px;
  max-width: 90%;
}

.dialog-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  color: #2b3674;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #a3aed0;
  cursor: pointer;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #2b3674;
  font-size: 14px;
}

.form-group input {
  padding: 8px 12px;
  border: 1px solid #e0e5f2;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  
  &:focus {
    border-color: #4318FF;
  }
}

.dialog-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-cancel {
  background: white;
  border: 1px solid #e0e5f2;
  color: #2b3674;
}

.btn-confirm {
  background: #4318FF;
  border: none;
  color: white;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style> 