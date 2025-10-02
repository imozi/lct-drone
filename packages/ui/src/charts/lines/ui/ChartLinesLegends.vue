<script setup lang="ts">
import { useInjectState } from '../composables/useInjectState';
const { state, actions } = useInjectState();

const mouseEnterHandler = (name: string) => {
  actions.updateHighlightSegment(name);
};

const mouseLeaveHandler = () => {
  actions.resetHighlightSegment();
};
</script>

<template>
  <div class="chart-lines-legends">
    <TransitionGroup name="legends" tag="ul" class="chart-lines-legends-list">
      <template v-if="state.reactive.filterLegends.length < 11">
        <li
          class="chart-lines-legends-item"
          v-for="legend of state.reactive.filterLegends"
          :style="`--chart-lines-legend: ${legend.color}`"
          :key="legend.name"
          @mouseenter="mouseEnterHandler(legend.name)"
          @mouseleave="mouseLeaveHandler"
        >
          {{ legend.name }}
        </li>
      </template>
      <template v-else>
        <li
          class="chart-lines-legends-item"
          v-for="legend of state.reactive.filterLegends.slice(0, 11)"
          :style="`--chart-lines-legend: ${legend.color}`"
          :key="legend.name"
          @mouseenter="mouseEnterHandler(legend.name)"
          @mouseleave="mouseLeaveHandler"
        >
          {{ legend.name }}
        </li>
        <li class="chart-lines-legends-item" :style="`--chart-lines-legend: #94a3b8`">
          +{{ state.reactive.filterLegends.slice(11, state.reactive.filterLegends.length).length }}
        </li>
      </template>
    </TransitionGroup>
  </div>
</template>

<style lang="css" scoped>
.chart-lines-legends {
  display: flex;
  align-items: center;
  justify-content: center;
  grid-column: 1/-1;
  grid-row: 3/5;
}

.chart-lines-legends-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  color: var(--color-black);
  gap: 0.313rem;
}

.chart-lines-legends-item {
  display: flex;
  align-items: center;
  padding: 0.313rem 0.625rem;
  border-radius: 0.375rem;
  cursor: default;
  gap: 0.5rem;
  transition: background-color 0.5s ease;
}

.chart-lines-legends-item:hover {
  background-color: var(--color-legend);
}

.chart-lines-legends-item::before {
  width: 0.75rem;
  height: 0.75rem;
  flex-shrink: 0;
  border-radius: 100%;
  background-color: var(--chart-lines-legend);
  content: '';
}

.legends-move,
.legends-enter-active,
.legends-leave-active {
  transition: all 0.3s ease;
}

.legends-enter-from,
.legends-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.legends-leave-active {
  position: absolute;
}
</style>
