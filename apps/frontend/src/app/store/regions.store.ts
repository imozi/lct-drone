import { regionsService, type RegionsResponse } from '@lct/services';
import { defineStore } from 'pinia';
import { shallowRef } from 'vue';

export const useRegionsStore = defineStore('regions', () => {
  const store = shallowRef<RegionsResponse[]>();

  const fetch = async () => {
    store.value = await regionsService.findAll();
  };

  return {
    store,
    fetch,
  };
});
