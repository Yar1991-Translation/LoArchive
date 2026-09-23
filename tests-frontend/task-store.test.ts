import { describe, expect, it, vi, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useTaskStore } from "@/stores/task";

// mock API 层
vi.mock("@/api", () => ({
  startTask: vi.fn().mockResolvedValue({ message: "任务已启动" }),
  stopTask: vi.fn().mockResolvedValue({ message: "已请求停止任务" }),
  getTaskStatus: vi.fn().mockResolvedValue({
    running: false,
    current_task: null,
    progress: 100,
    message: "",
    logs: [],
    error: null,
  }),
  taskEventsUrl: vi.fn().mockReturnValue("http://127.0.0.1:5000/api/task/events"),
}));

vi.mock("@/services/feedback", () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn(),
  confirmDanger: vi.fn(),
}));

describe("task store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("start 后进入运行中状态并展开任务坞", async () => {
    const store = useTaskStore();
    await store.start("ao3", { urls: ["https://example.com"] });

    expect(store.running).toBe(true);
    expect(store.currentTaskLabel).toBe("AO3 下载");
    expect(store.dockExpanded).toBe(true);
    expect(store.progress).toBe(0);
  });

  it("applyStatus 应用后端状态", () => {
    const store = useTaskStore();
    store.$patch({
      logs: [],
    });
    // 通过 SSE 快照同款路径应用状态
    (store as any).applyStatus({
      running: true,
      current_task: "like_share_tag",
      progress: 42,
      message: "抓取中",
      logs: ["[10:00:00] 开始"],
      error: null,
    });

    expect(store.running).toBe(true);
    expect(store.currentTaskLabel).toBe("喜欢 / 推荐 / Tag 爬取");
    expect(store.progress).toBe(42);
    expect(store.logs).toEqual(["[10:00:00] 开始"]);
  });

  it("日志超过 200 行时保留最新 200 行", () => {
    const store = useTaskStore();
    for (let i = 0; i < 250; i++) {
      (store as any).applyLogLine(`[10:00:00] line ${i}`, `line ${i}`);
    }
    expect(store.logs).toHaveLength(200);
    expect(store.logs[0]).toContain("line 50");
    expect(store.logs[199]).toContain("line 249");
  });

  it("未知任务类型回退显示原始名称", () => {
    const store = useTaskStore();
    (store as any).applyStatus({
      running: true,
      current_task: "mystery_task",
      progress: 0,
      message: "",
      logs: [],
      error: null,
    });
    expect(store.currentTaskLabel).toBe("mystery_task");
  });
});
