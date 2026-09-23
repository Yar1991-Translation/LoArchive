<script setup lang="ts">
import { NButton, NInput, NSelect, NSwitch } from "naive-ui";
import { onMounted, ref } from "vue";

import PageHeader from "@/components/PageHeader.vue";
import { isTauri, pickFolder } from "@/composables/usePlatform";
import { useTheme } from "@/composables/useTheme";
import { fetchCurrentVersion, checkForUpdates } from "@/services/updater";
import { notifyError, notifyInfo, notifySuccess } from "@/services/feedback";
import { useSettingsStore } from "@/stores/settings";

const settings = useSettingsStore();
const { themeName, setTheme } = useTheme();

const loginKey = ref("LOFTER-PHONE-LOGIN-AUTH");
const loginAuth = ref("");
const hasAuth = ref(false);
const savePathInput = ref("");
const version = ref("");
const checkingUpdate = ref(false);
const savingLogin = ref(false);

const loginKeyOptions = [
  { label: "手机号登录", value: "LOFTER-PHONE-LOGIN-AUTH" },
  { label: "Lofter ID 登录", value: "Authorization" },
  { label: "QQ/微信/微博登录", value: "LOFTER_SESS" },
  { label: "邮箱登录", value: "NTES_SESS" },
];

const themeOptions = [
  { value: "light", label: "默认", icon: "light_mode" },
  { value: "dark", label: "深色", icon: "dark_mode" },
  { value: "bw", label: "黑白块", icon: "contrast" },
] as const;

onMounted(async () => {
  await settings.loadAll();
  loginKey.value = settings.config.login_key;
  hasAuth.value = settings.config.has_auth;
  if (settings.config.has_auth) {
    loginAuth.value = settings.config.login_auth; // 后端遮蔽后的值
  }
  savePathInput.value = settings.settings.save_path;
  version.value = await fetchCurrentVersion();
});

async function onSaveLogin() {
  if (!loginAuth.value.trim()) {
    notifyError("请填写授权码");
    return;
  }
  savingLogin.value = true;
  try {
    await settings.saveLogin(loginKey.value, loginAuth.value.trim());
    hasAuth.value = settings.config.has_auth;
    loginAuth.value = settings.config.login_auth;
  } catch (e) {
    notifyError(e instanceof Error ? e.message : String(e));
  } finally {
    savingLogin.value = false;
  }
}

async function onBrowse() {
  const picked = await pickFolder(savePathInput.value);
  if (picked) savePathInput.value = picked;
}

async function onSavePath() {
  if (!savePathInput.value.trim()) {
    notifyError("请填写保存路径");
    return;
  }
  await settings.saveSettings({ save_path: savePathInput.value.trim() });
  savePathInput.value = settings.settings.save_path;
}

async function onToggleDedup(value: boolean) {
  await settings.saveSettings({ auto_dedup: value });
}

async function onToggleNotify(value: boolean) {
  await settings.saveSettings({ notify_on_complete: value });
}

async function onCheckUpdate() {
  checkingUpdate.value = true;
  try {
    await checkForUpdates(true);
  } finally {
    checkingUpdate.value = false;
  }
}
</script>

