<script setup lang="ts">
defineProps<{
  icon: string;
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <header class="page-header">
    <div class="page-header-icon">
      <span class="mi mi-filled" aria-hidden="true">{{ icon }}</span>
    </div>
    <div>
      <h2 class="page-header-title">{{ title }}</h2>
      <p v-if="subtitle" class="page-header-sub">{{ subtitle }}</p>
    </div>
  </header>
</template>
