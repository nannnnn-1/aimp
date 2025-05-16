<template>
  <div class="app-container">
    <!-- 左侧导航栏 -->
    <Sidebar class="sidebar" />
    
    <div class="main-content">
      <!-- 顶部栏 -->
      <Header class="header" />
      
      <!-- 主要内容区域 -->
      <main class="content">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 150px;
  background-color: #f8f9fe;
  border-right: 1px solid #eee;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  height: 60px;
  border-bottom: 1px solid #eee;
}

.content {
  flex: 1;
  padding: 20px;
  background-color: #f8f9fe;
}
</style> 