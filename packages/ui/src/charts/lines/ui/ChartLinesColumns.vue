<script setup lang="ts">
import { onMounted, useTemplateRef, watch } from 'vue';

import ChartLinesColumn from './ChartLinesColumn.vue';
import { useElementCoords } from '../composables/useElementCoords';
import { useInjectState } from '../composables/useInjectState';

const { state, actions } = useInjectState();

const columnsContainer = useTemplateRef('columnsContainer');
const columns = useTemplateRef('columns');

const setColumnsCoords = () => {
  if (!columnsContainer.value || !columns.value) return;

  const columnsCoords = columns.value.map((column) => {
    return useElementCoords({ container: columnsContainer.value!, element: column!.$el, centerElement: true });
  });
  actions.updateColumnsCoords(columnsCoords);
};

const setColumnWidth = () => {
  if (!columns.value) return;
  actions.updateColumnWidth(columns.value[0]?.$el.getBoundingClientRect().width);
};

const setAxisYOrigin = () => {
  if (!columnsContainer.value) return;
  actions.updateAxisYOrigin(columnsContainer.value.getBoundingClientRect().height);
};

const $o = new ResizeObserver(() => {
  setColumnsCoords();
  setColumnWidth();
});

onMounted(() => {
  $o.observe(document.body);
  setAxisYOrigin();
});

watch(columns, () => {
  setColumnsCoords();
  setColumnWidth();
});
</script>

<template>
  <div class="chart-lines-columns" ref="columnsContainer">
    <ChartLinesColumn
      ref="columns"
      v-for="index of state.columns"
      :key="index"
      :column-index="index - 1"
      :name="state.columnLabels[index - 1]"
    ></ChartLinesColumn>
    <slot />
  </div>
</template>

<style lang="css" scoped>
.chart-lines-columns {
  display: grid;
  grid-column: 2/-1;
  grid-row: 1/2;
  grid-template-columns: subgrid;
}
</style>
