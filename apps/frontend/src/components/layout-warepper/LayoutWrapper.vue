<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const layouts = {
  default: defineAsyncComponent(() => import('@/layouts').then((module) => module.Default)),
  auth: defineAsyncComponent(() => import('@/layouts').then((module) => module.Auth)),
  load: defineAsyncComponent(() => import('@/layouts').then((module) => module.Load)),
};

const layoutComponent = computed(() => {
  const layoutName = (route.meta.layout as keyof typeof layouts) || 'default';
  return layouts[layoutName] || layouts.default;
});
</script>

<template>
  <component :is="layoutComponent">
    <slot />
  </component>
</template>

<style lang="scss"></style>
