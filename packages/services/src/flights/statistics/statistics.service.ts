import { axios } from '../../axios';

import type { StatisticsResponse } from '../../types';

export const statisticsService = {
  findAll: async () => {
    const { data } = await axios.get<StatisticsResponse>('/flights/statistics/dashboard/');
    return data;
  },
};
