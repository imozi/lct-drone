<script setup lang="ts">
import { useId } from 'vue';

import { useInjectState } from '../composables/useInjectState';

const { state } = useInjectState();
</script>

<template>
  <div class="chart-lines-axiss">
    <div v-for="axis of state.axis" :key="`${axis}-${useId()}`" class="chart-lines-axiss-item">
      <p>{{ `${axis}`.includes('e') ? 0 : axis }}</p>
    </div>
  </div>
</template>

<style lang="css" scoped>
.chart-lines-axiss {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 0.625rem;
  color: var(--color-axiss);
  font-weight: 500;
  grid-column: 1/2;
  grid-row: 1/2;
}

.chart-lines-axiss-item {
  height: 1px;
}

.chart-lines-axiss-item p {
  text-align: right;
  transform: translateY(-50%);
}
</style>
