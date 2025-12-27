<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ShieldAlert, LayoutDashboard, List, Settings, Activity, Menu, X, User, Users, ClipboardList } from 'lucide-vue-next'
import DashboardView from './views/DashboardView.vue'
import LogsView from './views/LogsView.vue'
import LiveLogsView from './views/LiveLogsView.vue'
import SettingsView from './views/SettingsView.vue'
import LoginView from './views/LoginView.vue'
import UsersView from './views/UsersView.vue'
import ActivityLogsView from './views/ActivityLogsView.vue'
import axios from 'axios'

interface UserInfo {
  id: number
  username: string
  role: string
}

const currentPage = ref('dashboard')
const sidebarOpen = ref(false)
const isAuthenticated = ref(false)
const currentUser = ref<UserInfo | null>(null)

// Setup axios interceptor to add auth token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses (token expired/invalid)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      handleLogout()
    }
    return Promise.reject(error)
  }
)

function navigateTo(page: string) {
  currentPage.value = page
  sidebarOpen.value = false
}

function handleLogin(user: UserInfo) {
  currentUser.value = user
  isAuthenticated.value = true
  currentPage.value = 'dashboard'
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  currentUser.value = null
  isAuthenticated.value = false
  currentPage.value = 'dashboard'
}

// Check for existing session on mount
onMounted(() => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  
  if (token && userStr) {
    try {
      currentUser.value = JSON.parse(userStr)
      isAuthenticated.value = true
    } catch {
      handleLogout()
    }
  }
})
</script>

<template>
  <!-- Login Page (unauthenticated) -->
  <LoginView v-if="!isAuthenticated" @login="handleLogin" />
  
  <!-- Main App (authenticated) -->
  <div v-else class="flex h-screen bg-background text-foreground">
    <!-- Mobile Menu Overlay -->
    <div 
      v-if="sidebarOpen" 
      class="fixed inset-0 bg-black/50 z-40 md:hidden"
      @click="sidebarOpen = false"
    ></div>
    
    <!-- Sidebar -->
    <aside 
      class="fixed md:static z-50 h-full w-64 border-r bg-card flex flex-col transform transition-transform duration-200 ease-in-out"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <div class="p-6 flex items-center gap-3 border-b">
        <ShieldAlert class="h-8 w-8 text-primary" />
        <h1 class="text-xl font-bold tracking-tight">Si-Devi</h1>
        <button class="ml-auto md:hidden" @click="sidebarOpen = false">
          <X class="h-5 w-5" />
        </button>
      </div>
      
      <nav class="flex-1 p-4 space-y-2">
        <a href="#" 
           class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
           :class="{ 'bg-accent text-accent-foreground': currentPage === 'dashboard' }"
           @click.prevent="navigateTo('dashboard')">
          <LayoutDashboard class="h-4 w-4" />
          Dashboard
        </a>
        <a href="#" 
           class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
           :class="{ 'bg-accent text-accent-foreground': currentPage === 'live' }"
           @click.prevent="navigateTo('live')">
          <Activity class="h-4 w-4" />
          Live Logs
        </a>
        <a href="#" 
           class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
           :class="{ 'bg-accent text-accent-foreground': currentPage === 'logs' }"
           @click.prevent="navigateTo('logs')">
          <List class="h-4 w-4" />
          History
        </a>
        <a href="#" 
           class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
           :class="{ 'bg-accent text-accent-foreground': currentPage === 'settings' }"
           @click.prevent="navigateTo('settings')">
          <Settings class="h-4 w-4" />
          Settings
        </a>
        
        <!-- Admin Only Section -->
        <template v-if="currentUser?.role === 'admin'">
          <div class="mt-4 pt-4 border-t">
            <span class="px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Admin</span>
          </div>
          <a href="#" 
             class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
             :class="{ 'bg-accent text-accent-foreground': currentPage === 'users' }"
             @click.prevent="navigateTo('users')">
            <Users class="h-4 w-4" />
            Users
          </a>
          <a href="#" 
             class="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
             :class="{ 'bg-accent text-accent-foreground': currentPage === 'activity' }"
             @click.prevent="navigateTo('activity')">
            <ClipboardList class="h-4 w-4" />
            Activity Logs
          </a>
        </template>
      </nav>

      <div class="p-4 border-t">
        <div class="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground">
          <User class="h-4 w-4" />
          <span class="truncate">{{ currentUser?.username }}</span>
          <span class="text-xs bg-secondary px-1.5 rounded capitalize">{{ currentUser?.role }}</span>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="h-16 border-b flex items-center justify-between px-4 sm:px-6 bg-card/50 backdrop-blur">
        <div class="flex items-center gap-4">
          <button class="md:hidden" @click="sidebarOpen = true">
            <Menu class="h-6 w-6" />
          </button>
          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <span class="hidden sm:inline">Overview</span>
            <span class="hidden sm:inline">/</span>
            <span class="text-foreground font-medium capitalize">{{ currentPage }}</span>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="px-2 py-1 rounded bg-secondary text-secondary-foreground text-xs font-mono hidden sm:block">HOST: LOCALHOST</span>
        </div>
      </header>

      <!-- View Area -->
      <div class="flex-1 overflow-auto p-4 sm:p-6">
        <DashboardView v-if="currentPage === 'dashboard'" />
        <LiveLogsView v-else-if="currentPage === 'live'" />
        <LogsView v-else-if="currentPage === 'logs'" />
        <SettingsView v-else-if="currentPage === 'settings'" @logout="handleLogout" />
        <UsersView v-else-if="currentPage === 'users'" />
        <ActivityLogsView v-else-if="currentPage === 'activity'" />
      </div>
    </main>
  </div>
</template>
