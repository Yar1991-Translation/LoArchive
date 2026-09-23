<script setup lang="ts">
/** 模式选择卡片组（取代旧版三段复制的 mode-card 循环）。 */

interface ModeOption {
  value: string;
  label: string;
  icon: string;
}

defineProps<{
  options: ModeOption[];
  /** 无障碍名 */
  label: string;
}>();

const model = defineModel<string>({ required: true });
</script>

<template>
  <div class="mode-grid" role="radiogroup" :aria-label="label">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="mode-card"
      :class="{ selected: model === option.value }"
      role="radio"
      :aria-checked="model === option.value"
      @click="model = option.value"
    >
      <span class="mi mode-icon" aria-hidden="true">{{ option.icon }}</span>
      <span class="mode-name">{{ option.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.mode-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.mode-card {
  flex: 1;
  min-width: 130px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  border: 1.5px solid var(--la-border);
  border-radius: var(--la-radius);
  background: var(--la-surface);
  color: var(--la-text-secondary);
  font: inherit;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.mode-card:hover {
  border-color: var(--la-border-strong);
  transform: translateY(-1px);
}

.mode-card.selected {
  border-color: var(--la-primary);
  background: color-mix(in srgb, var(--la-primary) 8%, var(--la-surface));
  color: var(--la-primary);
}

.mode-card.selected .mode-icon {
  color: var(--la-primary);
}

.mode-icon {
  font-size: 24px;
}

.mode-name {
  font-size: 13.5px;
  font-weight: 600;
}

[data-theme="bw"] .mode-card.selected {
  border-width: 2.5px;
  background: var(--la-surface);
  color: #000;
  box-shadow: 3px 3px 0 #000;
}
</style>
