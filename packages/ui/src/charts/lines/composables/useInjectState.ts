import { inject } from 'vue';

import { stateKey } from '../state';

export const useInjectState = () => {
  const store = inject(stateKey);

  if (!store) {
    throw new Error('useChartLinesState must be used in a component provided with chartLinesStore');
  }

  return store;
};
