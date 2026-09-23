<script setup lang="ts">
import { NAlert, NButton, NDatePicker, NInput } from "naive-ui";
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
const startTime = ref<string | null>(null);
const endTime = ref<string | null>(null);
const starting = ref(false);

const showAuthHint = computed(() => !settings.config.has_auth);

async function start() {
  if (!authorUrl.value.trim()) {
    notifyError("请输入作者主页链接");
    return;
  }
  starting.value = true;
  try {
    await task.start("author_img", {
      author_url: authorUrl.value.trim(),
      start_time: startTime.value ?? "",
      end_time: endTime.value ?? "",
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
    <PageHeader icon="image" title="作者图片" subtitle="下载指定作者的全部图片博客" />

    <NAlert v-if="showAuthHint" type="warning" :show-icon="true" closable>
      使用 Lofter 功能前需要先配置登录授权码。
      <NButton text type="primary" size="small" @click="ui.switchView('settings')">前往设置</NButton>
    </NAlert>

    <div class="la-card">
      <div class="form-row">
        <label for="author-img-url">作者主页链接</label>
        <NInput
          id="author-img-url"
          v-model:value="authorUrl"
          placeholder="https://用户名.lofter.com/"
          :disabled="starting"
        />
      </div>

      <div class="form-row">
        <label>时间范围（可选）</label>
        <div class="date-pair">
          <NDatePicker
            v-model:formatted-value="startTime"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            placeholder="开始时间"
            :disabled="starting"
          />
          <NDatePicker
            v-model:formatted-value="endTime"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            placeholder="结束时间"
            :disabled="starting"
          />
        </div>
      </div>

      <NButton type="primary" size="large" block :loading="starting" @click="start">
        <template #icon><span class="mi" aria-hidden="true">rocket_launch</span></template>
        开始爬取
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.date-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  max-width: 420px;
}
</style>
