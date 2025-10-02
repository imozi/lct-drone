import { regionsGeneralService, type RegionsGeneralResponse } from '@lct/services';
import { defineStore } from 'pinia';
import { shallowRef } from 'vue';

export const useRegionsGeneralStore = defineStore('regions-general', () => {
  const store = shallowRef<RegionsGeneralResponse>();

  const fetch = async () => {
    store.value = await regionsGeneralService.findAll();
  };

  return {
    store,
    fetch,
  };
});
