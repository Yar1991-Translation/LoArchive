/** 任务状态：SSE 实时流为主，EventSource 放弃连接后回退轮询。 */

import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api";
import type { TaskStatus } from "@/api/types";
import { notifyError, notifySuccess } from "@/services/feedback";

const TASK_LABELS: Record<string, string> = {
  like_share_tag: "喜欢 / 推荐 / Tag 爬取",
  author_img: "作者图片下载",
  author_txt: "作者文章下载",
  single_img: "单篇图片保存",
  single_txt: "单篇文章保存",
  ao3: "AO3 下载",
};

export const useTaskStore = defineStore("task", () => {
  const running = ref(false);
  const currentTask = ref<string | null>(null);
  const progress = ref(0);
  const message = ref("");
  const logs = ref<string[]>([]);
  const error = ref<string | null>(null);
  const dockExpanded = ref(false);

  const currentTaskLabel = computed(() =>
    currentTask.value ? (TASK_LABELS[currentTask.value] ?? currentTask.value) : "",
  );

  function applyStatus(status: TaskStatus) {
    running.value = status.running;
    currentTask.value = status.current_task;
    progress.value = status.progress;
    message.value = status.message;
    logs.value = [...status.logs];
    error.value = status.error;
  }

  function applyLogLine(line: string, text: string) {
    logs.value.push(line);
    // 与后端一致，最多保留 200 行
    if (logs.value.length > 200) {
      logs.value.splice(0, logs.value.length - 200);
    }
    message.value = text;
  }

  // ---------- SSE / 轮询 ----------

  let eventSource: EventSource | null = null;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  /** SSE 不可用时整个会话降级为轮询 */
  let forcePolling = false;

  function ensureStream() {
    if (forcePolling) {
      ensurePolling();
      return;
    }
    if (eventSource) return;
    eventSource = new EventSource(api.taskEventsUrl());

    eventSource.addEventListener("snapshot", (e) => {
      const status = JSON.parse((e as MessageEvent).data) as TaskStatus;
      applyStatus(status);
      checkFinished(status);
    });
    eventSource.addEventListener("log", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as { line: string; message: string };
      applyLogLine(data.line, data.message);
    });
    eventSource.addEventListener("progress", (e) => {
      const data = JSON.parse((e as MessageEvent).data) as { progress: number };
      progress.value = data.progress;
    });
    eventSource.addEventListener("done", (e) => {
      const status = JSON.parse((e as MessageEvent).data) as TaskStatus;
      applyStatus(status);
      checkFinished(status);
    });
    eventSource.onerror = () => {
      // readyState CLOSED 表示浏览器放弃重连（如连接被拒），切换到轮询
      if (eventSource && eventSource.readyState === EventSource.CLOSED) {
        eventSource = null;
        forcePolling = true;
        ensurePolling();
      }
    };
  }

  function ensurePolling() {
    if (pollTimer) return;
    pollTimer = setInterval(async () => {
      try {
        const status = await api.getTaskStatus();
        applyStatus(status);
        checkFinished(status);
      } catch {
        // 后端暂时不可达，下个周期重试
      }
    }, 1000);
  }

  function checkFinished(status: TaskStatus) {
    // 快照是权威状态：短任务可能在订阅建立前就结束
    if (!status.running && status.progress >= 100) {
      running.value = false;
      if (status.error) {
        notifyError(`任务失败: ${status.error}`);
      } else {
        notifySuccess("任务完成！");
      }
    }
  }

  // ---------- 动作 ----------

  async function start(type: string, params: Record<string, unknown>) {
    await api.startTask(type, params);
    running.value = true;
    currentTask.value = type; // 立即显示任务名，后端快照随后覆盖
    error.value = null;
    progress.value = 0;
    message.value = "";
    dockExpanded.value = true;
    ensureStream();
  }

  async function stop() {
    await api.stopTask();
    message.value = "正在停止任务...";
  }

  /** 恢复界面时对齐一次后端状态（例如刷新后） */
  async function syncFromBackend() {
    try {
      const status = await api.getTaskStatus();
      applyStatus(status);
      if (status.running) ensureStream();
    } catch {
      // 后端不可达时保持默认空闲状态
    }
  }

  return {
    running,
    currentTask,
    currentTaskLabel,
    progress,
    message,
    logs,
    error,
    dockExpanded,
    applyStatus,
    applyLogLine,
    start,
    stop,
    syncFromBackend,
  };
});
