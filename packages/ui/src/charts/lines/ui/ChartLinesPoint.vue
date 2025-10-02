<script setup lang="ts">
type ChartLinesPointProps = {
  cx: number | null;
  cy: number | null;
  color: string;
  hovered: boolean;
};
const { cx, cy, hovered } = defineProps<ChartLinesPointProps>();
</script>

<template>
  <g v-if="cx !== null && cy !== null" class="chart-lines-point" :class="{ 'chart-lines-point-hovered': hovered }">
    <circle class="chart-lines-point-border" :cx="`${cx}`" :cy="`${cy}`" r="6"></circle>
    <circle class="chart-lines-point-fill" :cx="`${cx}`" :cy="`${cy}`" r="4"></circle>
  </g>
</template>

<style lang="css" scoped>
.chart-lines-point-border {
  fill: transparent;
  transition: fill 0.3s ease;
}

.chart-lines-point-fill {
  fill: v-bind(color);
  transition: fill 0.3s ease;
}

.chart-lines-point.chart-lines-point-hovered .chart-lines-point-border {
  fill: v-bind(color);
}

.chart-lines-point.chart-lines-point-hovered .chart-lines-point-fill {
  fill: #fff;
}
</style>
