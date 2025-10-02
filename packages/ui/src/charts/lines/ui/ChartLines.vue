<script setup lang="ts">
import { useTemplateRef } from 'vue';

import ChartLinesAxiss from './ChartLinesAxiss.vue';
import ChartLinesColumnLabels from './ChartLinesColumnLabels.vue';
import ChartLinesColumns from './ChartLinesColumns.vue';
import ChartLinesFilter from './ChartLinesFilter.vue';
import ChartLinesGridlines from './ChartLinesGridlines.vue';
import ChartLinesLegends from './ChartLinesLegends.vue';
import ChartLinesMetrics from './ChartLinesMetrics.vue';
import { useMouseCoords } from '../composables/useMouseCoords';
import { useProvideState } from '../composables/useProvideState';
import { useThrottle } from '../composables/useThrottle';

import type { InitialValue } from '../types';

export type ChartLinesProps = InitialValue;

const { chartData } = defineProps<{ chartData: ChartLinesProps }>();

const store = useProvideState(chartData);

const metricsContainer = useTemplateRef('metricsContainer');

const throttledMouseMove = useThrottle((evt: MouseEvent) => {
  store.actions.updateMouseCoords(useMouseCoords({ evt, container: metricsContainer.value?.$el }));
}, 100);

const resetMouseCoordinates = () => {
  store.actions.resetMouseCoords();
};
const resetHoveredSegment = () => {
  store.actions.resetHoveredSegment();
};

const handleMouseLeave = () => {
  resetMouseCoordinates();
  resetHoveredSegment();
};
</script>

<template>
  <div class="chart-lines">
    <slot>
      <ChartLinesFilter />
    </slot>

    <div class="chart-lines-wrapper">
      <div class="chart-lines-inner">
        <ChartLinesAxiss />
        <ChartLinesGridlines />
        <ChartLinesColumns />
        <ChartLinesMetrics ref="metricsContainer" @mousemove="throttledMouseMove" @mouseleave="handleMouseLeave" />
        <div class="chart-lines-bottom">
          <ChartLinesColumnLabels />
          <ChartLinesLegends />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="css" scoped>
.chart-lines {
  --columns: v-bind(store.state.columns);
  --top-indent: 1.875rem;
  --bottom-indent: 0.5rem;
  --color-gridlines: #a9b7cd;
  --color-axiss: #a9b7cd;
  --color-column-visible: #a9b7cd;
  --color-column-labels: #a9b7cd;
  --color-legend: #f3f5f9;
  --color-black: #303133;
  --color-negative: #e92c2c;
  --color-empty: #a9b7cd;
  --tooltip-shadow: 0px 10px 50px 4px rgb(138 161 203 / 23%);

  display: flex;
  flex-direction: column;
  row-gap: 1.25rem;
}

.chart-lines-wrapper {
  display: grid;
  min-width: 600px;
  min-height: 400px;
  padding: 0 2rem 1.5rem;
  border-radius: 1.25rem;
  background-color: #fff;
  font-family: inherit;
  font-size: inherit;
}

.chart-lines-inner {
  display: grid;
  padding-top: var(--top-indent);
  grid-template-columns: 60px repeat(var(--columns), 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.chart-lines-bottom {
  display: grid;
  grid-column: 2/-1;
  grid-row: 2/3;
  grid-template-columns: subgrid;
  grid-template-rows: repeat(4, 1fr);
  text-align: center;
}
</style>
