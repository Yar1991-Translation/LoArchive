<script setup lang="ts">
import {
  NButton,
  NSelect,
  NInput,
  NPagination,
  NSpin,
  NEmpty,
  NTag,
  useMessage,
} from "naive-ui";
import { onMounted, ref, watch } from "vue";

import PageHeader from "@/components/PageHeader.vue";
import { notifyError } from "@/services/feedback";
import { confirmDanger } from "@/services/feedback";
import { useHistoryStore } from "@/stores/history";

const history = useHistoryStore();
const message = useMessage();

const searchInput = ref(history.search);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const typeOptions = [
  { label: "全部类型", value: "" },
  { label: "图片", value: "image" },
  { label: "文章", value: "article" },
  { label: "AO3", value: "ao3" },
];

const sourceOptions = [
  { label: "全部来源", value: "" },
  { label: "Lofter", value: "lofter" },
  { label: "AO3", value: "ao3" },
];

// 防抖搜索：输入停顿 400ms 后自动查询
watch(searchInput, (value) => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    history.search = value;
    void history.fetchPage(1);
  }, 400);
});

watch([() => history.filterType, () => history.filterSource], () => {
  void history.fetchPage(1);
});

onMounted(() => {
  void history.fetchPage();
});

function typeLabel(type: string): string {
  if (type === "image") return "图片";
  if (type === "ao3") return "AO3";
  return "文章";
}

function typeTagType(type: string): "success" | "info" | "warning" {
  if (type === "image") return "success";
  if (type === "ao3") return "info";
  return "warning";
}

async function copyPath(path: string) {
  try {
    await navigator.clipboard.writeText(path);
    message.success("路径已复制到剪贴板");
  } catch {
    notifyError("复制失败，请手动复制");
  }
}

function removeItem(id: string, title: string) {
  confirmDanger({
    title: "删除记录",
    content: `确定删除「${title}」这条下载记录吗？（不会删除已保存的文件）`,
    positiveText: "删除",
    onConfirm: async () => {
      try {
        await history.removeItem(id);
        message.success("记录已删除");
      } catch (e) {
        notifyError(e instanceof Error ? e.message : String(e));
      }
    },
  });
}

function clearAll() {
  confirmDanger({
    title: "清空下载历史",
    content: "确定清空全部下载历史吗？此操作不可恢复（不会删除已保存的文件）。",
    positiveText: "全部清空",
    onConfirm: async () => {
      try {
        await history.clearAll();
        message.success("历史记录已清空");
      } catch (e) {
        notifyError(e instanceof Error ? e.message : String(e));
      }
    },
  });
}
</script>

<template>
  <div class="panel-stack wide">
    <PageHeader icon="content_paste" title="下载历史" subtitle="查看与管理已下载的内容记录" />

    <div class="la-card toolbar">
      <NInput
        v-model:value="searchInput"
        placeholder="搜索标题、作者或链接..."
        clearable
        class="toolbar-search"
      >
        <template #prefix><span class="mi" aria-hidden="true">search</span></template>
      </NInput>
      <NSelect v-model:value="history.filterType" :options="typeOptions" class="toolbar-select" />
      <NSelect v-model:value="history.filterSource" :options="sourceOptions" class="toolbar-select" />
      <NButton type="error" secondary @click="clearAll">
        <template #icon><span class="mi" aria-hidden="true">delete_sweep</span></template>
        清空
      </NButton>
      <div class="toolbar-stats" aria-live="polite">
        共 {{ history.result.stats.total }} 条 · 图片 {{ history.result.stats.images }} · 文章
        {{ history.result.stats.articles }}
      </div>
    </div>

    <div class="la-card list-card">
      <div v-if="history.loading" class="list-loading">
        <NSpin size="medium" />
        <span>加载中...</span>
      </div>

      <NEmpty
        v-else-if="history.result.items.length === 0"
        :description="history.loadError ? history.loadError : '暂无下载记录，去下载一些内容吧'"
        class="list-empty"
      />

      <template v-else>
        <ul class="history-list">
          <li v-for="item in history.result.items" :key="item.id" class="history-item">
            <span class="mi item-type-icon" aria-hidden="true">
              {{ item.type === "image" ? "image" : item.type === "ao3" ? "auto_stories" : "edit_note" }}
            </span>
            <div class="item-main">
              <div class="item-title" :title="item.url">{{ item.title }}</div>
              <div class="item-meta">
                <NTag :type="typeTagType(item.type)" size="tiny" :bordered="false">{{ typeLabel(item.type) }}</NTag>
                <span>{{ item.author }}</span>
                <span>{{ item.download_time }}</span>
              </div>
            </div>
            <div class="item-actions">
              <NButton quaternary size="tiny" :title="'复制路径: ' + item.file_path" @click="copyPath(item.file_path)">
                <template #icon><span class="mi" style="font-size: 16px" aria-hidden="true">content_copy</span></template>
                复制路径
              </NButton>
              <NButton quaternary size="tiny" type="error" :aria-label="`删除 ${item.title}`" @click="removeItem(item.id, item.title)">
                <template #icon><span class="mi" style="font-size: 16px" aria-hidden="true">delete</span></template>
                删除
              </NButton>
            </div>
          </li>
        </ul>

        <div class="list-pagination">
          <NPagination
            :page="history.page"
            :page-count="history.result.total_pages"
            :page-size="history.perPage"
            @update:page="(p: number) => history.fetchPage(p)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.toolbar-search {
  flex: 1;
  min-width: 200px;
}

.toolbar-select {
  width: 130px;
}

.toolbar-stats {
  width: 100%;
  font-size: 12.5px;
  color: var(--la-text-muted);
}

.list-card {
  min-height: 300px;
}

.list-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
  color: var(--la-text-muted);
}

.list-empty {
  padding: 48px 0;
}

.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 520px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 8px;
  border-bottom: 1px solid var(--la-border);
}

.history-item:last-child {
  border-bottom: none;
}

.item-type-icon {
  font-size: 22px;
  color: var(--la-primary);
  flex-shrink: 0;
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-weight: 500;
  font-size: 13.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 3px;
  font-size: 12px;
  color: var(--la-text-muted);
}

.item-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.list-pagination {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}
</style>
