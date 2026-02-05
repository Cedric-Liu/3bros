<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">自选股</h1>
      <el-button type="primary" :icon="Plus" circle @click="showAddDialog = true" />
    </div>

    <!-- 搜索添加对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加自选股"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="searchKeyword"
        placeholder="输入股票代码或名称"
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
      />
      <div class="search-results">
        <div
          v-for="item in searchResults"
          :key="item.code"
          class="search-item"
          @click="handleAdd(item)"
        >
          <span class="item-name">{{ item.name }}</span>
          <span class="item-code">{{ item.code }}</span>
        </div>
        <el-empty v-if="searchKeyword && searchResults.length === 0" description="无搜索结果" />
      </div>
    </el-dialog>

    <!-- 股票列表 -->
    <el-skeleton :rows="5" animated v-if="store.watchlistLoading" />

    <div v-else-if="store.watchlist.length === 0" class="empty-tip">
      <el-empty description="暂无自选股，点击右上角添加" />
    </div>

    <div v-else class="stock-list">
      <div
        v-for="stock in store.watchlist"
        :key="stock.code"
        class="stock-card"
        :class="signalClass(stock.action)"
        @click="goToDetail(stock.code)"
      >
        <div class="stock-main">
          <div class="stock-left">
            <div class="stock-name">{{ stock.name }}</div>
            <div class="stock-code">{{ stock.code }}</div>
          </div>
          <div class="stock-right">
            <div class="stock-price" :class="priceClass(stock.current_price)">
              {{ stock.current_price.toFixed(2) }}
            </div>
          </div>
        </div>

        <div class="stock-signal">
          <el-tag :type="actionTagType(stock.action)" size="small">
            {{ stock.action }}
          </el-tag>
          <span class="signal-reason">{{ stock.action_reason }}</span>
          <span class="volume-info">
            {{ stock.volume_status }} {{ stock.volume_ratio.toFixed(2) }}倍
          </span>
        </div>

        <div class="stock-patterns" v-if="stock.patterns.length > 0">
          <el-tag
            v-for="pattern in stock.patterns"
            :key="pattern"
            size="small"
            type="warning"
            class="pattern-tag"
          >
            {{ pattern }}
          </el-tag>
        </div>

        <div class="stock-chart" @click.stop>
          <KLineChart :code="stock.code" height="180px" />
        </div>

        <div class="stock-actions" @click.stop>
          <el-button
            type="danger"
            size="small"
            text
            :icon="Delete"
            @click="handleRemove(stock.code)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 刷新按钮 -->
    <div class="refresh-btn">
      <el-button
        type="primary"
        :icon="Refresh"
        circle
        size="large"
        @click="handleRefresh"
        :loading="store.watchlistLoading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { stockApi } from '@/api'
import { Plus, Search, Delete, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { SearchResult } from '@/types'
import KLineChart from '@/components/KLineChart.vue'

const router = useRouter()
const store = useAppStore()

const showAddDialog = ref(false)
const searchKeyword = ref('')
const searchResults = ref<SearchResult[]>([])
let searchTimer: number | null = null

// 搜索股票
async function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)

  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }

  searchTimer = window.setTimeout(async () => {
    try {
      const res = await stockApi.search(searchKeyword.value)
      searchResults.value = res.results
    } catch (e) {
      console.error(e)
    }
  }, 300)
}

// 添加股票
async function handleAdd(item: SearchResult) {
  const success = await store.addToWatchlist(item.code, item.name)
  if (success) {
    ElMessage.success(`已添加 ${item.name}`)
    showAddDialog.value = false
    searchKeyword.value = ''
    searchResults.value = []
  } else {
    ElMessage.error('添加失败')
  }
}

// 删除股票
async function handleRemove(code: string) {
  try {
    await ElMessageBox.confirm('确定要删除该自选股吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const success = await store.removeFromWatchlist(code)
    if (success) {
      ElMessage.success('已删除')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 取消
  }
}

// 刷新
function handleRefresh() {
  store.loadWatchlist()
}

// 跳转详情
function goToDetail(code: string) {
  router.push(`/stock/${code}`)
}

// 价格颜色
function priceClass(price: number) {
  return 'price-flat' // 需要昨收价来判断
}

// 信号卡片类
function signalClass(action: string) {
  if (['买入', '加仓'].includes(action)) return 'signal-buy'
  if (['卖出', '减仓'].includes(action)) return 'signal-sell'
  return 'signal-hold'
}

// 操作标签类型
function actionTagType(action: string) {
  if (['买入', '加仓'].includes(action)) return 'success'
  if (['卖出', '减仓'].includes(action)) return 'danger'
  return 'info'
}

onMounted(() => {
  store.loadWatchlist()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.search-results {
  margin-top: 15px;
  max-height: 300px;
  overflow-y: auto;
}

.search-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.search-item:hover {
  background: #f5f7fa;
}

.item-name {
  font-size: 15px;
  color: #333;
}

.item-code {
  font-size: 13px;
  color: #999;
}

.stock-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stock-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  cursor: pointer;
}

.stock-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.stock-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.stock-code {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.stock-price {
  font-size: 20px;
  font-weight: 600;
}

.stock-signal {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.signal-reason {
  font-size: 13px;
  color: #666;
  flex: 1;
}

.volume-info {
  font-size: 12px;
  color: #999;
}

.stock-patterns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.pattern-tag {
  font-size: 11px;
}

.stock-actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
  margin-top: 8px;
}

.refresh-btn {
  position: fixed;
  right: 20px;
  bottom: 80px;
}

.empty-tip {
  background: #fff;
  border-radius: 12px;
  padding: 40px 20px;
}

.stock-chart {
  margin: 10px 0;
  border-radius: 8px;
  overflow: hidden;
}
</style>
