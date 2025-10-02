<script setup lang="ts">
import { useRoute } from 'vue-router';

import { useStatisticsStore, useRegionsStore, useRegionsGeneralStore } from '@/app/store';

const route = useRoute();

if (route.meta.layout === 'default') {
  await useRegionsGeneralStore().fetch();
  await useStatisticsStore().fetch();
  await useRegionsStore().fetch();
}
</script>

<template>
  <div class="portal-wrapper flex min-h-full flex-col">
    <header class="header"></header>
    <main class="main mx-auto flex max-w-[1880px] px-5">
      <slot />
    </main>
    <footer class="footer"></footer>
  </div>
</template>

<style lang="scss"></style>