<template>
  <div class="panel-stack">
    <PageHeader icon="settings" title="设置" subtitle="登录配置、存储路径与应用偏好" />

    <section class="la-card">
      <h3 class="section-title"><span class="mi" aria-hidden="true">key</span> 登录配置</h3>
      <div class="form-row">
        <label for="login-key">登录方式</label>
        <NSelect id="login-key" v-model:value="loginKey" :options="loginKeyOptions" :style="{ maxWidth: '320px' }" />
      </div>
      <div class="form-row">
        <label for="login-auth">授权码</label>
        <NInput
          id="login-auth"
          v-model:value="loginAuth"
          type="textarea"
          :rows="3"
          :placeholder="hasAuth ? '已配置（输入新值可覆盖）' : '从浏览器开发者工具获取'"
        />
        <p class="form-hint">
          <span class="mi" aria-hidden="true">lightbulb</span>
          打开 Lofter → F12 → Application → Cookies → 找到对应 Cookie 的值
        </p>
      </div>
      <NButton type="primary" :loading="savingLogin" @click="onSaveLogin">
        <template #icon><span class="mi" aria-hidden="true">save</span></template>
        保存配置
      </NButton>
    </section>

    <section class="la-card">
      <h3 class="section-title"><span class="mi" aria-hidden="true">folder</span> 存储设置</h3>
      <div class="form-row">
        <label for="save-path">保存路径</label>
        <div class="path-row">
          <NInput id="save-path" v-model:value="savePathInput" placeholder="./dir" />
          <NButton v-if="isTauri" @click="onBrowse">
            <template #icon><span class="mi" aria-hidden="true">folder_open</span></template>
            浏览
          </NButton>
          <NButton type="primary" @click="onSavePath">
            <template #icon><span class="mi" aria-hidden="true">save</span></template>
            保存
          </NButton>
        </div>
        <p class="form-hint">
          <span class="mi" aria-hidden="true">lightbulb</span>
          支持相对路径（如 ./dir）或绝对路径（如 D:\Downloads）
        </p>
      </div>
    </section>

    <section class="la-card">
      <h3 class="section-title"><span class="mi" aria-hidden="true">palette</span> 外观设置</h3>
      <div class="form-row">
        <label id="theme-label">主题风格</label>
        <div class="theme-grid" role="radiogroup" aria-labelledby="theme-label">
          <button
            v-for="option in themeOptions"
            :key="option.value"
            type="button"
            class="theme-card"
            :class="{ selected: themeName === option.value }"
            role="radio"
            :aria-checked="themeName === option.value"
            @click="setTheme(option.value)"
          >
            <span class="mi theme-icon" aria-hidden="true">{{ option.icon }}</span>
            <span>{{ option.label }}</span>
          </button>
        </div>
      </div>
      <div class="setting-line">
        <div>
          <label class="setting-label">自动去重</label>
          <p class="form-hint">跳过已下载过的内容</p>
        </div>
        <NSwitch :value="settings.settings.auto_dedup" @update:value="onToggleDedup" />
      </div>
      <div class="setting-line">
        <div>
          <label class="setting-label">完成通知</label>
          <p class="form-hint">任务完成时弹出通知</p>
        </div>
        <NSwitch :value="settings.settings.notify_on_complete" @update:value="onToggleNotify" />
      </div>
    </section>

    <section class="la-card">
      <h3 class="section-title"><span class="mi" aria-hidden="true">sync</span> 软件更新</h3>
      <div class="setting-line">
        <div>
          <label class="setting-label">版本信息</label>
          <p class="form-hint">当前版本 v{{ version || "..." }}</p>
        </div>
        <NButton :loading="checkingUpdate" @click="onCheckUpdate">
          <template #icon><span class="mi" aria-hidden="true">search</span></template>
          检查更新
        </NButton>
      </div>
      <p class="form-hint">
        <span class="mi" aria-hidden="true">lightbulb</span>
        应用启动时会自动检查更新，也可以点击按钮手动检查
      </p>
    </section>

    <section class="la-card">
      <h3 class="section-title"><span class="mi" aria-hidden="true">menu_book</span> 使用说明</h3>
      <ol class="help-list">
        <li>首次使用请先在上方配置登录信息</li>
        <li>从左侧选择对应的爬取功能</li>
        <li>填写链接后点击开始按钮</li>
        <li>下载进度与日志显示在底部任务坞，完成后可在下载历史中查看</li>
        <li>AO3 功能无需配置登录信息</li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  margin: 0 0 16px;
}

.section-title .mi {
  color: var(--la-primary);
  font-size: 19px;
}

.path-row {
  display: flex;
  gap: 10px;
}

.path-row .n-input {
  flex: 1;
}

.theme-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.theme-card {
  width: 108px;
  padding: 14px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  border: 1.5px solid var(--la-border);
  border-radius: var(--la-radius);
  background: var(--la-surface);
  color: var(--la-text-secondary);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease;
}

.theme-card:hover {
  border-color: var(--la-border-strong);
}

.theme-card.selected {
  border-color: var(--la-primary);
  color: var(--la-primary);
}

.theme-icon {
  font-size: 22px;
}

.setting-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
}

.setting-line + .setting-line {
  border-top: 1px solid var(--la-border);
}

.setting-label {
  font-weight: 600;
  font-size: 13.5px;
}

.help-list {
  margin: 0;
  padding-left: 20px;
  color: var(--la-text-secondary);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
