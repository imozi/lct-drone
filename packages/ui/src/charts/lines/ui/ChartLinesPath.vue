<script setup lang="ts">
type ChartLinesPathProps = {
  coords: { start: { x: number; y: number } | { x: null; y: null }; end: { x: number; y: number } | { x: null; y: null } };
  color: string;
};
const { coords, color } = defineProps<ChartLinesPathProps>();
</script>

<template>
  <path
    v-if="coords.start.x !== null && coords.start.y !== null && coords.end.x !== null && coords.end.y !== null"
    class="chart-lines-path"
    :d="`M${coords.start.x} ${coords.start.y} L${coords.end.x} ${coords.end.y}`"
  ></path>
</template>

<style lang="css" scoped>
.chart-lines-path {
  stroke: v-bind(color);
  stroke-width: 2.5px;
}
</style>
