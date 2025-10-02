<script setup lang="ts">
import ChartLinesPath from './ChartLinesPath.vue';
import ChartLinesPoint from './ChartLinesPoint.vue';
import { useInjectState } from '../composables/useInjectState';

const { state } = useInjectState();
</script>

<template>
  <TransitionGroup
    name="segments"
    tag="svg"
    class="chart-lines-segments"
    :class="{
      'chart-lines-segments-active': state.reactive.highlightSegment,
    }"
  >
    <g
      v-for="segment of state.computed.segments"
      :key="segment.id"
      class="chart-lines-segments-group"
      :data-segment="segment.name"
      :class="{
        'chart-lines-segments-group-active': state.reactive.highlightSegment === segment.name,
      }"
    >
      <ChartLinesPath v-for="(coords, j) of segment.pathCoords" :key="`${segment.id}-path-${j}`" :coords="coords" :color="segment.color" />

      <ChartLinesPoint
        v-for="(coords, j) of segment.pointCoords"
        :key="`${segment.id}-point-${j}`"
        :cx="coords.x"
        :cy="coords.y"
        :color="segment.color"
        :hovered="state.reactive.hoveredSegment?.id === j"
      />
    </g>
  </TransitionGroup>
</template>

<style lang="css" scoped>
.chart-lines-segments {
  position: absolute;
  top: 0;
  left: 0;
  overflow: visible;
  width: 100%;
  height: 100%;
}

.chart-lines-segments-group {
  transition: opacity 0.4s ease;
}

.chart-lines-segments.chart-lines-segments-active .chart-lines-segments-group:not(.chart-lines-segments-group-active) {
  opacity: 0.1;
}

.segments-enter-active,
.segments-leave-active {
  transition: all 0.4s ease;
}

.segments-enter-from,
.segments-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
