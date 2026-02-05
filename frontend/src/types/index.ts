// 股票相关类型
export interface Stock {
  code: string
  name: string
}

export interface StockInWatchlist extends Stock {
  added_at?: string
  sort_order?: number
  notes?: string
}

export interface StockWithQuote extends Stock {
  price?: number
  prev_close?: number
  change?: number
  pct_change?: number
  volume?: number
  amount?: number
}

export interface StockSignalSummary extends Stock {
  current_price: number
  action: string
  action_reason: string
  risk_level: string
  volume_status: string
  volume_ratio: number
  macd_cross: string
  patterns: string[]
}

// 支撑/压力位
export interface SupportResistanceLine {
  price: number
  name: string
  type: 'strong' | 'medium' | 'weak'
  ref_date: string
  days_ago: number
  ref_open: number
  ref_close: number
  calculation: string
  vs_current: string
}

// 均线状态
export interface MAStatus {
  value: number
  above: boolean
  diff_pct: number
}

// 形态
export interface PatternInfo {
  name: string
  type: string
  strength: string
  desc: string
  position_advice?: string
}

// 完整分析结果
export interface StrategyAnalysis {
  code: string
  name: string
  current_price: number
  volume_status: string
  volume_ratio: number
  price_new_high: boolean
  price_new_low: boolean
  volume_price_conclusion: string
  support_lines: SupportResistanceLine[]
  resistance_lines: SupportResistanceLine[]
  near_support: boolean
  near_resistance: boolean
  support_break_status: string
  resistance_break_status: string
  upper_shadow_ratio: number
  upper_shadow_warning: boolean
  upper_shadow_detail: string
  ma_status: Record<string, MAStatus>
  ma_support: string
  macd_status: string
  macd_cross: string
  patterns: PatternInfo[]
  pattern_analysis: string[]
  trend_5d: string
  trend_10d: string
  trend_20d: string
  action: string
  action_reason: string
  action_detail: string
  bullish_factors: string[]
  bearish_factors: string[]
  risk_level: string
  position_advice: string
}

// 指数
export interface IndexInfo {
  code: string
  name: string
  price: number
  change: number
  pct_change: number
  volume?: number
  amount?: number
  action?: string
  action_reason?: string
  macd_cross?: string
}

// 今日信号
export interface TodaySignal {
  code: string
  name: string
  signal_type: string
  pattern_name: string
  strength: number
  price: number
  description?: string
  confirmations: string[]
  detected_at?: string
}

// 扫描结果
export interface ScanResult {
  code: string
  name: string
  price: number
  pct_change: number
  action: string
  action_reason: string
  patterns: string[]
  bullish_count: number
  bearish_count: number
  score: number
}

export interface ScanTaskInfo {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  total: number
  processed: number
  started_at?: string
  completed_at?: string
  results?: ScanResult[]
  buy_signals?: ScanResult[]
  sell_signals?: ScanResult[]
  error?: string
}

// ETF
export interface ETF {
  code: string
  name: string
}

export interface ETFInWatchlist extends ETF {
  added_at?: string
  sort_order?: number
  notes?: string
}

export interface PopularETF extends ETF {
  category: string
}

// 设置
export interface Settings {
  serverchan_key?: string
  serverchan_configured: boolean
  push_time?: string
}

// 买入信息
export interface BuyInfo {
  buy_price?: number
  buy_date?: string
  buy_quantity?: number
}

// 搜索结果
export interface SearchResult {
  code: string
  name: string
  type?: string
}

// K线数据点
export interface KlineDataPoint {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
}

// K线数据响应
export interface KlineResponse {
  code: string
  name: string
  klines: KlineDataPoint[]
  support_lines: SupportResistanceLine[]
  resistance_lines: SupportResistanceLine[]
}
