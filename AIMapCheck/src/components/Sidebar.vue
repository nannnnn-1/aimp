<template>
  <div class="sidebar">
    <div class="logo" @click="goToPortal" style="cursor: pointer;">
        <img src="../../public/images/logo2.png" alt="Logo" />
        <span class="navbar-title">AI MAPCHECK</span>
    </div>
    
    <nav class="nav-menu">
      <router-link to="/home" class="nav-item" :class="{ active: isHome }">
        <i class="fas fa-home"></i>
        任务中心
      </router-link>
      
      <router-link to="#" class="nav-item" :class="{ active: isMonitor }">
        <i class="fas fa-chart-line"></i>
        任务监测
      </router-link>

      <router-link to="#" class="nav-item" :class="{ active: isReport }">
        <i class="fas fa-file-alt"></i>
        报告查看
      </router-link>

      <router-link to="/model" class="nav-item" :class="{ active: isModel }">
        <i class="fas fa-cog"></i>
        模型管理
      </router-link>

      <router-link to="/sample-library" class="nav-item" :class="{ active: isSampleLibrary }">
        <i class="fas fa-cog"></i>
        样例管理
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isPortal = computed(() => route.path === '/home')
const isHome = computed(() => route.path === '/home')
const isMonitor = computed(() => route.meta.activeMenu === 'monitor')
const isReport = computed(() => route.meta.activeMenu === 'report')
const isModel = computed(() => route.meta.activeMenu === 'model')
const isSampleLibrary = computed(() => route.meta.activeMenu === 'sampleLibrary')
const goToPortal = ()=>{
  router.push('/')
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100%;
  background: white;
  border-right: 1px solid #e0e5f2;
  padding: 24px 0;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 0 24px;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
}

.logo img {
  height: 50px;
  margin-right: 15px;
}
.navbar-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #000000;
  }

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  color: #707eae;
  text-decoration: none;
  transition: all 0.2s;
  
  &:hover {
    background: #f4f7fe;
    color: #4318FF;
  }
  
  &.active {
    background: #4318FF;
    color: white;
  }
}

.nav-item i {
  width: 20px;
  text-align: center;
}
</style> 