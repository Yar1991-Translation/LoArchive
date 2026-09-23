/** 后端配置（登录授权）与应用设置。 */

import { defineStore } from "pinia";
import { ref } from "vue";

import * as api from "@/api";
import type { AppConfig, AppSettings } from "@/api/types";
import { notifyError, notifySuccess } from "@/services/feedback";

export const useSettingsStore = defineStore("settings", () => {
  const config = ref<AppConfig>({ login_key: "LOFTER-PHONE-LOGIN-AUTH", login_auth: "", has_auth: false, file_path: "./dir" });
  const settings = ref<AppSettings>({ save_path: "./dir", auto_dedup: true, notify_on_complete: true });
  /** 后端不可达（设置页显示离线与重试状态） */
  const backendDown = ref(false);

  async function loadAll() {
    try {
      const [cfg, st] = await Promise.all([api.getConfig(), api.getSettings()]);
      config.value = cfg;
      settings.value = st;
      backendDown.value = false;
    } catch (e) {
      backendDown.value = true;
    }
  }

  async function saveLogin(loginKey: string, loginAuth: string) {
    const result = await api.saveConfig({ login_key: loginKey, login_auth: loginAuth });
    // 重新拉取以拿到遮蔽后的授权码与 has_auth
    config.value = await api.getConfig();
    notifySuccess(result.message);
  }

  async function saveSettings(patch: Partial<AppSettings>) {
    try {
      const result = await api.saveSettings(patch);
      settings.value = await api.getSettings();
      backendDown.value = false;
      notifySuccess(result.message);
    } catch (e) {
      notifyError(e instanceof Error ? e.message : String(e));
      throw e;
    }
  }

  return { config, settings, backendDown, loadAll, saveLogin, saveSettings };
});
