<script setup lang="ts">
import { InfoCircleTwoTone, DownloadOutlined } from '@ant-design/icons-vue';
import { ChartLines, ChartLinesFilter } from '@lct/ui';
import { Select, Popover, Button } from 'ant-design-vue';
import { computed, ref, useTemplateRef } from 'vue';

import { useRegionsStore, useStatisticsStore } from '@/app/store';
import { Card } from '@/components';
import { exportToImage } from '@/utils';

import type { SelectHandler } from 'ant-design-vue/es/vc-select/Select';

const colors = [
  '#1f77b4', // Мягкий синий
  '#ff7f0e', // Приглушённый оранжевый
  '#2ca02c', // Умеренный зелёный
  '#d62728', // Тёплый красный (не кричащий)
  '#9467bd', // Лавандовый фиолетовый
  '#8c564b', // Земляной коричневый
  '#e377c2', // Нежно-розовый
  '#7f7f7f', // Нейтральный серый
  '#bcbd22', // Оливково-жёлтый
  '#17becf', // Мягкий бирюзовый
  '#aec7e8', // Светло-голубой
  '#ffbb78', // Светло-оранжевый
  '#98df8a', // Пастельный зелёный
  '#ff9896', // Светло-красный
  '#c5b0d5', // Светло-фиолетовый
  '#c49c94', // Светло-коричневый
  '#f7b6d2', // Бледно-розовый
  '#c7c7c7', // Светло-серый
  '#dbdb8d', // Бледно-жёлтый
  '#9edae5', // Светло-бирюзовый
];

const indicators = [
  { id: 'flights_count', name: 'Всего полетов', metrics: [] },
  { id: 'avg_flights_per_day', name: 'Среднее количество полетов в месяц' },
  { id: 'flight_density', name: 'Плотность полетов', metrics: [] },
  { id: 'total_duration_hours', name: 'Длительность полетов', metrics: [] },
  { id: 'avg_duration_minutes', name: 'Средняя длительность полета', metrics: [] },
  { id: 'median_duration_minutes', name: 'Медианая длительность полета', metrics: [] },
];

const chartRef = useTemplateRef('chartRef');

const statistics = useStatisticsStore();

const region = useRegionsStore();

const data = computed(() => {
  const metricsRegions = indicators.map((indicator) => {
    return {
      id: indicator.id,
      name: indicator.name,
      metrics: region.store!.map((item) => {
        const regionStatistics = statistics.store!.regional_monthly_statistics[item.id];

        return {
          name: item.name,
          percents: regionStatistics.monthly_data.map((item) => item[indicator.id as keyof typeof item] as number),
        };
      }),
    };
  });

  const metricsRussia = indicators.map((indicator) => {
    return {
      id: indicator.id,
      name: indicator.name,
      metrics: [
        {
          name: 'Среднее по РФ',
          percents: statistics.store!.monthly_statistics.map((item) => {
            const avgList = ['avg_duration_minutes', 'avg_flights_per_day', 'median_duration_minutes'];

            if (avgList.includes(indicator.id)) {
              return Math.round(item[indicator.id as keyof typeof item] as number);
            } else {
              return Math.round((item[indicator.id as keyof typeof item] as number) / region.store!.length);
            }
          }),
        },
      ],
    };
  });

  return {
    columns: 12,
    columnLabels: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
    legends: [
      { color: '#000000', name: 'Среднее по РФ' },
      ...region.store!.map((item) => {
        return {
          color: colors[Math.floor(Math.random() * colors.length)],
          name: item.name,
        };
      }),
    ],
    datasetLabel: '',
    datasets: metricsRegions.map((item) => {
      const russianMetric = metricsRussia.find((metic) => item.id === metic.id)!.metrics[0];

      item.metrics.unshift(russianMetric);

      return item;
    }),
  };
});

const selectIndicator = ref('flights_count');
const selectRegion = ref<{ value: string; label: string }[]>([]);
const isFilter = ref(true);
const downloadChart = async () => {
  if (!chartRef.value) return;

  exportToImage(chartRef.value.$el, `${selectIndicator.value}`);
};
</script>

<template>
  <Card>
    <div class="flex flex-col gap-5">
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">
          <p>Сравнение показателей по регионам</p>
        </div>
        <Popover>
          <template #content>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Динамика ключевых показателей в сравнении со средним значением по РФ и значением выбранных регионов</p>
            </div>
          </template>
          <InfoCircleTwoTone class="size-5" />
        </Popover>

        <Button type="primary" class="ml-auto" :style="{ boxShadow: '0 6px 16px 0 rgba(1,134,244,0.3)' }" @click="downloadChart">
          PNG
          <template #icon>
            <DownloadOutlined :style="{ verticalAlign: 'middle', fontSize: '16px' }" />
          </template>
        </Button>
      </div>
      <ChartLines :chart-data="data" ref="chartRef">
        <ChartLinesFilter>
          <template #filter-select="{ datasets, updateIdDataset }">
            <div class="flex flex-col gap-1">
              <div class="text-sm font-semibold text-slate-400">
                <p>Показатель</p>
              </div>
              <Select
                size="large"
                class="min-w-96"
                v-model:value="selectIndicator"
                :options="datasets.map((item) => ({ value: item.id, label: item.name }))"
                not-found-content="Нет данных"
                placeholder="Районы"
                @change="updateIdDataset(selectIndicator)"
              />
            </div>
          </template>

          <template #filter-legends="{ legends, updateValue, initValue }">
            <div class="flex flex-col gap-1">
              <div class="text-sm font-semibold text-slate-400">
                <p>Регионы</p>
              </div>
              <Select
                size="large"
                class="min-w-96"
                style="width: 100%"
                v-model:value="selectRegion"
                allowClear
                mode="multiple"
                :options="
                  (() => {
                    const formatData = legends.map((item) => ({ value: item.name, label: item.name }));

                    if (initValue && isFilter) {
                      selectRegion = formatData.slice(0, 5);

                      isFilter = false;
                    }

                    return formatData;
                  })()
                "
                not-found-content="Нет данных"
                max-tag-count="responsive"
                show-search
                placeholder="Выберите районы"
                @deselect="(value: SelectHandler['arguments']) => updateValue(value)"
                @select="(value: SelectHandler['arguments']) => updateValue(value)"
              />
            </div>
          </template>
        </ChartLinesFilter>
      </ChartLines>
    </div>
  </Card>
</template>

<style lang="scss"></style>
