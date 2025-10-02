import { statisticsService, type StatisticsResponse } from '@lct/services';
import { defineStore } from 'pinia';
import { shallowRef } from 'vue';

export const useStatisticsStore = defineStore('statistics', () => {
  const store = shallowRef<StatisticsResponse>();

  const fetch = async () => {
    store.value = await statisticsService.findAll();
  };

  return {
    store,
    fetch,
  };
});
