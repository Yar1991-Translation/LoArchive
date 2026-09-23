<script setup lang="ts">
import { NAlert, NButton, NInput } from "naive-ui";
import { computed, ref } from "vue";

import ModeSelect from "@/components/ModeSelect.vue";
import PageHeader from "@/components/PageHeader.vue";
import { notifyError, notifySuccess } from "@/services/feedback";
import { useSettingsStore } from "@/stores/settings";
import { useTaskStore } from "@/stores/task";
import { useUiStore } from "@/stores/ui";

const task = useTaskStore();
const settings = useSettingsStore();
const ui = useUiStore();

const modeOptions = [
  { value: "img", label: "保存图片", icon: "image" },
  { value: "txt", label: "保存文章", icon: "edit_note" },
];

const mode = ref("img");
const urlsText = ref("");
const starting = ref(false);

const showAuthHint = computed(() => !settings.config.has_auth);

function parseUrls(): string[] {
  return urlsText.value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

async function start() {
  const urls = parseUrls();
  if (urls.length === 0) {
    notifyError("请输入至少一个链接");
    return;
  }
  starting.value = true;
  try {
    await task.start(mode.value === "img" ? "single_img" : "single_txt", { urls });
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
    <PageHeader icon="attach_file" title="单篇保存" subtitle="精确保存单篇博客的图片或文章" />

    <NAlert v-if="showAuthHint" type="warning" :show-icon="true" closable>
      使用 Lofter 功能前需要先配置登录授权码。
      <NButton text type="primary" size="small" @click="ui.switchView('settings')">前往设置</NButton>
    </NAlert>

    <div class="la-card">
      <ModeSelect v-model="mode" :options="modeOptions" label="保存类型" />
    </div>

    <div class="la-card">
      <div class="form-row">
        <label for="single-urls">博客链接（每行一个）</label>
        <NInput
          id="single-urls"
          v-model:value="urlsText"
          type="textarea"
          :rows="5"
          placeholder="https://用户名.lofter.com/post/xxx&#10;https://用户名.lofter.com/post/yyy"
          :disabled="starting"
        />
      </div>

      <NButton type="primary" size="large" block :loading="starting" @click="start">
        <template #icon><span class="mi" aria-hidden="true">rocket_launch</span></template>
        开始保存
      </NButton>
    </div>
  </div>
</template>
