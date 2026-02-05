<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- 底部导航 -->
      <router-view v-slot="{ Component, route }">
        <keep-alive :exclude="['StockDetailPage']">
          <component :is="Component" :key="route.path" />
        </keep-alive>
      </router-view>

      <!-- 底部TabBar -->
      <div class="tab-bar">
        <router-link
          v-for="item in tabs"
          :key="item.path"
          :to="item.path"
          class="tab-item"
          :class="{ active: $route.path === item.path }"
        >
          <el-icon :size="24">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import {
  HomeFilled,
  Star,
  TrendCharts,
  Coin,
  Setting
} from '@element-plus/icons-vue'

const tabs = ref([
  { path: '/', label: '首页', icon: HomeFilled },
  { path: '/watchlist', label: '自选股', icon: Star },
  { path: '/top10', label: 'Top10', icon: TrendCharts },
  { path: '/etf', label: 'ETF', icon: Coin },
  { path: '/settings', label: '设置', icon: Setting },
])
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f5f5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  min-height: 100vh;
  padding-bottom: 70px;
}

.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  display: flex;
  justify-content: space-around;
  align-items: center;
  border-top: 1px solid #e5e5e5;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1000;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: #999;
  font-size: 12px;
  padding: 5px 10px;
  transition: color 0.2s;
}

.tab-item span {
  margin-top: 4px;
}

.tab-item.active {
  color: #409eff;
}

.tab-item:hover {
  color: #409eff;
}

/* 页面通用样式 */
.page-container {
  padding: 15px;
  padding-bottom: 80px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #333;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 信号卡片样式 */
.signal-buy {
  border-left: 4px solid #67c23a;
}

.signal-sell {
  border-left: 4px solid #f56c6c;
}

.signal-hold {
  border-left: 4px solid #909399;
}

/* 价格颜色 */
.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-flat {
  color: #909399;
}
</style>
