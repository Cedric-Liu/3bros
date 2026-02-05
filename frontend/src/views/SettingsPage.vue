<template>
  <div class="page-container">
    <h1 class="page-title">设置</h1>

    <!-- Server酱配置 -->
    <div class="card settings-section">
      <div class="section-header">
        <span class="section-title">微信推送 (Server酱)</span>
        <el-tag
          :type="store.settings.serverchan_configured ? 'success' : 'info'"
          size="small"
        >
          {{ store.settings.serverchan_configured ? '已配置' : '未配置' }}
        </el-tag>
      </div>

      <el-form label-position="top">
        <el-form-item label="SendKey">
          <el-input
            v-model="sendKey"
            :placeholder="store.settings.serverchan_key || '请输入Server酱SendKey'"
            type="password"
            show-password
          />
          <div class="form-tip">
            <a href="https://sct.ftqq.com/" target="_blank">
              点击获取SendKey
            </a>
          </div>
        </el-form-item>

        <el-form-item label="推送时间">
          <el-time-picker
            v-model="pushTime"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择推送时间"
          />
        </el-form-item>

        <div class="form-actions">
          <el-button type="primary" @click="handleSave" :loading="saving">
            保存设置
          </el-button>
          <el-button
            @click="handleTest"
            :loading="testing"
            :disabled="!store.settings.serverchan_configured && !sendKey"
          >
            测试推送
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 关于 -->
    <div class="card settings-section">
      <div class="section-title">关于</div>
      <div class="about-content">
        <p><strong>反转三兄弟</strong> v1.0.0</p>
        <p>基于K线反转形态的A股分析工具</p>
        <p class="tip">
          本工具仅供学习参考，不构成投资建议。
          <br/>
          股市有风险，投资需谨慎。
        </p>
      </div>
    </div>

    <!-- 策略说明 -->
    <div class="card settings-section">
      <div class="section-title">策略要点</div>
      <div class="strategy-content">
        <div class="strategy-item">
          <div class="strategy-name">阳吞阴</div>
          <div class="strategy-desc">阳线实体完全包含前阴线，看涨信号</div>
        </div>
        <div class="strategy-item">
          <div class="strategy-name">阴吞阳</div>
          <div class="strategy-desc">阴线实体完全包含前阳线，看跌信号</div>
        </div>
        <div class="strategy-item">
          <div class="strategy-name">刺透形态</div>
          <div class="strategy-desc">低开后阳线穿透前阴线1/2以上</div>
        </div>
        <div class="strategy-item">
          <div class="strategy-name">乌云盖顶</div>
          <div class="strategy-desc">高开后阴线深入前阳线1/2以上</div>
        </div>
        <div class="strategy-item">
          <div class="strategy-name">锤子线</div>
          <div class="strategy-desc">下跌趋势中长下影线，需隔天阳线确认</div>
        </div>
        <div class="strategy-item">
          <div class="strategy-name">上吊线</div>
          <div class="strategy-desc">上涨趋势中长下影线，需隔天阴线确认</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores'
import { ElMessage } from 'element-plus'

const store = useAppStore()

const sendKey = ref('')
const pushTime = ref<string>('15:30')
const saving = ref(false)
const testing = ref(false)

// 保存设置
async function handleSave() {
  saving.value = true
  try {
    const data: { serverchan_key?: string; push_time?: string } = {}

    if (sendKey.value) {
      data.serverchan_key = sendKey.value
    }
    if (pushTime.value) {
      data.push_time = pushTime.value
    }

    const success = await store.updateSettings(data)
    if (success) {
      ElMessage.success('设置已保存')
      sendKey.value = '' // 清空输入
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

// 测试推送
async function handleTest() {
  // 如果输入了新的key，先自动保存
  if (sendKey.value) {
    saving.value = true
    const success = await store.updateSettings({ serverchan_key: sendKey.value })
    saving.value = false
    if (!success) {
      ElMessage.error('保存SendKey失败')
      return
    }
    ElMessage.success('SendKey已保存')
    sendKey.value = ''
  }

  testing.value = true
  try {
    const res = await store.testNotify()
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  store.loadSettings()
})
</script>

<style scoped>
.settings-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.form-tip a {
  color: #409eff;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.about-content {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
}

.about-content p {
  margin: 0 0 10px;
}

.about-content .tip {
  font-size: 12px;
  color: #999;
  margin-top: 15px;
}

.strategy-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strategy-item {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 8px;
}

.strategy-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.strategy-desc {
  font-size: 13px;
  color: #666;
}
</style>
