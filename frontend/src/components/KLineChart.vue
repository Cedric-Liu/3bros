<template>
  <div class="kline-chart-container" :style="{ height }">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else-if="error" class="chart-error">
      <span>{{ error }}</span>
    </div>
    <v-chart v-else class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { stockApi } from '@/api'
import type { KlineResponse, KlineDataPoint, SupportResistanceLine } from '@/types'

// Register ECharts components
use([
  CanvasRenderer,
  CandlestickChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent
])

const props = defineProps<{
  code: string
  height?: string
}>()

const height = computed(() => props.height || '220px')
const loading = ref(true)
const error = ref('')
const klineData = ref<KlineResponse | null>(null)

async function loadData() {
  if (!props.code) return

  loading.value = true
  error.value = ''

  try {
    klineData.value = await stockApi.getKlines(props.code)
  } catch (e: any) {
    error.value = e.message || '加载K线数据失败'
  } finally {
    loading.value = false
  }
}

// Build chart option
const chartOption = computed(() => {
  if (!klineData.value || !klineData.value.klines.length) {
    return {}
  }

  const klines = klineData.value.klines
  const dates = klines.map(k => k.date)

  // OHLC data for candlestick: [open, close, low, high]
  const ohlcData = klines.map(k => [k.open, k.close, k.low, k.high])

  // Volume data
  const volumeData = klines.map((k, idx) => ({
    value: k.volume,
    itemStyle: {
      color: k.close >= k.open ? '#ef5350' : '#26a69a'
    }
  }))

  // Support/resistance lines as markLine data
  const markLineData: any[] = []

  // 支撑线 - 绿色，在当前价格下方
  klineData.value.support_lines.forEach((line: SupportResistanceLine) => {
    const isStrong = line.type === 'strong'
    markLineData.push({
      yAxis: line.price,
      name: line.name,
      lineStyle: {
        color: '#00C853',  // 绿色
        type: isStrong ? 'solid' : 'dashed',
        width: isStrong ? 3 : 2
      },
      label: {
        show: true,
        formatter: `${line.name} ${line.price.toFixed(2)}`,
        position: 'insideEndTop',
        color: '#fff',
        backgroundColor: '#00C853',
        padding: [2, 6],
        borderRadius: 2,
        fontSize: 11,
        fontWeight: 'bold'
      }
    })
  })

  // 压力线 - 红色/橙色，在当前价格上方
  klineData.value.resistance_lines.forEach((line: SupportResistanceLine) => {
    const isStrong = line.type === 'strong'
    markLineData.push({
      yAxis: line.price,
      name: line.name,
      lineStyle: {
        color: '#FF5722',  // 橙红色
        type: isStrong ? 'solid' : 'dashed',
        width: isStrong ? 3 : 2
      },
      label: {
        show: true,
        formatter: `${line.name} ${line.price.toFixed(2)}`,
        position: 'insideEndBottom',
        color: '#fff',
        backgroundColor: '#FF5722',
        padding: [2, 6],
        borderRadius: 2,
        fontSize: 11,
        fontWeight: 'bold'
      }
    })
  })

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any[]) => {
        const k = params.find(p => p.seriesType === 'candlestick')
        if (!k) return ''
        const [open, close, low, high] = k.data
        return `${k.name}<br/>
          开: ${open.toFixed(2)}<br/>
          收: ${close.toFixed(2)}<br/>
          高: ${high.toFixed(2)}<br/>
          低: ${low.toFixed(2)}`
      }
    },
    grid: [
      { left: '5%', right: '5%', top: '5%', height: '65%' },
      { left: '5%', right: '5%', top: '75%', height: '15%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#e0e0e0' } }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLabel: { fontSize: 10, color: '#999' },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#e0e0e0' } }
      }
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitLine: { lineStyle: { color: '#f0f0f0' } },
        axisLabel: { fontSize: 10, color: '#999' }
      },
      {
        type: 'value',
        gridIndex: 1,
        scale: true,
        splitLine: { show: false },
        axisLabel: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100,
        height: 15,
        bottom: 0
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlcData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
        },
        markLine: markLineData.length > 0 ? {
          symbol: 'none',
          data: markLineData
        } : undefined
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumeData,
        xAxisIndex: 1,
        yAxisIndex: 1
      }
    ]
  }
})

watch(() => props.code, () => {
  loadData()
}, { immediate: false })

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.kline-chart-container {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.chart {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.chart-error {
  color: #999;
  font-size: 13px;
}
</style>
