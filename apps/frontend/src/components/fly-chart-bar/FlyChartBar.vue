<script lang="ts" setup>
import { DownloadOutlined, InfoCircleTwoTone } from '@ant-design/icons-vue';
import { Button, Popover } from 'ant-design-vue';
import { BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { ref, provide, useTemplateRef } from 'vue';
import VChart, { THEME_KEY } from 'vue-echarts';

import { useStatisticsStore } from '@/app/store';
import { exportToImage } from '@/utils';

import { Card } from '../card';

const chartRef = useTemplateRef('chartRef');

const { store } = useStatisticsStore();

use([CanvasRenderer, BarChart, GridComponent, TitleComponent, TooltipComponent, LegendComponent]);

provide(THEME_KEY, 'light');

const option = ref({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'line',
    },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
  },
  xAxis: [
    {
      type: 'category',
      data: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
      axisTick: {
        alignWithLabel: true,
      },
      axisLabel: {
        fontSize: 10,
        interval: 0,
      },
    },
  ],
  yAxis: [
    {
      type: 'value',
    },
  ],
  series: [
    {
      name: 'Количество полетов',
      type: 'bar',
      barWidth: '85%',
      itemStyle: {
        color: 'rgba(247, 205, 35, 0.5)',
      },
      emphasis: {
        itemStyle: {
          color: 'rgba(247, 205, 35, 1)',
        },
      },
      data: store?.monthly_statistics?.map((item) => item.flights_count),
    },
  ],
});

const downloadChart = async () => {
  if (!chartRef.value) return;

  exportToImage(chartRef.value, `fly`);
};
</script>

<template>
  <Card>
    <div class="flex flex-col gap-5">
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">
          <p>Кол-во полётов БПЛА по месяцам</p>
        </div>
        <Popover>
          <template #content>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Блок отображает динамику кол-ва полётов по&nbsp;месяцам</p>
            </div>
          </template>

          <InfoCircleTwoTone />
        </Popover>
        <Button type="primary" class="ml-auto" :style="{ boxShadow: '0 6px 16px 0 rgba(1,134,244,0.3)' }" @click="downloadChart">
          PNG
          <template #icon>
            <DownloadOutlined :style="{ verticalAlign: 'middle', fontSize: '16px' }" />
          </template>
        </Button>
      </div>
    </div>

    <div class="" ref="chartRef">
      <VChart class="chart" :option="option" autoresize />
    </div>
  </Card>
</template>

<style scoped>
.chart {
  width: 100%;
  height: auto;
  min-height: 250px; /* Минимальная высота на мобильных */
  max-height: 400px;
  aspect-ratio: 2 / 1; /* Сохраняет пропорции, например 2:1 */
}
</style>
