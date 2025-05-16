import { createRouter, createWebHistory } from 'vue-router'
import TaskList from '../views/TaskList.vue'
import TaskMonitor from '../views/TaskMonitor.vue'
import TaskReport from '../views/TaskReport.vue'
import Login from '../views/Login.vue'
import { focusableStack } from 'element-plus/es/components/focus-trap/index.mjs'

import MapTest from '../views/MapTest.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path:'/',
      name:'portal',
      component: () => import('../views/Portal.vue'),
      meta:{
        requiresAuth: false
      }
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: {
        requiresAuth: false
      }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/Register.vue'),
    },
    {
      path: '/home',
      name: 'home',
      component: TaskList
    },
    {
      path: '/task/:id',
      name: 'taskMonitor',
      component: TaskMonitor,
      meta: {
        requiresAuth: true,
        activeMenu: 'monitor'
      }
    },
    {
      path: '/task/:id/report',
      name: 'taskReport',
      component: TaskReport,
      meta: {
        requiresAuth: true,
        activeMenu: 'report'
      }
    },
    {
      path: '/model',
      name: 'model',
      component: () => import('../views/Model.vue'),
      meta: {
        requiresAuth: true,
        activeMenu: 'model'
      }
    },
    {
      path: '/sample-library',
      name: 'sampleLibrary',
      component: () => import('../views/SampleLibrary.vue'),
      meta: {
        requiresAuth: true,
        activeMenu: 'sampleLibrary'
      }
    }
    // {
    //   path: '/calendar',
    //   name: 'calendar',
    //   component: () => import('../views/Calendar.vue')
    // },
    // {
    //   path: '/team',
    //   name: 'team',
    //   component: () => import('../views/Team.vue')
    // },
    // {
    //   path: '/files',
    //   name: 'files',
    //   component: () => import('../views/Files.vue')
    // },
    // {
    //   path: '/stats',
    //   name: 'stats',
    //   component: () => import('../views/Stats.vue')
    // },
    // {
    //   path: '/settings',
    //   name: 'settings',
    //   component: () => import('../views/Settings.vue')
    // }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  console.log('路由守卫 - 当前路由:', to.path)
  console.log('路由守卫 - token状态:', token ? '存在' : '不存在')
  
  // 如果需要登录但没有token，重定向到登录页
  if (to.meta.requiresAuth && !token) {
    console.log('需要登录权限，重定向到登录页')
    next({ name: 'login' })
  }
  // 如果已经有token且要去登录页，重定向到首页
  else if (to.name === 'login' && token) {
    console.log('已登录，重定向到首页')
    next({ name: 'home' })
  }
  // 其他情况正常跳转
  else {
    console.log('正常跳转到:', to.path)
    next()
  }
})

export default router
