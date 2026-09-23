<script setup lang="ts">
import { computed } from "vue";

import { useSettingsStore } from "@/stores/settings";
import { useTaskStore } from "@/stores/task";
import { useUiStore, type ViewName } from "@/stores/ui";

const ui = useUiStore();
const task = useTaskStore();
const settings = useSettingsStore();

interface NavItem {
  view: ViewName;
  label: string;
  icon: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const sections: NavSection[] = [
  {
    title: "Lofter",
    items: [
      { view: "lst", label: "喜欢 / 推荐 / Tag", icon: "favorite" },
      { view: "author-img", label: "作者图片", icon: "image" },
      { view: "author-txt", label: "作者文章", icon: "edit_note" },
      { view: "single", label: "单篇保存", icon: "attach_file" },
    ],
  },
  {
    title: "AO3",
    items: [{ view: "ao3", label: "AO3 文章", icon: "auto_stories" }],
  },
  {
    title: "系统",
    items: [
      { view: "history", label: "下载历史", icon: "content_paste" },
      { view: "settings", label: "设置", icon: "settings" },
    ],
  },
];

const statusText = computed(() => (task.running ? "运行中" : "就绪"));
const authText = computed(() => (settings.config.has_auth ? "已配置" : "未配置"));
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">
        <span class="mi mi-filled" aria-hidden="true">menu_book</span>
      </div>
      <div class="brand-text">
        <h1>LoArchive</h1>
        <p>Lofter &amp; AO3 存档工具</p>
      </div>
    </div>

    <nav class="nav" aria-label="功能导航">
      <template v-for="section in sections" :key="section.title">
        <div class="nav-section-title">{{ section.title }}</div>
        <button
          v-for="item in section.items"
          :key="item.view"
          type="button"
          class="nav-item"
          :class="{ active: ui.currentView === item.view }"
          :aria-current="ui.currentView === item.view ? 'page' : undefined"
          @click="ui.switchView(item.view)"
        >
          <span class="mi nav-icon" aria-hidden="true">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="status-card">
        <div class="status-row">
          <span>运行状态</span>
          <span class="status-value">
            <span class="status-dot" :class="{ running: task.running }" aria-hidden="true"></span>
            {{ statusText }}
          </span>
        </div>
        <div class="status-row">
          <span>登录状态</span>
          <span class="status-value">{{ authText }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 232px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--la-chrome);
  border-right: 1px solid var(--la-border);
  padding: 18px 12px 14px;
  gap: 16px;
  min-height: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 2px 8px;
}

.brand-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--la-radius);
  background: var(--la-primary);
  color: var(--la-primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-icon .mi {
  font-size: 24px;
}

.brand-text h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.2;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--la-text-muted);
}

.nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  min-height: 0;
}

.nav-section-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--la-text-muted);
  padding: 12px 10px 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: none;
  border-radius: var(--la-radius-small);
  background: transparent;
  color: var(--la-text-secondary);
  font: inherit;
  font-size: 13.5px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--la-surface-hover);
  color: var(--la-text);
}

.nav-item.active {
  background: var(--la-primary);
  color: var(--la-primary-text);
  font-weight: 500;
}

.nav-icon {
  font-size: 19px;
}

.sidebar-footer {
  flex-shrink: 0;
}

.status-card {
  border: 1px solid var(--la-border);
  border-radius: var(--la-radius-small);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12.5px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--la-text-muted);
}

.status-value {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--la-text-secondary);
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--la-text-muted);
}

.status-dot.running {
  background: var(--la-success);
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  50% {
    opacity: 0.45;
  }
}

@media (max-width: 900px) {
  .sidebar {
    width: 68px;
    padding: 14px 8px;
  }

  .brand-text,
  .nav-label,
  .nav-section-title,
  .status-card {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 11px 0;
  }
}
</style>
