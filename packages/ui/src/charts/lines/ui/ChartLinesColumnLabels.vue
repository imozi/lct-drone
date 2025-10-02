<script setup lang="ts">
import { useInjectState } from '../composables/useInjectState';
const { state } = useInjectState();
</script>

<template>
  <div class="chart-lines-labels">
    <ul class="chart-lines-labels-list">
      <li class="chart-lines-label" v-for="label of state.columnLabels" :key="label">
        <p>{{ label }}</p>
      </li>
    </ul>
  </div>
</template>

<style lang="css" scoped>
.chart-lines-labels {
  display: grid;
  align-items: center;
  border-top: 1px dotted var(--color-gridlines);
  grid-column: 1/-1;
  grid-row: 2/3;
  grid-template-columns: subgrid;
}

.chart-lines-labels-list {
  display: grid;
  padding-top: 0.313rem;
  color: var(--color-column-labels);
  font-weight: 500;
  grid-column: 1/-1;
  grid-template-columns: subgrid;
  grid-template-rows: subgrid;
}
</style>
