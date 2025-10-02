<script setup lang="ts">
import { useInjectState } from '../composables/useInjectState';
const { state } = useInjectState();
</script>

<template>
  <div class="chart-lines-gridlines">
    <div class="chart-lines-gridlines-item" v-for="gridline of state.gridlines" :key="gridline" :style="`--y-offset: ${gridline}%`"></div>
  </div>
</template>

<style lang="css" scoped>
.chart-lines-gridlines {
  position: relative;
  display: grid;
  grid-column: 2/-1;
  grid-row: 1/2;
}

.chart-lines-gridlines-item {
  position: absolute;
  top: var(--y-offset);
  right: 0;
  left: 0;
  height: 1px;
  border-bottom: 1px dotted var(--color-gridlines);
}
</style>
