import axios from 'axios'
import type {
  StockInWatchlist,
  StockSignalSummary,
  StrategyAnalysis,
  IndexInfo,
  TodaySignal,
  ScanTaskInfo,
  ETFInWatchlist,
  PopularETF,
  Settings,
  BuyInfo,
  SearchResult,
  KlineResponse
} from '@/types'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ============ 股票API ============

export const stockApi = {
  // 获取自选股列表
  getWatchlist: (): Promise<{ items: StockInWatchlist[]; total: number }> =>
    api.get('/stocks/watchlist'),

  // 获取带信号的自选股
  getWatchlistWithSignals: (): Promise<{ items: StockSignalSummary[]; total: number }> =>
    api.get('/stocks/watchlist/signals'),

  // 添加自选股
  addToWatchlist: (code: string, name: string, notes?: string): Promise<{ success: boolean }> =>
    api.post('/stocks/watchlist', { code, name, notes }),

  // 删除自选股
  removeFromWatchlist: (code: string): Promise<{ success: boolean }> =>
    api.delete(`/stocks/watchlist/${code}`),

  // 获取股票详细分析
  getAnalysis: (code: string): Promise<StrategyAnalysis> =>
    api.get(`/stocks/${code}/analysis`),

  // 更新买入信息
  updateBuyInfo: (code: string, info: BuyInfo): Promise<{ success: boolean }> =>
    api.put(`/stocks/${code}/buy-info`, info),

  // 获取买入信息
  getBuyInfo: (code: string): Promise<BuyInfo> =>
    api.get(`/stocks/${code}/buy-info`),

  // 搜索股票
  search: (keyword: string, includeEtf?: boolean): Promise<{ results: SearchResult[] }> =>
    api.get('/stocks/search', { params: { keyword, include_etf: includeEtf } }),

  // 获取K线数据
  getKlines: (code: string, days?: number): Promise<KlineResponse> =>
    api.get(`/stocks/${code}/klines`, { params: { days: days || 60 } })
}

// ============ 市场API ============

export const marketApi = {
  // 获取大盘指数
  getIndices: (): Promise<{ indices: IndexInfo[]; update_time: string }> =>
    api.get('/market/indices'),

  // 获取今日信号
  getTodaySignals: (): Promise<{ buy_signals: TodaySignal[]; sell_signals: TodaySignal[]; total: number }> =>
    api.get('/market/signals/today'),

  // 开始市场扫描
  startScan: (limit?: number): Promise<ScanTaskInfo> =>
    api.post('/market/scan', { limit }),

  // 获取扫描结果
  getScanResult: (taskId: string): Promise<ScanTaskInfo> =>
    api.get(`/market/scan/${taskId}`)
}

// ============ ETF API ============

export const etfApi = {
  // 获取ETF自选列表
  getWatchlist: (): Promise<{ items: ETFInWatchlist[]; total: number }> =>
    api.get('/etfs/watchlist'),

  // 添加ETF到自选
  addToWatchlist: (code: string, name: string, notes?: string): Promise<{ success: boolean }> =>
    api.post('/etfs/watchlist', { code, name, notes }),

  // 从自选中删除ETF
  removeFromWatchlist: (code: string): Promise<{ success: boolean }> =>
    api.delete(`/etfs/watchlist/${code}`),

  // 获取热门ETF
  getPopular: (): Promise<{ items: PopularETF[] }> =>
    api.get('/etfs/popular'),

  // 搜索ETF
  search: (keyword: string): Promise<{ results: SearchResult[] }> =>
    api.get('/etfs/search', { params: { keyword } }),

  // 获取ETF分析
  getAnalysis: (code: string): Promise<StrategyAnalysis> =>
    api.get(`/etfs/${code}/analysis`)
}

// ============ 设置API ============

export const settingsApi = {
  // 获取设置
  get: (): Promise<Settings> =>
    api.get('/settings'),

  // 更新设置
  update: (settings: { serverchan_key?: string; push_time?: string }): Promise<{ success: boolean }> =>
    api.put('/settings', settings),

  // 测试推送
  testNotify: (): Promise<{ success: boolean; message: string }> =>
    api.post('/settings/notify/test')
}

export default api
