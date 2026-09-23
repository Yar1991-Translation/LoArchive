/** 全局通知与确认对话框（discrete API，无需组件上下文即可调用）。 */

import { createDiscreteApi, darkTheme } from "naive-ui";
import { computed } from "vue";

import { useTheme } from "@/composables/useTheme";

const { naive } = useTheme();

const configProviderProps = computed(() => ({
  theme: naive.value.darkTheme ? darkTheme : null,
  themeOverrides: naive.value.overrides,
}));

export const { message, notification, dialog } = createDiscreteApi(
  ["message", "notification", "dialog"],
  { configProviderProps },
);

export function notifySuccess(text: string) {
  message.success(text);
}

export function notifyError(text: string) {
  message.error(text);
}

export function notifyInfo(text: string) {
  message.info(text);
}

/** 危险操作确认对话框 */
export function confirmDanger(options: {
  title: string;
  content: string;
  positiveText?: string;
  onConfirm: () => void | Promise<void>;
}) {
  dialog.warning({
    title: options.title,
    content: options.content,
    positiveText: options.positiveText ?? "确认",
    negativeText: "取消",
    onPositiveClick: () => options.onConfirm(),
  });
}
