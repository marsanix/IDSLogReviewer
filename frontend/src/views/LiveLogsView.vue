<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Globe, RefreshCcw, X, ChevronRight } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import axios from 'axios'

interface LogEntry {
  timestamp: string
  event_type: string
  src_ip: string
  dest_ip: string
  severity: number
  signature: string
  payload?: string  // Full JSON from eve.json
}

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const clientFilter = ref('')
const srcIpFilter = ref('')
const destIpFilter = ref('')
const refreshInterval = ref('3000')

// Modal state
const showModal = ref(false)
const selectedLog = ref<LogEntry | null>(null)
const payloadExpanded = ref(false)

function openLogDetail(log: LogEntry) {
  selectedLog.value = log
  showModal.value = true
  payloadExpanded.value = false  // Reset on open
}

function closeModal() {
  showModal.value = false
  selectedLog.value = null
}

function formatPayload(payload: string): string {
  try {
    return JSON.stringify(JSON.parse(payload), null, 2)
  } catch {
    return payload
  }
}

let timeoutId: ReturnType<typeof setTimeout> | null = null
const isPolling = ref(true)
const isInitialLoad = ref(true)

const API_URL = '/api'

async function fetchLiveLogs() {
  if (!isPolling.value) return
  
  try {
    // Only show loading bar on initial load
    if (isInitialLoad.value) {
      loading.value = true
    }
    const res = await axios.get(`${API_URL}/logs`)
    logs.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
    isInitialLoad.value = false  // After first load, don't show progress bar
    // Schedule next fetch only after current one completes
    if (isPolling.value) {
      timeoutId = setTimeout(fetchLiveLogs, parseInt(refreshInterval.value))
    }
  }
}

function reload() {
  if (timeoutId) clearTimeout(timeoutId)
  fetchLiveLogs()
}

// Client-side filtered logs
const displayedLogs = computed(() => {
  let result = logs.value
  
  // General text filter
  if (clientFilter.value) {
    const search = clientFilter.value.toLowerCase()
    result = result.filter(log => 
      (log.signature || '').toLowerCase().includes(search) ||
      log.src_ip.includes(search) ||
      log.dest_ip.includes(search) ||
      log.event_type.toLowerCase().includes(search)
    )
  }
  
  // Specific IP filters
  if (srcIpFilter.value) {
    result = result.filter(log => log.src_ip.includes(srcIpFilter.value))
  }
  if (destIpFilter.value) {
    result = result.filter(log => log.dest_ip.includes(destIpFilter.value))
  }
  
  return result
})

watch(refreshInterval, () => {
    // Reset timer on interval change
    if (timeoutId) clearTimeout(timeoutId)
    fetchLiveLogs()
})

onMounted(() => {
  fetchLiveLogs()
})

onUnmounted(() => {
  isPolling.value = false
  if (timeoutId) clearTimeout(timeoutId)
})
</script>

