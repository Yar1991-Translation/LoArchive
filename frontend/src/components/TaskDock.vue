<script setup lang="ts">
import { NButton } from "naive-ui";
import { ref, watch } from "vue";

import { useTaskStore } from "@/stores/task";

const task = useTaskStore();
const logBox = ref<HTMLElement | null>(null);

watch(
  () => task.logs.length,
  () => {
    requestAnimationFrame(() => {
      logBox.value?.scrollTo({ top: logBox.value.scrollHeight });
    });
  },
);

function toggleExpand() {
  task.dockExpanded = !task.dockExpanded;
}

async function onStop() {
  try {
    await task.stop();
  } catch {
    // 停止失败由全局通知提示
  }
}
</script>

<template>
  <section class="task-dock" :class="{ expanded: task.dockExpanded, active: task.running }" aria-label="任务状态">
    <div v-if="task.dockExpanded" class="dock-log">
      <div class="dock-log-header">
        <span class="mi" aria-hidden="true">receipt_long</span>
        运行日志
        <span class="dock-log-count">{{ task.logs.length }} 行</span>
      </div>
      <div ref="logBox" class="dock-log-body" role="log" aria-live="polite">
        <div v-if="task.logs.length === 0" class="dock-log-empty">暂无日志</div>
        <div v-for="(line, index) in task.logs" :key="index" class="dock-log-line">{{ line }}</div>
      </div>
    </div>

    <div class="dock-bar">
      <button
        type="button"
        class="dock-expand"
        :aria-expanded="task.dockExpanded"
        :title="task.dockExpanded ? '收起日志' : '展开日志'"
        @click="toggleExpand"
      >
        <span class="mi" aria-hidden="true">{{ task.dockExpanded ? "keyboard_arrow_down" : "keyboard_arrow_up" }}</span>
      </button>

      <div class="dock-info">
        <template v-if="task.running">
          <span class="dock-spinner" aria-hidden="true"></span>
          <span class="dock-title">{{ task.currentTaskLabel }}</span>
          <span class="dock-message">{{ task.message || "运行中..." }}</span>
        </template>
        <template v-else-if="task.error">
          <span class="mi dock-status-icon error" aria-hidden="true">error</span>
          <span class="dock-title">上次任务失败</span>
          <span class="dock-message">{{ task.error }}</span>
        </template>
        <template v-else>
          <span class="mi dock-status-icon idle" aria-hidden="true">check_circle</span>
          <span class="dock-message">就绪 · 所有模块可用</span>
        </template>
      </div>

      <div class="dock-progress" aria-hidden="true">
        <div class="dock-progress-fill" :style="{ width: task.progress + '%' }"></div>
      </div>
      <span class="dock-percent">{{ task.progress }}%</span>

      <NButton v-if="task.running" size="small" type="error" secondary @click="onStop">
        <template #icon><span class="mi" style="font-size: 16px">stop_circle</span></template>
        停止
      </NButton>
    </div>
  </section>
</template>

<style scoped>
.task-dock {
  position: fixed;
  left: 232px;
  right: 0;
  bottom: 0;
  background: var(--la-chrome);
  border-top: 1px solid var(--la-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.task-dock.expanded {
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.12);
}

.dock-log {
  height: 240px;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid var(--la-border);
  background: var(--la-surface-alt);
}

.dock-log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--la-text-secondary);
  border-bottom: 1px solid var(--la-border);
}

.dock-log-header .mi {
  font-size: 16px;
}

.dock-log-count {
  margin-left: auto;
  font-weight: 400;
  color: var(--la-text-muted);
}

.dock-log-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.7;
}

.dock-log-line {
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--la-text-secondary);
}

.dock-log-empty {
  color: var(--la-text-muted);
}

.dock-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  min-height: 52px;
}

.dock-expand {
  border: none;
  background: transparent;
  color: var(--la-text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--la-radius-small);
  display: flex;
}

.dock-expand:hover {
  background: var(--la-surface-hover);
  color: var(--la-text);
}

.dock-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.dock-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--la-track);
  border-top-color: var(--la-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.dock-status-icon.idle {
  color: var(--la-success);
  font-size: 18px;
}

.dock-status-icon.error {
  color: var(--la-error);
  font-size: 18px;
}

.dock-title {
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}

.dock-message {
  color: var(--la-text-muted);
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.dock-progress {
  width: 180px;
  height: 6px;
  border-radius: 3px;
  background: var(--la-track);
  overflow: hidden;
  flex-shrink: 0;
}

.dock-progress-fill {
  height: 100%;
  background: var(--la-primary);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.dock-percent {
  font-size: 12px;
  font-weight: 600;
  color: var(--la-text-secondary);
  width: 38px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .task-dock {
    left: 68px;
  }

  .dock-progress {
    width: 110px;
  }

  .dock-message {
    display: none;
  }
}
</style>
