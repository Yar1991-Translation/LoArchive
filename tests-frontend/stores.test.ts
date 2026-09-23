import { describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useUiStore } from "@/stores/ui";

vi.mock("@/api", () => ({
  queryHistory: vi.fn(async (options: any) => ({
    items: [],
    total: 0,
    page: options?.page ?? 1,
    per_page: options?.perPage ?? 20,
    total_pages: 1,
    stats: { total: 0, images: 0, articles: 0 },
  })),
  deleteHistoryItem: vi.fn(async () => ({ message: "记录已删除" })),
  clearHistory: vi.fn(async () => ({ message: "历史记录已清空" })),
}));

describe("ui store", () => {
  it("切换视图", () => {
    setActivePinia(createPinia());
    const ui = useUiStore();
    expect(ui.currentView).toBe("lst");
    ui.switchView("ao3");
    expect(ui.currentView).toBe("ao3");
  });
});

describe("history store", () => {
  it("fetchPage 组合过滤参数并写回分页", async () => {
    setActivePinia(createPinia());
    const { queryHistory } = await import("@/api");
    const { useHistoryStore } = await import("@/stores/history");

    const store = useHistoryStore();
    store.search = "魔法少女";
    store.filterType = "image";
    await store.fetchPage(2);

    expect(queryHistory).toHaveBeenCalledWith(
      expect.objectContaining({ page: 2, search: "魔法少女", type: "image" }),
    );
    expect(store.page).toBe(2);
  });

  it("removeItem 与 clearAll 调用对应 API 并刷新列表", async () => {
    setActivePinia(createPinia());
    const { deleteHistoryItem, clearHistory } = await import("@/api");
    const { useHistoryStore } = await import("@/stores/history");

    const store = useHistoryStore();
    await store.removeItem("abc");
    await store.clearAll();

    expect(deleteHistoryItem).toHaveBeenCalledWith("abc");
    expect(clearHistory).toHaveBeenCalled();
  });
});
