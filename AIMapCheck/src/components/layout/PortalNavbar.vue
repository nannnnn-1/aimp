<!-- src/components/layout/PortalNavbar.vue -->
<template>
    <nav class="portal-navbar">
      <div class="navbar-content">
        <!-- Left: Logo/Title -->
        <div class="navbar-brand">
          <img src="/images/logo.png" alt="Logo" class="navbar-logo" />
          <span class="navbar-title">AI智能审图平台</span>
        </div>
  
        <!-- Right: Actions -->
        <div class="navbar-actions">
           <a href="#" class="nav-link">关于我们</a>
           <el-button type="primary" round @click="goToLogin">登录</el-button>
           <el-button round plain @click="goToRegister">注册</el-button>
        </div>
      </div>
    </nav>
  </template>
  
  <script setup lang="ts">
  import { useRouter } from 'vue-router';
  import { ElButton } from 'element-plus';
  
  const router = useRouter();
  
  const goToLogin = () => {
    // TODO: Replace '/login' with your actual login route path
    router.push('/login');
  };
  
  const goToRegister = () => {
    // TODO: Replace '/register' with your actual register route path
    router.push('/register');
  };
  </script>
  
  <style scoped>
  .portal-navbar {
    position: fixed; /* Or sticky */
    top: 0;
    left: 0;
    right: 0;
    z-index: 10; /* Ensure above overlay and content */
    background-color: rgba(15, 23, 42, 0.8); /* Semi-transparent dark background */
    backdrop-filter: blur(5px); /* Optional blur effect */
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 10px 5%; /* Padding left/right */
    height: 60px; /* Navbar height */
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }
  
  .navbar-content {
    max-width: 1400px; /* Match content max-width */
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
  }
  
  .navbar-brand {
    display: flex;
    align-items: center;
  }
  
  .navbar-logo {
    height: 30px; /* Adjust logo size */
    margin-right: 15px;
  }
  
  .navbar-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
  }
  
  .navbar-actions {
    display: flex;
    align-items: center;
    gap: 15px; /* Space between buttons */
  }
  
  /* Optional styles for other nav links if added */
  .nav-link {
      color: rgba(255, 255, 255, 0.8);
      text-decoration: none;
      font-size: 0.95rem;
      padding: 5px 10px;
      border-radius: 4px;
      transition: background-color 0.2s, color 0.2s;
  }
  .nav-link:hover {
      background-color: rgba(255, 255, 255, 0.1);
      color: #ffffff;
  }
  
  /* Button styling adjustments */
  .navbar-actions .el-button {
      /* font-size: 0.9rem; */ /* Adjust if needed */
  }
  .navbar-actions .el-button--primary {
     /* Customize primary button if needed */
  }
  .navbar-actions .el-button--default.is-plain, /* Targeting plain button */
  .navbar-actions .el-button.is-plain { /* General plain button */
     color: #fff;
     background: transparent;
     border-color: rgba(255, 255, 255, 0.5);
  }
  .navbar-actions .el-button--default.is-plain:hover,
  .navbar-actions .el-button.is-plain:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.8);
  }
  
  </style>