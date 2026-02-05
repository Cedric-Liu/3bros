<template>
  <div class="page-container">
    <!-- 加载状态 -->
    <div v-if="store.loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="!store.currentAnalysis" class="error-state">
      <el-empty description="加载失败，请返回重试" />
      <el-button @click="router.back()">返回</el-button>
    </div>

    <!-- 详情内容 -->
    <template v-else>
      <div class="detail-header">
        <el-button :icon="ArrowLeft" text @click="router.back()">返回</el-button>
      </div>

      <!-- 基本信息 -->
      <div class="card stock-header">
        <div class="stock-title">
          <span class="stock-name">{{ analysis.name }}</span>
          <span class="stock-code">{{ analysis.code }}</span>
        </div>
        <div class="stock-price">
          {{ analysis.current_price.toFixed(2) }}
        </div>
        <div class="action-row">
          <el-tag :type="actionTagType(analysis.action)" size="large">
            {{ analysis.action }}
          </el-tag>
          <span class="action-reason">{{ analysis.action_reason }}</span>
        </div>
        <div class="position-advice">
          <el-icon><InfoFilled /></el-icon>
          {{ analysis.position_advice }}
        </div>
      </div>

      <!-- K线图 -->
      <div class="card kline-section">
        <div class="section-title">K线走势</div>
        <KLineChart :code="analysis.code" height="300px" />
      </div>

      <!-- 量价分析 -->
      <div class="card section">
        <div class="section-title">量价分析</div>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">量能状态</span>
            <span class="value">{{ analysis.volume_status }}</span>
          </div>
          <div class="info-item">
            <span class="label">量比</span>
            <span class="value">{{ analysis.volume_ratio.toFixed(2) }}</span>
          </div>
          <div class="info-item" v-if="analysis.price_new_high">
            <span class="label">创新高</span>
            <span class="value price-up">是</span>
          </div>
          <div class="info-item" v-if="analysis.price_new_low">
            <span class="label">创新低</span>
            <span class="value price-down">是</span>
          </div>
        </div>
        <div class="conclusion">{{ analysis.volume_price_conclusion }}</div>
      </div>

      <!-- 趋势分析 -->
      <div class="card section">
        <div class="section-title">趋势分析</div>
        <div class="trend-grid">
          <div class="trend-item">
            <span class="label">5日</span>
            <span class="value">{{ analysis.trend_5d }}</span>
          </div>
          <div class="trend-item">
            <span class="label">10日</span>
            <span class="value">{{ analysis.trend_10d }}</span>
          </div>
          <div class="trend-item">
            <span class="label">20日</span>
            <span class="value">{{ analysis.trend_20d }}</span>
          </div>
        </div>
      </div>

      <!-- 均线状态 -->
      <div class="card section">
        <div class="section-title">均线状态</div>
        <div class="ma-list">
          <div
            v-for="(ma, key) in analysis.ma_status"
            :key="key"
            class="ma-item"
          >
            <span class="ma-name">{{ key }}</span>
            <span class="ma-value">{{ ma.value.toFixed(2) }}</span>
            <el-tag
              :type="ma.above ? 'success' : 'danger'"
              size="small"
            >
              {{ ma.above ? '上方' : '下方' }} {{ ma.diff_pct.toFixed(1) }}%
            </el-tag>
          </div>
        </div>
        <div class="conclusion">{{ analysis.ma_support }}</div>
      </div>

      <!-- MACD -->
      <div class="card section">
        <div class="section-title">MACD</div>
        <div class="info-row">
          <span>{{ analysis.macd_status }}</span>
          <el-tag
            v-if="analysis.macd_cross !== '无'"
            :type="analysis.macd_cross === '金叉' ? 'success' : 'danger'"
          >
            {{ analysis.macd_cross }}
          </el-tag>
        </div>
      </div>

      <!-- 上影线分析 -->
      <div class="card section" v-if="analysis.upper_shadow_warning">
        <div class="section-title">
          上影线预警
          <el-tag type="warning" size="small">注意</el-tag>
        </div>
        <div class="warning-text">
          上影线/实体比例: {{ analysis.upper_shadow_ratio.toFixed(2) }}
        </div>
        <div class="detail-text">{{ analysis.upper_shadow_detail }}</div>
      </div>

      <!-- 反转形态 -->
      <div class="card section">
        <div class="section-title">反转形态</div>
        <div v-if="analysis.patterns.length > 0" class="patterns-list">
          <div
            v-for="(pattern, idx) in analysis.patterns"
            :key="idx"
            class="pattern-card"
            :class="patternClass(pattern.type)"
          >
            <div class="pattern-header">
              <span class="pattern-name">{{ pattern.name }}</span>
              <el-tag
                :type="pattern.type === '看涨' ? 'success' : (pattern.type === '看跌' ? 'danger' : 'info')"
                size="small"
              >
                {{ pattern.type }} | {{ pattern.strength }}
              </el-tag>
            </div>
            <div class="pattern-desc">{{ pattern.desc }}</div>
            <div v-if="pattern.position_advice" class="pattern-advice">
              {{ pattern.position_advice }}
            </div>
          </div>
        </div>
        <div v-else class="no-pattern">
          暂无明显反转形态
        </div>
        <div class="pattern-analysis">
          <div
            v-for="(item, idx) in analysis.pattern_analysis"
            :key="idx"
            class="analysis-item"
          >
            {{ item }}
          </div>
        </div>
      </div>

      <!-- 支撑/压力线 -->
      <div class="card section">
        <div class="section-title">支撑/压力位</div>

        <div v-if="analysis.resistance_lines.length > 0" class="levels-section">
          <div class="levels-title">压力位</div>
          <div
            v-for="(line, idx) in analysis.resistance_lines"
            :key="'r'+idx"
            class="level-item resistance"
          >
            <div class="level-main">
              <span class="level-price">{{ line.price.toFixed(2) }}</span>
              <span class="level-name">{{ line.name }}</span>
            </div>
            <div class="level-detail">
              {{ line.vs_current }}
            </div>
          </div>
        </div>

        <div v-if="analysis.support_lines.length > 0" class="levels-section">
          <div class="levels-title">支撑位</div>
          <div
            v-for="(line, idx) in analysis.support_lines"
            :key="'s'+idx"
            class="level-item support"
          >
            <div class="level-main">
              <span class="level-price">{{ line.price.toFixed(2) }}</span>
              <span class="level-name">{{ line.name }}</span>
            </div>
            <div class="level-detail">
              {{ line.vs_current }}
            </div>
          </div>
        </div>

        <div v-if="analysis.support_break_status" class="break-status danger">
          {{ analysis.support_break_status }}
        </div>
        <div v-if="analysis.resistance_break_status" class="break-status success">
          {{ analysis.resistance_break_status }}
        </div>
      </div>

      <!-- 看多/看空因素 -->
      <div class="card section">
        <div class="section-title">综合分析</div>
        <div class="detail-text">{{ analysis.action_detail }}</div>

        <div v-if="analysis.bullish_factors.length > 0" class="factors bullish">
          <div class="factors-title">看多因素 ({{ analysis.bullish_factors.length }})</div>
          <div
            v-for="(f, idx) in analysis.bullish_factors"
            :key="'b'+idx"
            class="factor-item"
          >
            {{ f }}
          </div>
        </div>

        <div v-if="analysis.bearish_factors.length > 0" class="factors bearish">
          <div class="factors-title">看空因素 ({{ analysis.bearish_factors.length }})</div>
          <div
            v-for="(f, idx) in analysis.bearish_factors"
            :key="'e'+idx"
            class="factor-item"
          >
            {{ f }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import KLineChart from '@/components/KLineChart.vue'

defineOptions({ name: 'StockDetailPage' })

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const analysis = computed(() => store.currentAnalysis)

function actionTagType(action: string) {
  if (['买入', '加仓'].includes(action)) return 'success'
  if (['卖出', '减仓'].includes(action)) return 'danger'
  return 'info'
}

function patternClass(type: string) {
  if (type === '看涨') return 'bullish'
  if (type === '看跌') return 'bearish'
  return ''
}

watch(() => route.params.code, (newCode) => {
  if (newCode) {
    const type = route.query.type as string
    store.loadAnalysis(newCode as string, type === 'etf' ? 'etf' : 'stock')
  }
}, { immediate: true })
</script>

<style scoped>
.loading-state,
.error-state {
  padding: 40px 20px;
  text-align: center;
}

.detail-header {
  margin-bottom: 10px;
}

.stock-header {
  margin-bottom: 15px;
}

.stock-title {
  margin-bottom: 10px;
}

.stock-name {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.stock-code {
  font-size: 14px;
  color: #999;
  margin-left: 10px;
}

.stock-price {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.action-reason {
  font-size: 14px;
  color: #666;
}

.position-advice {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #409eff;
  background: #ecf5ff;
  padding: 10px;
  border-radius: 8px;
}

.section {
  margin-bottom: 15px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 6px;
}

.label {
  color: #666;
  font-size: 13px;
}

.value {
  color: #333;
  font-weight: 500;
}

.conclusion {
  font-size: 14px;
  color: #409eff;
  padding: 10px;
  background: #ecf5ff;
  border-radius: 6px;
}

.trend-grid {
  display: flex;
  gap: 15px;
}

.trend-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.trend-item .label {
  display: block;
  margin-bottom: 5px;
}

.trend-item .value {
  font-size: 13px;
}

.ma-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.ma-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: #f9f9f9;
  border-radius: 6px;
}

.ma-name {
  font-weight: 500;
}

.ma-value {
  color: #666;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.warning-text {
  font-size: 15px;
  color: #e6a23c;
  margin-bottom: 8px;
}

.detail-text {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.patterns-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.pattern-card {
  padding: 12px;
  border-radius: 8px;
  background: #f9f9f9;
}

.pattern-card.bullish {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.pattern-card.bearish {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.pattern-name {
  font-size: 15px;
  font-weight: 500;
}

.pattern-desc {
  font-size: 13px;
  color: #666;
}

.pattern-advice {
  font-size: 13px;
  color: #409eff;
  margin-top: 8px;
}

.no-pattern {
  font-size: 14px;
  color: #999;
  margin-bottom: 10px;
}

.pattern-analysis {
  background: #f9f9f9;
  padding: 10px;
  border-radius: 6px;
}

.analysis-item {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.levels-section {
  margin-bottom: 15px;
}

.levels-title {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.level-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  margin-bottom: 6px;
  border-radius: 6px;
}

.level-item.resistance {
  background: #fef0f0;
}

.level-item.support {
  background: #f0f9eb;
}

.level-price {
  font-weight: 600;
  margin-right: 10px;
}

.level-name {
  font-size: 13px;
  color: #666;
}

.level-detail {
  font-size: 12px;
  color: #999;
}

.break-status {
  padding: 10px;
  border-radius: 6px;
  margin-top: 10px;
  font-size: 14px;
}

.break-status.danger {
  background: #fef0f0;
  color: #f56c6c;
}

.break-status.success {
  background: #f0f9eb;
  color: #67c23a;
}

.factors {
  margin-top: 15px;
  padding: 12px;
  border-radius: 8px;
}

.factors.bullish {
  background: #f0f9eb;
}

.factors.bearish {
  background: #fef0f0;
}

.factors-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 10px;
}

.factor-item {
  font-size: 13px;
  color: #666;
  padding: 5px 0;
  border-bottom: 1px dashed #e0e0e0;
}

.factor-item:last-child {
  border-bottom: none;
}

.kline-section {
  padding: 15px;
}
</style>
