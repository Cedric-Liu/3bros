import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomePage.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('@/views/WatchlistPage.vue'),
    meta: { title: '自选股' }
  },
  {
    path: '/top10',
    name: 'Top10',
    component: () => import('@/views/Top10Page.vue'),
    meta: { title: 'Top10推荐' }
  },
  {
    path: '/etf',
    name: 'ETF',
    component: () => import('@/views/EtfPage.vue'),
    meta: { title: '自选ETF' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsPage.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/stock/:code',
    name: 'StockDetail',
    component: () => import('@/views/StockDetailPage.vue'),
    meta: { title: '股票详情' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || '反转三兄弟'} - 反转三兄弟`
  next()
})

export default router
