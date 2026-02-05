<template>
  <div class="page-container">
    <h1 class="page-title">自选ETF</h1>

    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" class="etf-tabs">
      <el-tab-pane label="我的ETF" name="my">
        <div v-if="store.etfWatchlist.length === 0" class="empty-tip">
          <el-empty description="暂无自选ETF">
            <el-button type="primary" @click="activeTab = 'popular'">
              去添加
            </el-button>
          </el-empty>
        </div>

        <div v-else class="etf-list">
          <div
            v-for="etf in store.etfWatchlist"
            :key="etf.code"
            class="etf-card"
            @click="goToDetail(etf.code)"
          >
            <div class="etf-main">
              <div class="etf-info">
                <span class="etf-name">{{ etf.name }}</span>
                <span class="etf-code">{{ etf.code }}</span>
              </div>
            </div>
            <div class="etf-actions" @click.stop>
              <el-button
                type="danger"
                size="small"
                text
                :icon="Delete"
                @click="handleRemove(etf.code)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="搜索" name="search">
        <el-input
          v-model="searchKeyword"
          placeholder="输入ETF代码或名称"
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
        />

        <div class="search-results">
          <div
            v-for="item in searchResults"
            :key="item.code"
            class="search-item"
          >
            <div class="item-info">
              <span class="item-name">{{ item.name }}</span>
              <span class="item-code">{{ item.code }}</span>
            </div>
            <el-button
              type="primary"
              size="small"
              @click="handleAdd(item)"
            >
              添加
            </el-button>
          </div>
          <el-empty
            v-if="searchKeyword && searchResults.length === 0"
            description="无搜索结果"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="热门ETF" name="popular">
        <div class="popular-section">
          <div class="category-title">宽基ETF</div>
          <div class="popular-list">
            <div
              v-for="etf in broadEtfs"
              :key="etf.code"
              class="popular-card"
            >
              <div class="popular-info" @click="goToDetail(etf.code)">
                <span class="popular-name">{{ etf.name }}</span>
                <span class="popular-code">{{ etf.code }}</span>
              </div>
              <el-button
                v-if="!isInWatchlist(etf.code)"
                type="primary"
                size="small"
                @click.stop="handleAdd(etf)"
              >
                添加
              </el-button>
              <el-tag v-else type="success" size="small">已添加</el-tag>
            </div>
          </div>
        </div>

        <div class="popular-section">
          <div class="category-title">行业ETF</div>
          <div class="popular-list">
            <div
              v-for="etf in industryEtfs"
              :key="etf.code"
              class="popular-card"
            >
              <div class="popular-info" @click="goToDetail(etf.code)">
                <span class="popular-name">{{ etf.name }}</span>
                <span class="popular-code">{{ etf.code }}</span>
              </div>
              <el-button
                v-if="!isInWatchlist(etf.code)"
                type="primary"
                size="small"
                @click.stop="handleAdd(etf)"
              >
                添加
              </el-button>
              <el-tag v-else type="success" size="small">已添加</el-tag>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import { etfApi } from '@/api'
import { Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { SearchResult, ETF } from '@/types'

const router = useRouter()
const store = useAppStore()

const activeTab = ref('my')
const searchKeyword = ref('')
const searchResults = ref<SearchResult[]>([])
let searchTimer: number | null = null

// 宽基ETF
const broadEtfs = computed(() =>
  store.popularEtfs.filter(e => e.category === '宽基')
)

// 行业ETF
const industryEtfs = computed(() =>
  store.popularEtfs.filter(e => e.category === '行业')
)

// 是否在自选中
function isInWatchlist(code: string) {
  return store.etfWatchlist.some(e => e.code === code)
}

// 搜索
async function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)

  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }

  searchTimer = window.setTimeout(async () => {
    try {
      const res = await etfApi.search(searchKeyword.value)
      searchResults.value = res.results
    } catch (e) {
      console.error(e)
    }
  }, 300)
}

// 添加
async function handleAdd(item: ETF) {
  const success = await store.addEtfToWatchlist(item.code, item.name)
  if (success) {
    ElMessage.success(`已添加 ${item.name}`)
  } else {
    ElMessage.error('添加失败')
  }
}

// 删除
async function handleRemove(code: string) {
  try {
    await ElMessageBox.confirm('确定要删除该ETF吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const success = await store.removeEtfFromWatchlist(code)
    if (success) {
      ElMessage.success('已删除')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 取消
  }
}

// 跳转详情
function goToDetail(code: string) {
  router.push(`/stock/${code}?type=etf`)
}

onMounted(() => {
  store.loadEtfWatchlist()
  store.loadPopularEtfs()
})
</script>

<style scoped>
.etf-tabs {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
}

.etf-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.etf-card {
  background: #f9f9f9;
  border-radius: 10px;
  padding: 12px 15px;
  cursor: pointer;
}

.etf-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.etf-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.etf-code {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.etf-actions {
  display: flex;
  justify-content: flex-end;
}

.search-results {
  margin-top: 15px;
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.item-info {
  display: flex;
  align-items: center;
}

.item-name {
  font-size: 15px;
  color: #333;
}

.item-code {
  font-size: 13px;
  color: #999;
  margin-left: 8px;
}

.popular-section {
  margin-bottom: 20px;
}

.category-title {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 10px;
  padding-left: 5px;
  border-left: 3px solid #409eff;
}

.popular-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.popular-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9f9f9;
  border-radius: 10px;
  padding: 12px 15px;
}

.popular-info {
  cursor: pointer;
}

.popular-name {
  font-size: 14px;
  color: #333;
}

.popular-code {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.empty-tip {
  padding: 40px 20px;
}
</style>
