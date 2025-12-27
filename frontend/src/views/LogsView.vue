<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import axios from 'axios'
import { RefreshCcw, ChevronLeft, ChevronRight, X } from 'lucide-vue-next'

interface LogEntry {
  id: number
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
const filterSearch = ref('')
const filterSignatureSelect = ref('')
const signatureOptions = ref<string[]>([])
const filterHigh = ref(false)
const startDate = ref('')
const endDate = ref('')
const filterSrcIp = ref('')
const filterDestIp = ref('')

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

// Pagination state
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const perPage = ref(20)

const API_URL = '/api'

async function fetchSignatures() {
  try {
    const res = await axios.get(`${API_URL}/signatures`)
    signatureOptions.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function fetchLogs(page = 1) {
  loading.value = true
  currentPage.value = page
  
  try {
    const params = new URLSearchParams()
    if (filterSearch.value) params.append('search', filterSearch.value)
    if (filterSignatureSelect.value) params.append('signature', filterSignatureSelect.value)
    if (filterHigh.value) params.append('severity', 'high')
    if (startDate.value) params.append('start_date', startDate.value)
    if (endDate.value) params.append('end_date', endDate.value)
    if (filterSrcIp.value) params.append('src_ip', filterSrcIp.value)
    if (filterDestIp.value) params.append('dest_ip', filterDestIp.value)
    
    params.append('page', page.toString())
    params.append('limit', perPage.value.toString())

    const res = await axios.get(`${API_URL}/history`, { params })
    
    // Handle new response structure
    if (res.data.meta) {
        logs.value = res.data.logs
        currentPage.value = res.data.meta.page
        totalPages.value = res.data.meta.total_pages
        totalItems.value = res.data.meta.total_items
    } else {
        // Fallback if backend not updated yet
        logs.value = res.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    fetchLogs(currentPage.value + 1)
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    fetchLogs(currentPage.value - 1)
  }
}

// Computed property for generating page numbers (sliding window)
import { computed } from 'vue'
const displayedPages = computed(() => {
  const delta = 2 // Number of pages to show on each side of current page
  const range = []
  const rangeWithDots = []
  const l = 1
  const r = totalPages.value

  for (let i = 1; i <= totalPages.value; i++) {
    if (i == 1 || i == totalPages.value || (i >= currentPage.value - delta && i <= currentPage.value + delta)) {
      range.push(i)
    }
  }

  let prev
  for (const i of range) {
    if (prev) {
      if (i - prev === 2) {
        rangeWithDots.push(prev + 1)
      } else if (i - prev !== 1) {
        rangeWithDots.push('...')
      }
    }
    rangeWithDots.push(i)
    prev = i
  }

  return rangeWithDots
})

onMounted(() => {
  fetchSignatures()
  fetchLogs()
})
</script>

<template>
  <Card class="h-full flex flex-col">
    <CardHeader class="flex flex-col gap-4 pb-2">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <CardTitle>Historical Logs</CardTitle>
        <Button variant="outline" size="icon" @click="fetchLogs(currentPage)" :disabled="loading">
          <RefreshCcw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
        </Button>
      </div>
      
      <!-- Filter Row 1: Signature & Search -->
      <div class="flex flex-wrap items-center gap-2">
        <select 
          v-model="filterSignatureSelect" 
          @change="fetchLogs(1)"
          class="h-9 w-full sm:w-48 px-3 rounded-md border border-input bg-background text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
          <option value="">All Signatures</option>
          <option v-for="sig in signatureOptions" :key="sig" :value="sig">
            {{ sig }}
          </option>
        </select>

        <input 
          v-model="filterSearch"
          type="text" 
          placeholder="Search..." 
          class="h-9 flex-1 min-w-[120px] px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          @keyup.enter="fetchLogs(1)"
        >
      </div>
      
      <!-- Filter Row 2: IP Filters -->
      <div class="flex flex-wrap items-center gap-2">
        <input 
          v-model="filterSrcIp"
          type="text" 
          placeholder="Src IP" 
          class="h-9 w-full sm:w-32 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          @keyup.enter="fetchLogs(1)"
        >
        <input 
          v-model="filterDestIp"
          type="text" 
          placeholder="Dest IP" 
          class="h-9 w-full sm:w-32 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          @keyup.enter="fetchLogs(1)"
        >
        
        <input 
          v-model="startDate"
          type="date"
          class="h-9 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          @change="fetchLogs(1)"
        >
        <span class="text-xs text-muted-foreground hidden sm:inline">-</span>
        <input 
          v-model="endDate"
          type="date"
          class="h-9 px-3 rounded-md border border-input bg-background/50 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          @change="fetchLogs(1)"
        >

        <label class="flex items-center gap-2 text-sm font-medium cursor-pointer whitespace-nowrap">
          <input type="checkbox" v-model="filterHigh" class="rounded border-gray-300 text-primary focus:ring-primary" @change="fetchLogs(1)">
          High Only
        </label>
      </div>
    </CardHeader>
    <div v-if="loading" class="h-1 w-full bg-secondary overflow-hidden">
      <div class="h-full bg-primary animate-progress origin-left-right"></div>
    </div>
    <CardContent class="flex-1 overflow-auto flex flex-col">
      <div class="relative w-full overflow-auto flex-1">
        <table class="w-full caption-bottom text-sm text-left">
          <thead class="[&_tr]:border-b">
            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Timestamp</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Type</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Signature</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Src IP</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Dest IP</th>
              <th class="h-12 px-4 align-middle font-medium text-muted-foreground">Severity</th>
            </tr>
          </thead>
          <tbody class="[&_tr:last-child]:border-0">
            <tr v-for="log in logs" :key="log.id" 
                class="border-b transition-colors hover:bg-muted/50 cursor-pointer"
                @click="openLogDetail(log)"
            >
              <td class="p-4 align-middle">{{ new Date(log.timestamp).toLocaleString() }}</td>
              <td class="p-4 align-middle capitalize">{{ log.event_type }}</td>
              <td class="p-4 align-middle font-medium">{{ log.signature }}</td>
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
              <td colspan="6" class="p-4 text-center text-muted-foreground">No logs found</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination Controls -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 border-t py-4 mt-2">
        <div class="flex flex-wrap items-center gap-2 text-sm text-muted-foreground justify-center sm:justify-start">
            <span>Show</span>
            <select 
              v-model="perPage" 
              @change="fetchLogs(1)"
              class="h-8 w-16 px-2 rounded-md border border-input bg-background text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <span>entries</span>
            <span class="hidden sm:inline ml-2"> | Showing {{ logs.length }} of {{ totalItems }} entries</span>
            <span class="sm:hidden text-xs">{{ logs.length }}/{{ totalItems }}</span>
        </div>
        
        <div class="flex items-center gap-1">
            <Button variant="outline" size="icon" class="h-8 w-8" @click="prevPage" :disabled="currentPage <= 1 || loading">
                <ChevronLeft class="h-4 w-4" />
            </Button>
            
            <!-- Page numbers - hidden on mobile -->
            <template v-for="page in displayedPages" :key="page">
              <span v-if="page === '...'" class="px-2 text-muted-foreground hidden sm:inline">...</span>
              <Button 
                v-else
                :variant="currentPage === page ? 'default' : 'outline'" 
                size="icon"
                class="h-8 w-8 hidden sm:inline-flex"
                @click="fetchLogs(Number(page))" 
                :disabled="loading"
              >
                {{ page }}
              </Button>
            </template>
            
            <!-- Mobile page indicator -->
            <span class="sm:hidden text-sm text-muted-foreground px-2">{{ currentPage }} / {{ totalPages }}</span>

            <Button variant="outline" size="icon" class="h-8 w-8" @click="nextPage" :disabled="currentPage >= totalPages || loading">
                <ChevronRight class="h-4 w-4" />
            </Button>
        </div>
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
              <label class="text-xs text-muted-foreground">ID</label>
              <p class="font-medium font-mono">{{ selectedLog.id }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Timestamp</label>
              <p class="font-medium">{{ new Date(selectedLog.timestamp).toLocaleString() }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground">Event Type</label>
              <p class="font-medium capitalize">{{ selectedLog.event_type }}</p>
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
              <p class="font-medium">{{ selectedLog.signature }}</p>
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
