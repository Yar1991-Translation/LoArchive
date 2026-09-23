/** 平台环境检测与原生能力封装（全应用唯一的 Tauri 判定来源）。 */

import { ref } from "vue";

function detectTauri(): boolean {
  return (
    typeof window !== "undefined" &&
    ((window as any).__TAURI_INTERNALS__ !== undefined ||
      (window as any).__TAURI__ !== undefined ||
      navigator.userAgent.includes("Tauri"))
  );
}

export const isTauri = ref(detectTauri());

/** 打开外部链接：Tauri 走 shell 插件，浏览器直接开新窗口 */
export async function openExternal(url: string): Promise<void> {
  const tauri = (window as any).__TAURI__;
  if (isTauri.value && tauri?.shell?.open) {
    await tauri.shell.open(url);
    return;
  }
  window.open(url, "_blank", "noopener");
}

/** 系统对话框选择文件夹；浏览器环境返回 null */
export async function pickFolder(defaultPath?: string): Promise<string | null> {
  const tauri = (window as any).__TAURI__;
  if (!isTauri.value || !tauri?.dialog) return null;
  const selected = await tauri.dialog.open({
    directory: true,
    multiple: false,
    defaultPath,
  });
  return typeof selected === "string" ? selected : null;
}

export function usePlatform() {
  return { isTauri, openExternal, pickFolder };
}
