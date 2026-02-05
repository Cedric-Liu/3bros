<template>
  <div class="page-container">
    <h1 class="page-title">反转三兄弟</h1>

    <!-- 大盘指数 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">大盘指数</span>
        <span class="update-time">{{ store.indicesUpdateTime }}</span>
      </div>
      <div class="indices-grid">
        <div
          v-for="index in store.indices"
          :key="index.code"
          class="index-card"
        >
          <div class="index-name">{{ index.name }}</div>
          <div class="index-price" :class="priceClass(index.pct_change)">
            {{ index.price.toFixed(2) }}
          </div>
          <div class="index-change" :class="priceClass(index.pct_change)">
            {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }}
            ({{ index.pct_change >= 0 ? '+' : '' }}{{ index.pct_change.toFixed(2) }}%)
          </div>
          <div v-if="index.action" class="index-signal">
            <el-tag :type="actionTagType(index.action)" size="small">
              {{ index.action }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 自选股信号概览 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">自选股信号</span>
        <router-link to="/watchlist" class="view-all">查看全部</router-link>
      </div>

      <el-skeleton :rows="3" animated v-if="store.watchlistLoading" />

      <div v-else-if="store.watchlist.length === 0" class="empty-tip">
        <el-empty description="暂无自选股">
          <router-link to="/watchlist">
            <el-button type="primary">添加自选股</el-button>
          </router-link>
        </el-empty>
      </div>

      <div v-else class="signal-summary">
        <div class="summary-cards">
          <div class="summary-card buy">
            <div class="summary-count">{{ store.buySignalsCount }}</div>
            <div class="summary-label">买入/加仓</div>
          </div>
          <div class="summary-card sell">
            <div class="summary-count">{{ store.sellSignalsCount }}</div>
            <div class="summary-label">卖出/减仓</div>
          </div>
          <div class="summary-card hold">
            <div class="summary-count">{{ store.watchlist.length - store.buySignalsCount - store.sellSignalsCount }}</div>
            <div class="summary-label">持有观望</div>
          </div>
        </div>

        <!-- 重点信号 -->
        <div v-if="importantSignals.length > 0" class="important-signals">
          <div
            v-for="stock in importantSignals"
            :key="stock.code"
            class="signal-item"
            :class="signalClass(stock.action)"
            @click="goToDetail(stock.code)"
          >
            <div class="stock-info">
              <span class="stock-name">{{ stock.name }}</span>
              <span class="stock-code">{{ stock.code }}</span>
            </div>
            <div class="signal-info">
              <el-tag :type="actionTagType(stock.action)" size="small">
                {{ stock.action }}
              </el-tag>
              <span class="signal-reason">{{ stock.action_reason }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="section">
      <div class="section-title">快捷入口</div>
      <div class="quick-links">
        <router-link to="/watchlist" class="quick-link">
          <el-icon :size="32"><Star /></el-icon>
          <span>自选股</span>
        </router-link>
        <router-link to="/top10" class="quick-link">
          <el-icon :size="32"><TrendCharts /></el-icon>
          <span>Top10推荐</span>
        </router-link>
        <router-link to="/etf" class="quick-link">
          <el-icon :size="32"><Coin /></el-icon>
          <span>自选ETF</span>
        </router-link>
        <router-link to="/settings" class="quick-link">
          <el-icon :size="32"><Setting /></el-icon>
          <span>设置</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { Star, TrendCharts, Coin, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const store = useAppStore()

// 重点信号（买入/卖出的股票）
const importantSignals = computed(() =>
  store.watchlist
    .filter(s => ['买入', '加仓', '卖出', '减仓'].includes(s.action))
    .slice(0, 5)
)

// 价格颜色类
function priceClass(pctChange: number) {
  if (pctChange > 0) return 'price-up'
  if (pctChange < 0) return 'price-down'
  return 'price-flat'
}

// 操作标签类型
function actionTagType(action: string) {
  if (['买入', '加仓'].includes(action)) return 'success'
  if (['卖出', '减仓'].includes(action)) return 'danger'
  return 'info'
}

// 信号卡片类
function signalClass(action: string) {
  if (['买入', '加仓'].includes(action)) return 'signal-buy'
  if (['卖出', '减仓'].includes(action)) return 'signal-sell'
  return 'signal-hold'
}

// 跳转详情
function goToDetail(code: string) {
  router.push(`/stock/${code}`)
}

onMounted(() => {
  store.loadIndices()
  store.loadWatchlist()
})
</script>

<style scoped>
.section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.update-time {
  font-size: 12px;
  color: #999;
}

.view-all {
  font-size: 14px;
  color: #409eff;
  text-decoration: none;
}

/* 指数卡片 */
.indices-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.index-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  text-align: center;
}

.index-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.index-price {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.index-change {
  font-size: 13px;
  margin-bottom: 8px;
}

.index-signal {
  margin-top: 4px;
}

/* 信号概览 */
.summary-cards {
  display: flex;
  gap: 12px;
  margin-bottom: 15px;
}

.summary-card {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  text-align: center;
}

.summary-card.buy {
  background: linear-gradient(135deg, #67c23a20 0%, #67c23a10 100%);
  border: 1px solid #67c23a30;
}

.summary-card.sell {
  background: linear-gradient(135deg, #f56c6c20 0%, #f56c6c10 100%);
  border: 1px solid #f56c6c30;
}

.summary-card.hold {
  background: linear-gradient(135deg, #90939920 0%, #90939910 100%);
  border: 1px solid #90939930;
}

.summary-count {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.summary-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 重点信号 */
.signal-item {
  background: #fff;
  border-radius: 12px;
  padding: 12px 15px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.stock-code {
  font-size: 12px;
  color: #999;
}

.signal-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.signal-reason {
  font-size: 12px;
  color: #666;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 快捷入口 */
.quick-links {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.quick-link {
  background: #fff;
  border-radius: 12px;
  padding: 20px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: #333;
}

.quick-link span {
  margin-top: 8px;
  font-size: 13px;
}

.quick-link:hover {
  background: #f5f7fa;
}

.empty-tip {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
}
</style>
