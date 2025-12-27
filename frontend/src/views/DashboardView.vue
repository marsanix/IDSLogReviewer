<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { AlertOctagon, AlertTriangle, Activity } from 'lucide-vue-next'
import axios from 'axios'
import Chart from 'chart.js/auto'

const stats = ref({
  severity_high: 0,
  severity_medium: 0,
  total_alerts: 0,
  top_signatures: {} // Key matched to backend: top_signatures
})

const API_URL = '/api'
const loading = ref(false)

let timeoutId: ReturnType<typeof setTimeout> | null = null
let isPolling = true

async function fetchStats() {
  if (!isPolling) return
  
  try {
    // Only show loading on initial fetch or manual refresh if we had one
    // For background polling usually we don't show loading bar to avoid distraction, 
    // but user asked for it "while load data". 
    // To be less distracting, maybe only if it takes time? 
    // Let's just follow request: "loading data" -> show bar.
    // However, constant flashing every 2 seconds might be annoying.
    // Let's show it.
    if (!timeoutId) loading.value = true 
    
    const res = await axios.get(`${API_URL}/stats`)
    stats.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
    // Schedule next fetch only after current one completes
    if (isPolling) {
      timeoutId = setTimeout(fetchStats, 2000)
    }
  }
}

onMounted(() => {
  fetchStats()
})

onUnmounted(() => {
  isPolling = false
  if (timeoutId) clearTimeout(timeoutId)
})
</script>

<template>
  <div class="space-y-6">
    <div v-if="loading" class="h-1 w-full bg-secondary overflow-hidden fixed top-16 left-0 z-50">
      <div class="h-full bg-primary animate-progress origin-left-right"></div>
    </div>
    
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card class="border-l-4 border-l-red-500">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">High Severity</CardTitle>
          <AlertOctagon class="h-4 w-4 text-red-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-red-600">{{ stats.severity_high }}</div>
          <p class="text-xs text-muted-foreground">Critical Threats</p>
        </CardContent>
      </Card>

      <Card class="border-l-4 border-l-yellow-500">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Medium Severity</CardTitle>
          <AlertTriangle class="h-4 w-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-yellow-600">{{ stats.severity_medium }}</div>
          <p class="text-xs text-muted-foreground">Warnings</p>
        </CardContent>
      </Card>

      <Card class="border-l-4 border-l-blue-500">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Total Events</CardTitle>
          <Activity class="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.total_alerts }}</div>
          <p class="text-xs text-muted-foreground">All Detections</p>
        </CardContent>
      </Card>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
       <!-- Top Threats -->
       <Card>
        <CardHeader>
          <CardTitle>Top Threats</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-4">
            <div v-for="(count, threat) in stats.top_signatures" :key="threat" class="flex items-center">
              <div class="w-full flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium truncate w-64" :title="String(threat)">{{ threat }}</span>
                  <span class="text-sm text-muted-foreground">{{ count }}</span>
                </div>
                <!-- Progress bar simulation -->
                <div class="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div class="h-full bg-primary" :style="{ width: `${Math.min((Number(count) / stats.total_alerts) * 100, 100)}%` }"></div>
                </div>
              </div>
            </div>
             <div v-if="stats.top_signatures && Object.keys(stats.top_signatures).length === 0" class="text-sm text-muted-foreground">
              No threats detected yet.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
