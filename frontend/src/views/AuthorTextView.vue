<script setup lang="ts">
import { NAlert, NButton, NInput } from "naive-ui";
import { computed, ref } from "vue";

import PageHeader from "@/components/PageHeader.vue";
import { notifyError, notifySuccess } from "@/services/feedback";
import { useSettingsStore } from "@/stores/settings";
import { useTaskStore } from "@/stores/task";
import { useUiStore } from "@/stores/ui";

const task = useTaskStore();
const settings = useSettingsStore();
const ui = useUiStore();

const authorUrl = ref("");
const starting = ref(false);

const showAuthHint = computed(() => !settings.config.has_auth);

async function start() {
  if (!authorUrl.value.trim()) {
    notifyError("请输入作者主页链接");
    return;
  }
  starting.value = true;
  try {
    await task.start("author_txt", { author_url: authorUrl.value.trim() });
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
    <PageHeader icon="edit_note" title="作者文章" subtitle="下载指定作者的全部文章" />

    <NAlert v-if="showAuthHint" type="warning" :show-icon="true" closable>
      使用 Lofter 功能前需要先配置登录授权码。
      <NButton text type="primary" size="small" @click="ui.switchView('settings')">前往设置</NButton>
    </NAlert>

    <div class="la-card">
      <div class="form-row">
        <label for="author-txt-url">作者主页链接</label>
        <NInput
          id="author-txt-url"
          v-model:value="authorUrl"
          placeholder="https://用户名.lofter.com/"
          :disabled="starting"
        />
      </div>

      <NButton type="primary" size="large" block :loading="starting" @click="start">
        <template #icon><span class="mi" aria-hidden="true">rocket_launch</span></template>
        开始爬取
      </NButton>
    </div>
  </div>
</template>
