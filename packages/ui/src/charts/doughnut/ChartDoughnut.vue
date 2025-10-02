<script setup lang="ts">
import { computed, ref, useTemplateRef, watch } from 'vue';
import { useFormatNumber } from './composables/useFormatNumber';

export type DoughnutProps = {
  percent: number;
  color?: string;
  size?: number;
  degree?: number;
  difference?: number;
  description?: string;
};

const { color = '#7f22fe', percent = 0, size = 240, degree = 0, description, difference } = defineProps<DoughnutProps>();

const dasharray = ref<number>(0);
const dashoffset = computed(() => {
  return dasharray.value - (percent / 100) * dasharray.value;
});

const rotate = computed(() => `rotate(${degree}deg)`);
const formatPercent = computed(() => useFormatNumber(percent));
const diff = computed(() => {
  if (!difference) return null;

  return difference < 0 ? `${useFormatNumber(difference)}` : `+${useFormatNumber(difference)}`;
});
const chartDoughnutMetricRef = useTemplateRef('chartDoughnutMetricRef');

watch(chartDoughnutMetricRef, () => {
  const correctLength = 1;

  if (!chartDoughnutMetricRef.value) return;

  dasharray.value = chartDoughnutMetricRef.value.getTotalLength() + correctLength;
});
</script>

<template>
  <div class="chart-doughnut" ref="chartDoughnutRef">
    <div class="chart-doughnut-wrapper">
      <svg class="chart-doughnut-metrics" viewBox="0 0 100 100">
        <g class="chart-doughnut-segment-group">
          <circle cx="50" cy="50" class="chart-doughnut-segment chart-doughnut-background"></circle>
          <circle
            ref="chartDoughnutMetricRef"
            cx="50"
            cy="50"
            class="chart-doughnut-segment chart-doughnut-metric"
            :stroke-dasharray="dasharray"
            :stroke-dashoffset="dashoffset"
          ></circle>
        </g>
        <text class="chart-doughnut-percent" x="50" y="50" text-anchor="middle" dominant-baseline="middle">
          {{ formatPercent }}
        </text>
        <text
          v-if="diff"
          class="chart-doughnut-difference"
          :class="{ 'difference-negative': difference && difference < 0 }"
          x="50"
          y="65"
          text-anchor="middle"
          dominant-baseline="middle"
        >
          {{ diff }}
        </text>
      </svg>
    </div>
    <div class="chart-doughnut-description" v-if="description">
      <p>{{ description }}</p>
    </div>
  </div>
</template>

<style lang="css">
.chart-doughnut {
  --color: #303133;
  --color-negative: #e92c2c;
  --shadow: 0px 5px 20px 1px rgb(138 161 203 / 40%);
  --chart-doughnut-size: v-bind(size);
  --chart-doughnut-segment-stroke-default: 200;
  --chart-doughnut-segment-stroke: calc(var(--chart-doughnut-segment-stroke-default) * 0.0584);
  --chart-doughnut-segment-radius: calc(50 - var(--chart-doughnut-segment-stroke) / 2);

  display: flex;
  max-width: calc(var(--chart-doughnut-size) * 1px);
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color);
  fill: var(--color);
  font-family: inherit;
  font-weight: 600;
  gap: 0.625rem;
}

.chart-doughnut-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  max-height: calc(var(--chart-doughnut-size) * 1px);
}

.chart-doughnut-wrapper::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 1px;
  border-radius: 100%;
  background: transparent;
  box-shadow: var(--shadow);
  content: '';
}

.chart-doughnut-wrapper::after {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border: 1px;
  border-radius: 100%;
  background: transparent;
  box-shadow: inset var(--shadow);
  content: '';
  transform: translate(-50%, -50%) scale(calc(1 - 2 * var(--chart-doughnut-segment-stroke) / 100));
}

.chart-doughnut-segment-group {
  transform: v-bind(rotate);
  transform-origin: center;
}

.chart-doughnut-segment {
  fill: none;
  r: calc(var(--chart-doughnut-segment-radius) * 1%);
  stroke-width: calc(var(--chart-doughnut-segment-stroke) * 1%);
}

.chart-doughnut-background {
  stroke: #fff;
}

.chart-doughnut-metric {
  stroke: v-bind(color);
  transition: stroke-dashoffset 0.8s ease-in-out;
}

.chart-doughnut-percent {
  fill: inherit;
  font-size: 1rem;
}

.chart-doughnut-difference {
  fill: v-bind(color);
  font-size: 0.438rem;
}

.chart-doughnut-description {
  font-size: calc(var(--chart-doughnut-size) * 0.004vw);
}

.difference-negative {
  fill: var(--color-negative);
}
</style>
