<script setup lang="ts">
import { LayoutLoader, Loader } from '@lct/ui';
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { LayoutWrapper } from '@/components';

const route = useRoute();

const layoutKey = computed(() => route.meta.layout);
const pageKey = computed(() => route.fullPath);
</script>

<template>
  <Suspense :key="layoutKey">
    <transition name="layout" appear>
      <LayoutWrapper>
        <RouterView v-slot="{ Component }">
          <template v-if="Component">
            <Transition name="page">
              <Suspense :key="pageKey">
                <KeepAlive>
                  <component :is="Component" />
                </KeepAlive>

                <template #fallback>
                  <Loader />
                </template>
              </Suspense>
            </Transition>
          </template>
        </RouterView>
      </LayoutWrapper>
    </transition>

    <template #fallback>
      <LayoutLoader />
    </template>
  </Suspense>
</template>

<style lang="css">
.layout-enter-active,
.layout-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.layout-enter-from,
.layout-leave-to {
  opacity: 0;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
}
</style>
