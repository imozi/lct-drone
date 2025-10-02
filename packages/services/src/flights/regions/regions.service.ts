import { axios } from '../../axios';

import type { RegionsResponse } from '../../types';

export const regionsService = {
  findAll: async () => {
    const { data } = await axios.get<RegionsResponse[]>('/flights/regions/');
    return data;
  },
};
