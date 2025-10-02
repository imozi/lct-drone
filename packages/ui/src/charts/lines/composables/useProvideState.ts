import { provide } from 'vue';

import { createState, stateKey } from '../state';
import { type InitialValue } from '../types';

export const useProvideState = (initialValue: InitialValue) => {
  const { state, actions } = createState(initialValue);

  provide(stateKey, { state, actions });

  return { state, actions };
};
