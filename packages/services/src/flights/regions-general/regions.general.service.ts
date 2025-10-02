import { axios } from '../../axios';

import type { RegionsGeneralResponse } from '../../types';

export const regionsGeneralService = {
  findAll: async () => {
    const { data } = await axios.get<RegionsGeneralResponse>('/flights/statistics/regional_annual_statistics/');
    return data;
  },
};
