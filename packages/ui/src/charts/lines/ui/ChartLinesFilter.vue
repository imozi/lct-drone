<script setup lang="ts">
import { useInjectState } from '../composables/useInjectState';
const { state, actions } = useInjectState();

const onChangeChecked = (name: string) => {
  actions.updateFilterLegend(name);
};

const onChangeDataset = (evt: Event) => {
  const target = evt.target as HTMLSelectElement;

  actions.updateIdDataset(target.value);
};
</script>

<template>
  <div class="chart-lines-filter">
    <div class="chart-lines-filter-column">
      <p>{{ state.datasetLabel }}</p>
      <slot
        name="filter-select"
        :datasets="state.datasets"
        :updateIdDataset="actions.updateIdDataset"
        :init-value="state.reactive.filterIdDataset"
      >
        <select name="" id="" @change="onChangeDataset">
          <option :value="dataset.id" v-for="dataset of state.datasets" :key="dataset.id">{{ dataset.name }}</option>
        </select>
      </slot>
    </div>
    <div class="chart-lines-filter-column">
      <slot name="filter-legends" :legends="state.legends" :updateValue="onChangeChecked" :init-value="true">
        <label v-for="(legend, i) of state.legends" :key="legend.name">
          <input type="checkbox" :checked="i <= 5 ? true : false" @change="onChangeChecked(legend.name)" />
          {{ legend.name }}
        </label>
      </slot>
    </div>
  </div>
</template>

<style lang="css" scoped>
.chart-lines-filter {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.chart-lines-filter-column {
  display: flex;
  align-items: center;
  gap: 1rem;
}
</style>
