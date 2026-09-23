<script setup lang="ts">
import { NConfigProvider, NMessageProvider, darkTheme, zhCN, dateZhCN } from "naive-ui";
import { computed, onMounted, ref } from "vue";

import AppSidebar from "@/components/AppSidebar.vue";
import AppTitlebar from "@/components/AppTitlebar.vue";
import OnboardingModal from "@/components/OnboardingModal.vue";
import TaskDock from "@/components/TaskDock.vue";
import { useTheme } from "@/composables/useTheme";
import { scheduleUpdateCheck } from "@/services/updater";
import { useSettingsStore } from "@/stores/settings";
import { useTaskStore } from "@/stores/task";
import { useUiStore } from "@/stores/ui";

import Ao3View from "@/views/Ao3View.vue";
import AuthorImageView from "@/views/AuthorImageView.vue";
import AuthorTextView from "@/views/AuthorTextView.vue";
import HistoryView from "@/views/HistoryView.vue";
import LstView from "@/views/LstView.vue";
import SettingsView from "@/views/SettingsView.vue";
import SingleView from "@/views/SingleView.vue";

const { naive } = useTheme();
const ui = useUiStore();
const task = useTaskStore();
const settings = useSettingsStore();

const onboardingVisible = ref(false);

const VIEWS = {
  lst: LstView,
  "author-img": AuthorImageView,
  "author-txt": AuthorTextView,
  single: SingleView,
  ao3: Ao3View,
  history: HistoryView,
  settings: SettingsView,
} as const;

const currentView = computed(() => VIEWS[ui.currentView]);

onMounted(() => {
  void task.syncFromBackend();
  void settings.loadAll();
  if (!localStorage.getItem("loarchive_onboarding_done")) {
    onboardingVisible.value = true;
  }
  scheduleUpdateCheck();
});
</script>

<template>
  <NConfigProvider
    :theme="naive.darkTheme ? darkTheme : null"
    :theme-overrides="naive.overrides"
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <NMessageProvider>
      <div class="app-shell">
        <AppTitlebar />
        <div class="app-body">
          <AppSidebar />
          <main class="app-main">
            <component :is="currentView" />
          </main>
        </div>
        <TaskDock />
        <OnboardingModal :show="onboardingVisible" @done="onboardingVisible = false" />
      </div>
    </NMessageProvider>
  </NConfigProvider>
</template>
