/** 界面状态：当前视图、侧边栏状态。 */

import { defineStore } from "pinia";
import { ref } from "vue";

export type ViewName = "lst" | "author-img" | "author-txt" | "single" | "ao3" | "history" | "settings";

export const useUiStore = defineStore("ui", () => {
  const currentView = ref<ViewName>("lst");
  const onboardingVisible = ref(false);

  function switchView(view: ViewName) {
    currentView.value = view;
  }

  return { currentView, onboardingVisible, switchView };
});
