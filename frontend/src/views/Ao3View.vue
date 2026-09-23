<script setup lang="ts">
import { NButton, NCheckbox, NInput, NInputNumber } from "naive-ui";
import { ref } from "vue";

import ModeSelect from "@/components/ModeSelect.vue";
import PageHeader from "@/components/PageHeader.vue";
import { notifyError, notifySuccess } from "@/services/feedback";
import { useTaskStore } from "@/stores/task";

const task = useTaskStore();

const modeOptions = [
  { value: "work", label: "单篇作品", icon: "menu_book" },
  { value: "series", label: "系列", icon: "auto_stories" },
  { value: "author", label: "作者", icon: "person" },
  { value: "tag", label: "Tag", icon: "sell" },
];

const mode = ref("work");
const urlsText = ref("");
const maxPages = ref<number | null>(5);
const downloadChapters = ref(true);
const saveMetadata = ref(true);
const exportPdf = ref(false);
const exportEpub = ref(false);
const starting = ref(false);

function parseUrls(): string[] {
  return urlsText.value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

async function start() {
  const urls = parseUrls();
  if (urls.length === 0) {
    notifyError("请输入至少一个 AO3 链接");
    return;
  }
  starting.value = true;
  try {
    await task.start("ao3", {
      urls,
      mode: mode.value,
      download_chapters: downloadChapters.value,
      save_metadata: saveMetadata.value,
      export_pdf: exportPdf.value,
      export_epub: exportEpub.value,
      max_pages: maxPages.value ?? 5,
    });
    notifySuccess("任务已启动");
  } catch (e) {
    notifyError(e instanceof Error ? e.message : String(e));
  } finally {
    starting.value = false;
  }
}
</script>

<template>
  <div class="panel-stack">
    <PageHeader icon="auto_stories" title="AO3 文章" subtitle="下载 AO3 作品，支持 PDF / EPUB 导出，无需登录" />

    <div class="la-card">
      <ModeSelect v-model="mode" :options="modeOptions" label="下载模式" />
    </div>

    <div class="la-card">
      <div class="form-row">
        <label for="ao3-urls">AO3 链接（每行一个）</label>
        <NInput
          id="ao3-urls"
          v-model:value="urlsText"
          type="textarea"
          :rows="4"
          placeholder="https://archiveofourown.org/works/12345678"
          :disabled="starting"
        />
      </div>

      <div class="form-row">
        <label for="ao3-max-pages">最大页数</label>
        <NInputNumber
          id="ao3-max-pages"
          v-model:value="maxPages"
          :min="1"
          :max="50"
          :style="{ maxWidth: '160px' }"
          :disabled="starting"
        />
        <p class="form-hint">
          <span class="mi" aria-hidden="true">lightbulb</span>
          用于 Tag / 作者模式，限制爬取的页数
        </p>
      </div>

      <div class="form-row">
        <label>下载选项</label>
        <div class="check-line">
          <NCheckbox v-model:checked="downloadChapters" :disabled="starting">全部章节</NCheckbox>
          <NCheckbox v-model:checked="saveMetadata" :disabled="starting">元数据</NCheckbox>
          <NCheckbox v-model:checked="exportPdf" :disabled="starting">导出 PDF</NCheckbox>
          <NCheckbox v-model:checked="exportEpub" :disabled="starting">导出 EPUB</NCheckbox>
        </div>
      </div>

      <NButton type="primary" size="large" block :loading="starting" @click="start">
        <template #icon><span class="mi" aria-hidden="true">rocket_launch</span></template>
        开始下载
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.check-line {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}
</style>
