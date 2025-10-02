<script setup lang="ts">
import { computed, useTemplateRef } from 'vue';

import { useInjectState } from '../composables/useInjectState';

const { state } = useInjectState();

const tooltip = useTemplateRef('tooltip');

const positionX = computed(() => {
  if (!tooltip.value || !state.computed.tooltip || !state.columnWidth) return;

  const rectTooltip = tooltip.value.getBoundingClientRect();

  const left = state.computed.tooltip.position.x - rectTooltip.width - state.columnWidth;
  const right = state.computed.tooltip.position.x + state.columnWidth;
  const isOutOfBoundsLeft = left < 0;

  return `--x-offset: ${isOutOfBoundsLeft ? right : left}px`;
});
</script>

<template>
  <Transition name="tooltip">
    <div class="chart-lines-segment-tooltip" v-if="state.computed.tooltip" :style="positionX" ref="tooltip">
      <div class="chart-lines-segment-tooltip-name">
        <p>{{ state.computed.tooltip.name }}</p>
      </div>
      <ul class="chart-lines-segment-tooltip-list">
        <li
          class="chart-lines-segment-tooltip-list-item"
          v-for="metric of state.computed.tooltip.metrics"
          :key="metric.name"
          :style="`--accent: ${metric.color}`"
        >
          <p>{{ metric.name }}</p>
          <span v-if="metric.percent !== null" :class="{ negative: metric.percent < 0 }"> {{ metric.percent }}</span>
          <span v-else class="chart-lines-segment-tooltip-empty">-</span>
        </li>
      </ul>
    </div>
  </Transition>
</template>

<style lang="css" scoped>
.chart-lines-segment-tooltip {
  position: absolute;
  z-index: 10;
  top: 50%;
  left: var(--x-offset);
  display: flex;
  max-width: 300px;
  flex-direction: column;
  padding: 1.25rem 1.563rem;
  border-radius: 0.75rem;
  background-color: #fff;
  box-shadow: var(--tooltip-shadow);
  gap: 1rem;
  transform: translateY(-50%);
}

.chart-lines-segment-tooltip-name {
  font-size: 1rem;
  font-weight: 700;
}

.chart-lines-segment-tooltip-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.chart-lines-segment-tooltip-list-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  line-height: 1;
}

.chart-lines-segment-tooltip-empty {
  color: var(--color-empty);
}

.chart-lines-segment-tooltip-list-item span {
  margin-left: auto;
}

.chart-lines-segment-tooltip-list-item span.negative {
  color: var(--color-negative);
}

.chart-lines-segment-tooltip-list-item::before {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 100%;
  background-color: var(--accent);
  content: '';
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.3s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(-55%);
}
</style>
