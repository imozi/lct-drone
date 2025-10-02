<script setup lang="ts">
import { ref, useTemplateRef, watch } from 'vue';

import { useElementBounds } from '../composables/useElementBounds';
import { useInjectState } from '../composables/useInjectState';
import { useIsMouseInside } from '../composables/useIsMouseInside';

type ColumnProps = {
  name: string;
  columnIndex: number;
};

const { state, actions } = useInjectState();
const { columnIndex, name } = defineProps<ColumnProps>();

const columnRef = useTemplateRef('columnRef');
const isActive = ref<boolean>(false);

const setActive = () => {
  isActive.value = true;
};

const setInactive = () => {
  isActive.value = false;
};

const toggleActive = () => {
  if (!columnRef.value || !columnRef.value.parentNode || !state.computed.segments?.length) return;
  const parentNode = columnRef.value.parentNode as HTMLElement;
  const elementBounds = useElementBounds(parentNode, columnRef.value);
  const isInside = useIsMouseInside(state.reactive.mouseCoords, elementBounds);
  if (isInside) {
    if (!isActive.value) {
      setActive();
    }
  } else {
    setInactive();
  }
};

const updateHoveredSegment = () => {
  actions.updateHoveredSegment({ id: columnIndex, name: name });
};

watch(isActive, () => {
  if (isActive.value) {
    updateHoveredSegment();
  }
});

watch(
  () => state.reactive.mouseCoords,
  () => {
    toggleActive();
  },
);
</script>

<template>
  <div ref="columnRef" class="chart-lines-column" :class="{ 'chart-lines-column-active': isActive }"></div>
</template>
<style lang="css" scoped>
.chart-lines-column {
  position: relative;
  grid-row: 1/2;
}

.chart-lines-column::before {
  position: absolute;
  top: calc(var(--top-indent) * -1);
  left: 50%;
  width: 2px;
  height: calc(125.6% + var(--top-indent));
  background-color: var(--color-column-visible);
  border-top-left-radius: 1px;
  border-top-right-radius: 1px;
  content: '';
  opacity: 0;
  transform: translateX(-50%);
  transition: opacity 0.4s ease;
}

.chart-lines-column.chart-lines-column-active::before {
  opacity: 1;
}
</style>
