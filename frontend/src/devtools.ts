/** 仅开发构建加载的调试工具（import.meta.env.DEV 控制打包剔除）。 */

import { useTaskStore } from "@/stores/task";
import { useUiStore, type ViewName } from "@/stores/ui";

export function initDevtools() {
  if (!import.meta.env.DEV) return;

  (window as any).dev = {
    help() {
      console.log(`dev.switchPanel(view)  切换视图 (${VIEW_NAMES.join(", ")})
dev.state()           查看任务状态
dev.startTask(type)   启动测试任务（不填参数，仅后端报错）
dev.stopTask()        停止任务`);
    },
    switchPanel(view: ViewName) {
      useUiStore().switchView(view);
    },
    state() {
      return useTaskStore().$state;
    },
    async startTask(type: string) {
      await useTaskStore().start(type, {});
    },
    async stopTask() {
      await useTaskStore().stop();
    },
  };
  console.log("[LoArchive] 开发者模式可用：window.dev.help()");
}

const VIEW_NAMES: ViewName[] = ["lst", "author-img", "author-txt", "single", "ao3", "history", "settings"];
