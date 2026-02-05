<template>
  <div class="page-container">
    <h1 class="page-title">Top10 推荐</h1>

    <!-- 扫描控制 -->
    <div class="scan-control card">
      <div class="scan-info">
        <p v-if="!store.scanTask">点击扫描按钮，从活跃股票中筛选买入/卖出信号</p>
        <p v-else-if="store.scanTask.status === 'running'">
          正在扫描... {{ store.scanTask.processed }} / {{ store.scanTask.total }}
        </p>
        <p v-else-if="store.scanTask.status === 'completed'">
          扫描完成，共处理 {{ store.scanTask.total }} 只股票
        </p>
        <p v-else-if="store.scanTask.status === 'failed'">
          扫描失败: {{ store.scanTask.error }}
        </p>
      </div>

      <el-button
        type="primary"
        :loading="store.scanTask?.status === 'running'"
        @click="handleScan"
      >
        {{ store.scanTask?.status === 'running' ? '扫描中...' : '开始扫描' }}
      </el-button>
    </div>

    <!-- 进度条 -->
    <div v-if="store.scanTask?.status === 'running'" class="progress-bar">
      <el-progress
        :percentage="store.scanTask.progress"
        :stroke-width="8"
        :show-text="true"
      />
    </div>

    <!-- 扫描结果 -->
    <template v-if="store.scanTask?.status === 'completed'">
      <!-- 买入信号 -->
      <div class="section">
        <div class="section-title">
          <span>买入信号</span>
          <el-tag type="success" size="small">
            {{ store.scanTask.buy_signals?.length || 0 }}
          </el-tag>
        </div>

        <div v-if="store.scanTask.buy_signals?.length" class="result-list">
          <div
            v-for="(item, index) in store.scanTask.buy_signals"
            :key="item.code"
            class="result-card signal-buy"
            @click="goToDetail(item.code)"
          >
            <div class="rank">{{ index + 1 }}</div>
            <div class="result-main">
              <div class="result-info">
                <span class="result-name">{{ item.name }}</span>
                <span class="result-code">{{ item.code }}</span>
              </div>
              <div class="result-price">
                <span class="price">{{ item.price.toFixed(2) }}</span>
                <span class="change" :class="item.pct_change >= 0 ? 'price-up' : 'price-down'">
                  {{ item.pct_change >= 0 ? '+' : '' }}{{ item.pct_change.toFixed(2) }}%
                </span>
              </div>
            </div>
            <div class="result-detail">
              <el-tag type="success" size="small">{{ item.action }}</el-tag>
              <span class="reason">{{ item.action_reason }}</span>
            </div>
            <div class="result-patterns" v-if="item.patterns.length">
              <el-tag
                v-for="p in item.patterns"
                :key="p"
                size="small"
                type="warning"
              >
                {{ p }}
              </el-tag>
            </div>
            <div class="result-score">
              评分: +{{ item.score }}
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无买入信号" />
      </div>

    </template>

    <!-- 初始状态 -->
    <div v-if="!store.scanTask" class="empty-state card">
      <el-icon :size="64" color="#c0c4cc"><TrendCharts /></el-icon>
      <p>点击上方按钮开始扫描活跃股票</p>
      <p class="tip">扫描将从成交额最高的200只股票中筛选信号</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()
const store = useAppStore()

function handleScan() {
  store.startScan(200)
}

function goToDetail(code: string) {
  router.push(`/stock/${code}`)
}
</script>

<style scoped>
.scan-control {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.scan-info p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.progress-bar {
  margin-bottom: 20px;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  position: relative;
  cursor: pointer;
}

.rank {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background: #67c23a;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.rank.sell {
  background: #f56c6c;
}

.result-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.result-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.result-code {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.result-price {
  text-align: right;
}

.price {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.change {
  display: block;
  font-size: 13px;
}

.result-detail {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.reason {
  font-size: 13px;
  color: #666;
}

.result-patterns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.result-score {
  font-size: 12px;
  color: #409eff;
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state p {
  margin: 15px 0 0;
  color: #666;
}

.empty-state .tip {
  font-size: 13px;
  color: #999;
}
</style>
