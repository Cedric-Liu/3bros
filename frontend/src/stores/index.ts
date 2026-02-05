import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { stockApi, marketApi, etfApi, settingsApi } from '@/api'
import type {
  StockSignalSummary,
  StrategyAnalysis,
  IndexInfo,
  TodaySignal,
  ScanTaskInfo,
  ETFInWatchlist,
  PopularETF,
  Settings
} from '@/types'

// 主Store
export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 自选股
  const watchlist = ref<StockSignalSummary[]>([])
  const watchlistLoading = ref(false)

  // 指数
  const indices = ref<IndexInfo[]>([])
  const indicesUpdateTime = ref('')

  // 今日信号
  const todayBuySignals = ref<TodaySignal[]>([])
  const todaySellSignals = ref<TodaySignal[]>([])

  // 扫描任务
  const scanTask = ref<ScanTaskInfo | null>(null)
  const scanPolling = ref(false)

  // ETF
  const etfWatchlist = ref<ETFInWatchlist[]>([])
  const popularEtfs = ref<PopularETF[]>([])

  // 设置
  const settings = ref<Settings>({
    serverchan_configured: false
  })

  // 当前分析详情
  const currentAnalysis = ref<StrategyAnalysis | null>(null)

  // ============ Actions ============

  // 加载自选股
  async function loadWatchlist() {
    try {
      watchlistLoading.value = true
      const res = await stockApi.getWatchlistWithSignals()
      watchlist.value = res.items
    } catch (e: any) {
      error.value = e.message
    } finally {
      watchlistLoading.value = false
    }
  }

  // 添加自选股
  async function addToWatchlist(code: string, name: string) {
    try {
      await stockApi.addToWatchlist(code, name)
      await loadWatchlist()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  // 删除自选股
  async function removeFromWatchlist(code: string) {
    try {
      await stockApi.removeFromWatchlist(code)
      await loadWatchlist()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  // 加载大盘指数
  async function loadIndices() {
    try {
      const res = await marketApi.getIndices()
      indices.value = res.indices
      indicesUpdateTime.value = res.update_time
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 加载今日信号
  async function loadTodaySignals() {
    try {
      const res = await marketApi.getTodaySignals()
      todayBuySignals.value = res.buy_signals
      todaySellSignals.value = res.sell_signals
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 开始扫描
  async function startScan(limit = 200) {
    try {
      scanTask.value = await marketApi.startScan(limit)
      pollScanStatus()
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 轮询扫描状态
  async function pollScanStatus() {
    if (!scanTask.value || scanPolling.value) return

    scanPolling.value = true

    while (scanTask.value && ['pending', 'running'].includes(scanTask.value.status)) {
      try {
        scanTask.value = await marketApi.getScanResult(scanTask.value.task_id)
        await new Promise(resolve => setTimeout(resolve, 1000))
      } catch (e) {
        break
      }
    }

    scanPolling.value = false
  }

  // 加载股票分析
  async function loadAnalysis(code: string, type: string = 'stock') {
    try {
      loading.value = true
      if (type === 'etf') {
        currentAnalysis.value = await etfApi.getAnalysis(code)
      } else {
        currentAnalysis.value = await stockApi.getAnalysis(code)
      }
    } catch (e: any) {
      error.value = e.message
      currentAnalysis.value = null
    } finally {
      loading.value = false
    }
  }

  // 加载ETF自选
  async function loadEtfWatchlist() {
    try {
      const res = await etfApi.getWatchlist()
      etfWatchlist.value = res.items
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 加载热门ETF
  async function loadPopularEtfs() {
    try {
      const res = await etfApi.getPopular()
      popularEtfs.value = res.items
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 添加ETF到自选
  async function addEtfToWatchlist(code: string, name: string) {
    try {
      await etfApi.addToWatchlist(code, name)
      await loadEtfWatchlist()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  // 从自选删除ETF
  async function removeEtfFromWatchlist(code: string) {
    try {
      await etfApi.removeFromWatchlist(code)
      await loadEtfWatchlist()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  // 加载设置
  async function loadSettings() {
    try {
      settings.value = await settingsApi.get()
    } catch (e: any) {
      error.value = e.message
    }
  }

  // 更新设置
  async function updateSettings(data: { serverchan_key?: string; push_time?: string }) {
    try {
      await settingsApi.update(data)
      await loadSettings()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  // 测试推送
  async function testNotify() {
    try {
      const res = await settingsApi.testNotify()
      return res
    } catch (e: any) {
      return { success: false, message: e.message }
    }
  }

  // 计算属性
  const buySignalsCount = computed(() =>
    watchlist.value.filter(s => ['买入', '加仓'].includes(s.action)).length
  )

  const sellSignalsCount = computed(() =>
    watchlist.value.filter(s => ['卖出', '减仓'].includes(s.action)).length
  )

  return {
    // 状态
    loading,
    error,
    watchlist,
    watchlistLoading,
    indices,
    indicesUpdateTime,
    todayBuySignals,
    todaySellSignals,
    scanTask,
    scanPolling,
    etfWatchlist,
    popularEtfs,
    settings,
    currentAnalysis,

    // 计算属性
    buySignalsCount,
    sellSignalsCount,

    // Actions
    loadWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    loadIndices,
    loadTodaySignals,
    startScan,
    loadAnalysis,
    loadEtfWatchlist,
    loadPopularEtfs,
    addEtfToWatchlist,
    removeEtfFromWatchlist,
    loadSettings,
    updateSettings,
    testNotify
  }
})
