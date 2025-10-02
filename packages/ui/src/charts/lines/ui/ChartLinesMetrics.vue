<script setup lang="ts">
import ChartLinesSegments from './ChartLinesSegments.vue';
import ChartLinesSegmentTooltip from './ChartLinesSegmentTooltip.vue';
</script>

<template>
  <div class="chart-lines-metrics" ref="metricsContainer">
    <ChartLinesSegments />
    <ChartLinesSegmentTooltip />
  </div>
</template>

<style lang="css" scoped>
.chart-lines-metrics {
  position: relative;
  grid-column: 2/-1;
  grid-row: 1/2;
}
</style>
