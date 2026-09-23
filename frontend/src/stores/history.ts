/** 下载历史：分页查询、过滤搜索、删除与清空。 */

import { defineStore } from "pinia";
import { ref } from "vue";

import * as api from "@/api";
import type { HistoryItem, HistoryQueryResult } from "@/api/types";

const EMPTY: HistoryQueryResult = {
  items: [],
  total: 0,
  page: 1,
  per_page: 20,
  total_pages: 1,
  stats: { total: 0, images: 0, articles: 0 },
};

export const useHistoryStore = defineStore("history", () => {
  const result = ref<HistoryQueryResult>(EMPTY);
  const page = ref(1);
  const perPage = ref(20);
  const filterType = ref("");
  const filterSource = ref("");
  const search = ref("");
  const loading = ref(false);
  const loadError = ref("");

  async function fetchPage(targetPage?: number) {
    loading.value = true;
    loadError.value = "";
    if (targetPage) page.value = targetPage;
    try {
      result.value = await api.queryHistory({
        page: page.value,
        perPage: perPage.value,
        type: filterType.value,
        source: filterSource.value,
        search: search.value.trim(),
      });
      page.value = result.value.page;
    } catch (e) {
      loadError.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  async function removeItem(itemId: string) {
    await api.deleteHistoryItem(itemId);
    await fetchPage();
  }

  async function clearAll() {
    await api.clearHistory();
    await fetchPage(1);
  }

  return {
    result,
    page,
    perPage,
    filterType,
    filterSource,
    search,
    loading,
    loadError,
    fetchPage,
    removeItem,
    clearAll,
  };
});
