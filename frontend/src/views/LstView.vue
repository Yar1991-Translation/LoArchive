<script setup lang="ts">
import { NAlert, NButton, NCheckbox, NDatePicker, NInput } from "naive-ui";
import { computed, reactive, ref } from "vue";

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
  { value: "like2", label: "我的喜欢", icon: "favorite" },
  { value: "share", label: "我的推荐", icon: "outbox" },
  { value: "tag", label: "Tag 内容", icon: "sell" },
];

const mode = ref("like2");
const url = ref("");
const startTime = ref<string | null>(null);
const exportingPdf = ref(false);
const saveMode = reactive({ img: true, article: true, text: true, longArticle: true });
const starting = ref(false);

const showAuthHint = computed(() => !settings.config.has_auth);

function validate(): string | null {
  if (!url.value.trim()) return "请输入链接地址";
  if (!saveMode.img && !saveMode.article && !saveMode.text && !saveMode.longArticle) {
    return "请至少选择一种保存内容";
  }
  return null;
}

async function start() {
  const problem = validate();
  if (problem) {
    notifyError(problem);
    return;
  }
  starting.value = true;
  try {
    await task.start("like_share_tag", {
      url: url.value.trim(),
      mode: mode.value,
      save_mode: {
        img: saveMode.img ? 1 : 0,
        article: saveMode.article ? 1 : 0,
        text: saveMode.text ? 1 : 0,
        "long article": saveMode.longArticle ? 1 : 0,
      },
      start_time: startTime.value ?? "",
      export_pdf: exportingPdf.value,
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
    <PageHeader icon="favorite" title="喜欢 / 推荐 / Tag" subtitle="批量保存 Lofter 收藏、推荐与 Tag 内容" />

    <NAlert v-if="showAuthHint" type="warning" :show-icon="true" closable>
      使用 Lofter 功能前需要先配置登录授权码。
      <NButton text type="primary" size="small" @click="ui.switchView('settings')">前往设置</NButton>
    </NAlert>

    <div class="la-card">
      <ModeSelect v-model="mode" :options="modeOptions" label="爬取模式" />
    </div>

    <div class="la-card">
      <div class="form-row">
        <label for="lst-url">链接地址</label>
        <NInput
          id="lst-url"
          v-model:value="url"
          placeholder="https://你的用户名.lofter.com/ 或 Tag 链接"
          :disabled="starting"
        />
        <p class="form-hint">
          <span class="mi" aria-hidden="true">lightbulb</span>
          喜欢/推荐模式填写个人主页链接，Tag 模式填写 Tag 页面链接
        </p>
      </div>

      <div class="form-row">
        <label>保存内容</label>
        <div class="check-line">
          <NCheckbox v-model:checked="saveMode.img" :disabled="starting">图片</NCheckbox>
          <NCheckbox v-model:checked="saveMode.article" :disabled="starting">文章</NCheckbox>
          <NCheckbox v-model:checked="saveMode.text" :disabled="starting">文本</NCheckbox>
          <NCheckbox v-model:checked="saveMode.longArticle" :disabled="starting">长文章</NCheckbox>
          <NCheckbox v-model:checked="exportingPdf" :disabled="starting">导出 PDF</NCheckbox>
        </div>
      </div>

      <div class="form-row">
        <label for="lst-start-time">开始时间（可选）</label>
        <NDatePicker
          id="lst-start-time"
          v-model:formatted-value="startTime"
          type="date"
          value-format="yyyy-MM-dd"
          clearable
          :style="{ maxWidth: '280px' }"
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

<style scoped>
.check-line {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}
</style>
