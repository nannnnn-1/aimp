<template>
  <div class="login-page" v-if="route.name === 'portal' || route.name ==='login' || route.name ==='register'">

      
      <router-view></router-view>
  </div>
  <div class="app" v-else>

    <Sidebar class="sidebar" />
      <div class="main">
        <Header />
        <div class="content">
          <router-view></router-view>
        </div>
      </div>

  </div>
  <!-- <MapTest /> -->
</template>

<script setup lang="ts">
import MapTest from './views/MapTest.vue'
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import Header from './components/Header.vue'

const route = useRoute()
const isLoginPage = computed(() => route.name === 'portal')
onMounted(() => {
  // 检查 token 状态
  const token = localStorage.getItem('token')
  console.log('App mounted - token状态:', token ? '存在' : '不存在')
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: #f8f9fe;
  color: #2b3674;
}

/* 图标字体样式 */
@font-face {
  font-family: 'iconfont';
  src: url('/fonts/iconfont.woff2') format('woff2');
}

.icon-search,
.icon-bell,
.icon-chevron-down,
.icon-grid,
.icon-calendar,
.icon-users,
.icon-folder,
.icon-bar-chart,
.icon-settings,
.icon-plus,
.icon-chevron-left,
.icon-chevron-right {
  font-family: 'iconfont';
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  height: 100vh;
  display: flex;
}

.sidebar {
  flex-shrink: 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content {
  flex: 1;
  overflow: auto;
  background: #f4f7fe;
}
.login-page {
  height: 100vh;
}
</style>