<template>
  <Card class="h-full flex flex-col">
    <CardHeader class="flex flex-col gap-4 pb-2">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <CardTitle class="flex items-center gap-2">
          <span class="relative flex h-3 w-3 mr-1">
            <span 
              v-if="isPolling"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"
            ></span>
            <span 
              class="relative inline-flex rounded-full h-3 w-3"
              :class="isPolling ? 'bg-green-500' : 'bg-gray-400'"
            ></span>
          </span>
          Live Logs
          <span v-if="!isPolling" class="text-xs text-muted-foreground font-normal">(Paused)</span>
        </CardTitle>
        
        <div class="flex items-center gap-2">
           <select 
            v-model="refreshInterval" 
            class="h-9 w-20 px-2 rounded-md border border-input bg-background text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="1000">1s</option>
            <option value="3000">3s</option>
            <option value="5000">5s</option>
            <option value="10000">10s</option>
          </select>

          <Button variant="outline" size="icon" @click="reload" :disabled="loading">
            <RefreshCcw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
          </Button>

          <Globe class="h-4 w-4 text-muted-foreground hidden sm:block" />
        </div>
      </div>
      
      <!-- Filter Row -->
      <div class="flex flex-wrap items-center gap-2">
         <input 
          v-model="clientFilter"
          type="text" 
          placeholder="Filter..." 
          class="h-9 flex-1 min-w-[100px] px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
        <input 
          v-model="srcIpFilter"
          type="text" 
          placeholder="Src IP" 
          class="h-9 w-full sm:w-28 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
        <input 
          v-model="destIpFilter"
          type="text" 
          placeholder="Dest IP" 
          class="h-9 w-full sm:w-28 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
      </div>
    </CardHeader>
    <div v-if="loading" class="h-1 w-full bg-secondary overflow-hidden">
      <div class="h-full bg-primary animate-progress origin-left-right"></div>
    </div>
    <CardContent class="flex-1 overflow-auto">
      <div class="relative w-full overflow-auto">
        <table class="w-full caption-bottom text-sm text-left">
          <thead class="[&_tr]:border-b">
            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Time</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Type</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Signature</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Src IP</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Dest IP</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Severity</th>
            </tr>
          </thead>
          <tbody class="[&_tr:last-child]:border-0">
            <tr v-for="(log, index) in displayedLogs" :key="index" 
                class="border-b transition-colors hover:bg-muted/50 animate-in fade-in slide-in-from-top-1 duration-300 cursor-pointer"
                @click="openLogDetail(log)"
            >
              <td class="p-4 align-middle whitespace-nowrap">{{ new Date(log.timestamp).toLocaleString() }}</td>
              <td class="p-4 align-middle capitalize">{{ log.event_type }}</td>
              <td class="p-4 align-middle font-medium">{{ log.signature || 'N/A' }}</td>
              <td class="p-4 align-middle">{{ log.src_ip }}</td>
              <td class="p-4 align-middle">{{ log.dest_ip }}</td>
              <td class="p-4 align-middle">
                <span 
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  :class="log.severity === 1 ? 'bg-red-500/10 text-red-500' : 'bg-yellow-500/10 text-yellow-500'"
                >
                  Level {{ log.severity }}
                </span>
              </td>
            </tr>
            <tr v-if="logs.length === 0 && !loading">
              <td colspan="6" class="p-4 text-center text-muted-foreground">Waiting for new logs...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </CardContent>
  </Card>
  
  <!-- Log Detail Modal -->
  <Teleport to="body">
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black/50" @click="closeModal"></div>
      <div class="relative z-50 w-full max-w-2xl max-h-[90vh] m-4 bg-card rounded-lg shadow-lg border overflow-hidden">
        <div class="flex items-center justify-between p-4 border-b">
          <h2 class="text-lg font-semibold">Log Details</h2>
          <button @click="closeModal" class="p-1 rounded-md hover:bg-accent">
            <X class="h-5 w-5" />
          </button>
        </div>
        <div class="p-4 overflow-auto max-h-[calc(90vh-120px)] space-y-4" v-if="selectedLog">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-muted-foreground">Timestamp</label>
              <p class="font-medium">{{ new Date(selectedLog.timestamp).toLocaleString() }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Event Type</label>
              <p class="font-medium capitalize">{{ selectedLog.event_type }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Source IP</label>
              <p class="font-medium font-mono">{{ selectedLog.src_ip }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Destination IP</label>
              <p class="font-medium font-mono">{{ selectedLog.dest_ip }}</p>
            </div>
            <div class="sm:col-span-2">
              <label class="text-xs text-muted-foreground">Signature</label>
              <p class="font-medium">{{ selectedLog.signature || 'N/A' }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Severity</label>
              <span 
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
                :class="selectedLog.severity === 1 ? 'bg-red-500/10 text-red-500' : 'bg-yellow-500/10 text-yellow-500'"
              >
                Level {{ selectedLog.severity }}
              </span>
            </div>
          </div>
          
          <!-- Full Payload Section (Collapsible) -->
          <div v-if="selectedLog.payload" class="mt-4">
            <button 
              @click="payloadExpanded = !payloadExpanded"
              class="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full text-left"
            >
              <ChevronRight class="h-4 w-4 transition-transform" :class="{ 'rotate-90': payloadExpanded }" />
              <span>Full Payload (from eve.json)</span>
            </button>
            <div v-if="payloadExpanded" class="mt-2">
              <pre class="bg-secondary/50 p-4 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all max-h-64 overflow-y-auto">{{ formatPayload(selectedLog.payload) }}</pre>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 p-4 border-t">
          <button @click="closeModal" class="px-4 py-2 text-sm font-medium rounded-md bg-secondary hover:bg-secondary/80">
            Close
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
