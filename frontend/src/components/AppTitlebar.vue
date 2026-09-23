<script setup lang="ts">
import { onMounted, ref } from "vue";

import { isTauri } from "@/composables/usePlatform";

const maximized = ref(false);
let appWindow: any = null;

async function toggleMaximize() {
  if (!appWindow) return;
  maximized.value = await appWindow.isMaximized();
  maximized.value ? await appWindow.unmaximize() : await appWindow.maximize();
}

onMounted(async () => {
  if (!isTauri.value) return;
  try {
    const tauri = (window as any).__TAURI__;
    if (tauri?.window) {
      appWindow = tauri.window.getCurrentWindow();
    } else {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      appWindow = getCurrentWindow();
    }
    maximized.value = await appWindow.isMaximized();
    const unlisten = await appWindow.onResized(async () => {
      maximized.value = await appWindow.isMaximized();
    });
    if (typeof unlisten === "function") onMounted(() => unlisten());
  } catch (e) {
    console.error("Tauri 窗口控制初始化失败:", e);
  }
});
</script>

<template>
  <header v-if="isTauri" class="titlebar" data-tauri-drag-region>
    <div class="titlebar-brand" data-tauri-drag-region>
      <span class="mi mi-filled titlebar-logo" aria-hidden="true">menu_book</span>
      <span class="titlebar-name">LoArchive</span>
    </div>
    <div class="titlebar-actions">
      <button class="titlebar-btn" type="button" title="最小化" aria-label="最小化" @click="appWindow?.minimize()">
        <svg viewBox="0 0 12 12" aria-hidden="true"><line x1="2" y1="6" x2="10" y2="6" /></svg>
      </button>
      <button
        class="titlebar-btn"
        type="button"
        :title="maximized ? '还原' : '最大化'"
        :aria-label="maximized ? '还原' : '最大化'"
        @click="toggleMaximize"
      >
        <svg v-if="maximized" viewBox="0 0 12 12" aria-hidden="true">
          <rect x="1.5" y="3.5" width="7" height="7" rx="1" />
          <polyline points="3.5,3.5 3.5,1.5 10.5,1.5 10.5,8.5 8.5,8.5" />
        </svg>
        <svg v-else viewBox="0 0 12 12" aria-hidden="true"><rect x="2" y="2" width="8" height="8" rx="1.5" /></svg>
      </button>
      <button class="titlebar-btn titlebar-close" type="button" title="关闭" aria-label="关闭" @click="appWindow?.close()">
        <svg viewBox="0 0 12 12" aria-hidden="true">
          <line x1="3" y1="3" x2="9" y2="9" />
          <line x1="9" y1="3" x2="3" y2="9" />
        </svg>
      </button>
    </div>
  </header>
</template>

<style scoped>
.titlebar {
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--la-chrome);
  border-bottom: 1px solid var(--la-border);
  user-select: none;
  padding-left: 14px;
}

.titlebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  flex: 1;
}

.titlebar-logo {
  font-size: 18px;
  color: var(--la-primary);
}

.titlebar-name {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.titlebar-actions {
  display: flex;
  height: 100%;
}

.titlebar-btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: var(--la-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s ease;
}

.titlebar-btn svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
  stroke-linecap: round;
}

.titlebar-btn:hover {
  background: var(--la-surface-hover);
}

.titlebar-close:hover {
  background: #e81123;
  color: #ffffff;
}

[data-theme="bw"] .titlebar {
  border-bottom: 2px solid #000;
}
</style>
