<script setup lang="ts">
import { NModal, NButton } from "naive-ui";
import { ref } from "vue";

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{ done: [] }>();

const step = ref(1);
const TOTAL_STEPS = 3;

interface StepContent {
  title: string;
  items: { icon: string; heading: string; text: string }[];
}

const steps: StepContent[] = [
  {
    title: "主要功能",
    items: [
      { icon: "favorite", heading: "Lofter 内容爬取", text: "保存喜欢、推荐、Tag 内容，支持图片和文章批量下载" },
      { icon: "auto_stories", heading: "AO3 文章下载", text: "下载 AO3 作品、系列、作者全部文章，支持导出 PDF / EPUB" },
      { icon: "bookmark", heading: "PDF 导出", text: "将下载的内容转换为精美排版的 PDF 文件" },
    ],
  },
  {
    title: "配置登录信息",
    items: [
      { icon: "key", heading: "获取授权码", text: "打开 Lofter 网页版 → 按 F12 打开开发者工具 → Application → Cookies" },
      { icon: "edit_note", heading: "填写配置", text: "在「设置」页面选择登录方式，粘贴对应的授权码" },
      { icon: "auto_awesome", heading: "AO3 无需配置", text: "AO3 功能无需登录，可直接使用" },
    ],
  },
  {
    title: "开始使用",
    items: [
      { icon: "looks_one", heading: "选择功能", text: "从左侧菜单选择需要的功能模块" },
      { icon: "looks_two", heading: "填写链接", text: "粘贴要爬取的页面链接，可选择保存格式" },
      { icon: "rocket_launch", heading: "开始爬取", text: "点击开始按钮，进度与日志会显示在底部任务坞" },
    ],
  },
];

function next() {
  if (step.value < TOTAL_STEPS) {
    step.value += 1;
  } else {
    finish();
  }
}

function finish() {
  localStorage.setItem("loarchive_onboarding_done", "1");
  emit("done");
}

function skip() {
  finish();
}
</script>

<template>
  <NModal :show="props.show" :mask-closable="false" :close-on-esc="false" transform-origin="center">
    <div class="onboarding" role="dialog" aria-label="新手引导">
      <div class="onb-hero">
        <span class="mi mi-filled onb-logo" aria-hidden="true">menu_book</span>
        <h2>欢迎使用 LoArchive</h2>
        <p>Lofter &amp; AO3 内容存档工具</p>
      </div>

      <div class="onb-body">
        <h3 class="onb-step-title">
          <span class="onb-step-num">{{ step }}</span>
          {{ steps[step - 1]!.title }}
        </h3>
        <ul class="onb-list">
          <li v-for="item in steps[step - 1]!.items" :key="item.heading">
            <span class="mi onb-item-icon" aria-hidden="true">{{ item.icon }}</span>
            <div>
              <h4>{{ item.heading }}</h4>
              <p>{{ item.text }}</p>
            </div>
          </li>
        </ul>
      </div>

      <div class="onb-footer">
        <div class="onb-dots" aria-hidden="true">
          <span v-for="i in TOTAL_STEPS" :key="i" class="onb-dot" :class="{ active: step === i }"></span>
        </div>
        <div class="onb-actions">
          <NButton quaternary @click="skip">跳过</NButton>
          <NButton type="primary" @click="next">
            {{ step < TOTAL_STEPS ? "下一步" : "开始使用" }}
          </NButton>
        </div>
      </div>
    </div>
  </NModal>
</template>

<style scoped>
.onboarding {
  width: min(520px, calc(100vw - 48px));
  background: var(--la-surface);
  border: 1px solid var(--la-border);
  border-radius: var(--la-radius);
  box-shadow: var(--la-shadow);
  overflow: hidden;
}

.onb-hero {
  background: var(--la-primary);
  color: var(--la-primary-text);
  padding: 28px 32px;
}

.onb-logo {
  font-size: 40px;
  margin-bottom: 10px;
  display: inline-block;
}

.onb-hero h2 {
  margin: 0;
  font-size: 20px;
}

.onb-hero p {
  margin: 4px 0 0;
  opacity: 0.85;
  font-size: 13px;
}

.onb-body {
  padding: 22px 32px;
  min-height: 240px;
}

.onb-step-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  margin: 0 0 16px;
}

.onb-step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--la-primary);
  color: var(--la-primary-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

.onb-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.onb-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.onb-item-icon {
  color: var(--la-primary);
  font-size: 22px;
  margin-top: 2px;
}

.onb-list h4 {
  margin: 0;
  font-size: 14px;
}

.onb-list p {
  margin: 2px 0 0;
  font-size: 12.5px;
  color: var(--la-text-muted);
}

.onb-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 32px 20px;
}

.onb-dots {
  display: flex;
  gap: 6px;
}

.onb-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--la-track);
  transition: background 0.2s ease;
}

.onb-dot.active {
  background: var(--la-primary);
}

.onb-actions {
  display: flex;
  gap: 8px;
}
</style>
