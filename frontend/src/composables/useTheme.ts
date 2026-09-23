import { computed, ref, watchEffect } from "vue";

import { buildNaiveOverrides, CSS_VAR_MAPPING, THEMES, ThemeName } from "@/themes";

const STORAGE_KEY = "loarchive_theme";

const current = ref<ThemeName>(loadInitial());

function loadInitial(): ThemeName {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark" || saved === "bw") return saved;
  // 兼容旧版后端 dark_mode 偏好
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function setTheme(theme: ThemeName) {
  current.value = theme;
  localStorage.setItem(STORAGE_KEY, theme);
}

/** 把当前主题的令牌写入 :root CSS 变量 */
watchEffect(() => {
  const tokens = THEMES[current.value];
  const root = document.documentElement;
  root.dataset.theme = current.value;
  for (const [cssVar, tokenKey] of Object.entries(CSS_VAR_MAPPING)) {
    root.style.setProperty(cssVar, tokens[tokenKey]);
  }
});

export function useTheme() {
  const themeName = computed(() => current.value);
  const tokens = computed(() => THEMES[current.value]);
  const naive = computed(() => buildNaiveOverrides(THEMES[current.value]));
  return { themeName, tokens, naive, setTheme };
}
