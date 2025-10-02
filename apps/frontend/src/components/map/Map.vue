<script setup lang="ts">
import { InfoCircleTwoTone, DownloadOutlined } from '@ant-design/icons-vue';
import { Loader } from '@lct/ui';
import { Select, Popover, Button, Modal, Collapse, CollapsePanel } from 'ant-design-vue';
import maplibregl from 'maplibre-gl';
import { computed, onMounted, ref, shallowRef, useTemplateRef, watch } from 'vue';

import { useRegionsGeneralStore, useRegionsStore, useStatisticsStore } from '@/app/store';
import { exportToImage } from '@/utils';

import { Card } from '../card';

const indicators = [
  { value: 'flights_count', label: 'Всего полетов' },
  { value: 'flight_density', label: 'Плотность полетов' },
  { value: 'avg_flights_per_day', label: 'Среднее количество полетов' },
  { value: 'total_duration_hours', label: 'Длительность полетов' },
  { value: 'avg_duration_minutes', label: 'Средняя длительность полета' },
  { value: 'median_duration_minutes', label: 'Медианая длительность полета' },
];

const periods = [
  {
    value: 'Y',
    label: 'Текущий год',
  },
  {
    value: 'Q1',
    label: '1 квартал',
  },
  {
    value: 'Q2',
    label: '2 квартал',
  },
  {
    value: 'Q3',
    label: '3 квартал',
  },
  {
    value: 'Q4',
    label: '4 квартал',
  },
];

const instansMap = shallowRef<maplibregl.Map | null>(null);
const mapRef = useTemplateRef('mapRef');
const statistics = useStatisticsStore();
const region = useRegionsStore();
const regionsGeneral = useRegionsGeneralStore();

const hoveredRegion = ref<string | number | undefined | null>(null);
const selectedRegion = ref<string | number | undefined | null>(null);
const selectIndicator = shallowRef<string>('flights_count');
const selectPeriod = shallowRef<string>('Y');
const isMapLoading = ref<boolean>(true);
const isOpenModal = ref<boolean>(false);
const isOpenTop = ref<['1']>(['1']);

const selectedRegionInfo = computed(() => {
  if (!selectedRegion.value) return null;

  if (selectPeriod.value === 'Y') {
    return regionsGeneral.store!.regional_statistics.find((item) => item.region_id === selectedRegion.value);
  }

  return statistics.store?.all_regions_quarterly[selectPeriod.value].find((item) => item.region_id === selectedRegion.value);
});

const data = computed(() => {
  if (selectPeriod.value === 'Y') {
    return regionsGeneral.store?.regional_statistics.map((item) => {
      return {
        id: item.region_id,
        name: item.region_name,
        metrics: Math.log1p(item[selectIndicator.value as keyof typeof item] as number),
      };
    });
  }

  return statistics.store?.all_regions_quarterly[selectPeriod.value].map((item) => {
    return {
      id: item.region_id,
      name: item.region_name,
      metrics: Math.log1p(item[selectIndicator.value as keyof typeof item] as number),
    };
  });
});

const topPeriod = computed(() => {
  let top = [];

  if (selectPeriod.value === 'Y') {
    top = regionsGeneral.store!.regional_statistics.map((item) => {
      return {
        id: item.region_id,
        name: item.region_name,
        metrics: item[selectIndicator.value as keyof typeof item] as number,
      };
    });
  } else {
    top = statistics.store!.all_regions_quarterly[selectPeriod.value].map((item) => {
      return {
        id: item.region_id,
        name: item.region_name,
        metrics: item[selectIndicator.value as keyof typeof item] as number,
      };
    });
  }

  return top.sort((a, b) => b.metrics - a.metrics).slice(0, 10);
});

// const minValue = computed(() => {
//   const min = Math.min(...data.value!.map((d) => d.metrics));
//   return min === -Infinity ? 0 : min;
// });

const maxValue = computed(() => {
  const max = Math.max(...data.value!.map((d) => d.metrics));
  return max === Infinity ? 0 : max;
});

const minPositiveValue = computed(() => {
  const positives = data.value!.map((d) => d.metrics).filter((v) => v > 0);
  return positives.length > 0 ? Math.min(...positives) : 1;
});
const downloadChart = async () => {
  if (!mapRef.value) return;

  exportToImage(mapRef.value, `map-${selectIndicator.value}`);
};

watch(data, () => {
  if (!instansMap.value) return;

  data.value?.forEach((item) => {
    instansMap.value?.setFeatureState(
      { source: 'division', sourceLayer: 'russian_regions', id: item.id },
      { metrics: item.metrics === -Infinity ? 0 : item.metrics },
    );
  });
});

watch(selectedRegion, () => {
  if (!selectedRegion.value) return;

  isOpenModal.value = true;
});

onMounted(() => {
  const map = new maplibregl.Map({
    container: 'map',
    style: 'https://api.maptiler.com/maps/streets-v2/style.json?key=nF38wIVDWTFKYEineOME',
    center: [94.2167, 56.6],
    attributionControl: false,
    zoom: 2.5,
    canvasContextAttributes: {
      preserveDrawingBuffer: true,
    },
  });

  map.on('load', () => {
    const layers = map.getStyle().layers;
    const labelLayers = layers.filter((layer) => layer.type === 'symbol' && layer.layout?.['text-field']);

    labelLayers.forEach((layer) => {
      try {
        map.setLayoutProperty(layer.id, 'text-field', ['coalesce', ['get', 'name:ru'], ['get', 'name']]);
      } catch (error: unknown) {
        console.warn('Не удалось обновить слой:', layer.id, error);
      }
    });

    map.addSource('division', {
      type: 'vector',
      promoteId: 'id',
      tiles: [import.meta.env.VITE_TILESSERVER_URL],
    });

    map.addLayer({
      id: 'division-fill-outline',
      type: 'fill',
      source: 'division',
      'source-layer': 'russian_regions',
      paint: {
        'fill-color': [
          'case',

          ['==', ['to-number', ['coalesce', ['feature-state', 'metrics'], 0]], 0],
          '#DDDDDD',

          [
            'interpolate',
            ['linear'],
            ['to-number', ['feature-state', 'metrics']],
            minPositiveValue.value,
            '#FFE374',
            maxValue.value,
            '#D0360F',
          ],
        ],
        'fill-opacity': 0.8,
        'fill-outline-color': '#1e293b',
      },
      // paint: {
      //   'fill-color': [
      //     'interpolate',
      //     ['linear'],
      //     ['coalesce', ['feature-state', 'metrics'], 0],
      //     minValue.value,
      //     '#00ff00', // зелёный
      //     (minValue.value + maxValue.value) / 2,
      //     '#ffff00', // жёлтый
      //     maxValue.value,
      //     '#ff0000', // красный
      //   ],
      //   'fill-opacity': 0.8,
      //   'fill-outline-color': '#1e293b',
      // },
      minzoom: 0,
      maxzoom: 6,
    });

    map.addLayer({
      id: 'division-labels',
      type: 'symbol',
      source: 'division',
      'source-layer': 'russian_regions_label',
      layout: {
        'text-field': ['get', 'name'],
        'text-size': 12,
        'text-anchor': 'center',
      },
      paint: {
        'text-color': '#000000',
        'text-halo-color': '#ffffff',
        'text-halo-width': 1,
      },
      minzoom: 0,
      maxzoom: 6,
    });

    map.addLayer({
      id: 'division-hover',
      type: 'fill',
      source: 'division',
      'source-layer': 'russian_regions',
      paint: {
        'fill-color': '#1e293b',
        'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.2, 0],
      },
      minzoom: 0,
      maxzoom: 6,
    });

    map.addLayer({
      id: 'division-water-fill',
      type: 'fill',
      source: 'division',
      'source-layer': 'russian_regions_water',
      paint: {
        'fill-color': '#1e293b',
        'fill-opacity': 0.02,
      },
      minzoom: 0,
      maxzoom: 6,
    });

    map.addLayer({
      id: 'division-water-outline',
      type: 'line',
      source: 'division',
      'source-layer': 'russian_regions_water',
      paint: {
        'line-color': '#1e293b',
        'line-width': 0.1,
        'line-opacity': 0.2,
      },
      minzoom: 0,
      maxzoom: 6,
    });
  });

  map.on('mousemove', 'division-hover', (e) => {
    if (e.features && e.features.length > 0) {
      map.getCanvas().style.cursor = 'pointer';

      if (hoveredRegion.value !== null) {
        map.setFeatureState({ source: 'division', sourceLayer: 'russian_regions', id: hoveredRegion.value }, { hover: false });
      }

      hoveredRegion.value = e.features[0].id;

      map.setFeatureState({ source: 'division', sourceLayer: 'russian_regions', id: hoveredRegion.value }, { hover: true });
    }
  });

  map.on('mouseleave', 'division-hover', () => {
    map.getCanvas().style.cursor = '';

    if (hoveredRegion.value !== null) {
      map.setFeatureState({ source: 'division', sourceLayer: 'russian_regions', id: hoveredRegion.value }, { hover: false });
    }

    hoveredRegion.value = null;
  });

  map.on('idle', () => {
    isMapLoading.value = false;
  });

  map.on('sourcedata', (e) => {
    if (e.sourceId === 'division') {
      data.value?.forEach((item) => {
        instansMap.value?.setFeatureState({ source: 'division', sourceLayer: 'russian_regions', id: item.id }, { metrics: item.metrics });
      });
    }
  });

  map.on('click', 'division-fill-outline', (e) => {
    if (e.features && e.features.length > 0) {
      selectedRegion.value = e.features[0].id;
    }
  });

  instansMap.value = map;
});
</script>

<template>
  <Card>
    <div class="flex flex-col gap-5">
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">
          <p>Карта активности БПЛА</p>
        </div>
        <Popover>
          <template #content>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Тепловая карта ключевых показателей регионов РФ за выбранный период.</p>
              <p>Серым цветом - регионы с показателем 0</p>
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
      <div class="flex flex-col gap-5" ref="mapRef">
        <div class="flex items-center gap-5">
          <div class="flex flex-col gap-1">
            <div class="text-sm font-semibold text-slate-400">
              <p>Показатель</p>
            </div>
            <Select
              size="large"
              v-model:value="selectIndicator"
              :options="indicators"
              class="min-w-80"
              not-found-content="Нет данных"
              show-search
              placeholder="Показетель"
            />
          </div>
          <div class="flex flex-col gap-1">
            <div class="text-sm font-semibold text-slate-400">
              <p>Период</p>
            </div>
            <Select
              size="large"
              v-model:value="selectPeriod"
              :options="periods"
              class="min-w-80"
              not-found-content="Нет данных"
              show-search
              placeholder="Выберите квартал"
            />
          </div>
        </div>
        <div class="relative h-[900px] w-full overflow-hidden rounded-lg">
          <Loader v-if="isMapLoading" class="z-50 bg-black/30" />
          <div id="map" class="map h-full w-full overflow-hidden rounded-lg"></div>
          <Modal
            :mask="false"
            :footer="false"
            v-model:open="isOpenModal"
            :title="
              selectedRegionInfo
                ? `${selectedRegionInfo!.region_name} - ${periods.find((item) => item.value === selectPeriod)!.label.toLowerCase()}`
                : ''
            "
            width="450px"
            centered
            :after-close="() => (selectedRegion = null)"
          >
            <div class="flex flex-col gap-5">
              <ul v-if="selectedRegionInfo" class="flex flex-col gap-2">
                <li class="flex items-center justify-between rounded-xs p-0.5 px-2">
                  <p>Прощадь региона:</p>
                  <p>{{ region.store!.find((item) => item.id === selectedRegion)!.area }}km<sup>2</sup></p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'flights_count' }"
                >
                  <p>Всего полетов</p>
                  <p>{{ selectedRegionInfo.flights_count }}</p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'avg_flights_per_day' }"
                >
                  <p>Среднее количество полетов</p>
                  <p>{{ selectedRegionInfo.avg_flights_per_day }}</p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'flight_density' }"
                >
                  <p>Плотность полетов на 1000км<sup>2</sup></p>
                  <p>{{ selectedRegionInfo.flight_density }}</p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'total_duration_hours' }"
                >
                  <p>∑ Длительность полетов</p>
                  <p>{{ selectedRegionInfo.total_duration_hours }}</p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'avg_duration_minutes' }"
                >
                  <p>Средняя длительность полета</p>
                  <p>{{ selectedRegionInfo.avg_duration_minutes }}</p>
                </li>
                <li
                  class="flex items-center justify-between rounded-xs p-0.5 px-2"
                  :class="{ 'bg-blue-100 font-medium': selectIndicator === 'median_duration_minutes' }"
                >
                  <p>Медианая длительность полета</p>
                  <p>{{ selectedRegionInfo.median_duration_minutes }}</p>
                </li>
              </ul>
              <Button type="primary" class="w-full">
                <RouterLink :to="`/dashboard/${selectedRegionInfo?.region_id}`"> Перейти на дашборд региона </RouterLink>
              </Button>
            </div>
          </Modal>

          <Card class="absolute top-5 right-5 flex flex-col gap-5 bg-white p-0 text-sm">
            <Collapse v-model:activeKey="isOpenTop" ghost expandIconPosition="end" class="bg-white">
              <CollapsePanel key="1" class="bg-white px-3 text-lg font-medium">
                <template #header>
                  <div class="bg-white px-3 pt-1 font-sans text-xl font-bold">
                    <p>ТОП 10 регионов</p>
                    <p class="text-sm font-normal">
                      {{ indicators.find((item) => item.value === selectIndicator)?.label.toLowerCase() }} -
                      {{ periods.find((item) => item.value === selectPeriod)!.label.toLowerCase() }}
                    </p>
                  </div>
                </template>
                <ul class="flex flex-col gap-1 bg-white px-3 pb-3 text-sm font-normal">
                  <li class="flex items-center gap-1" v-for="(value, i) in topPeriod" :key="value.id">
                    <p>{{ i + 1 }}</p>
                    <Button type="link">
                      <RouterLink :to="`/dashboard/${value?.id}`"> {{ value.name }} </RouterLink>
                    </Button>
                    <p class="ml-auto rounded-lg bg-slate-100 p-1 px-2">{{ value.metrics }}</p>
                  </li>
                </ul>
              </CollapsePanel>
            </Collapse>
            <!-- <div class="flex flex-col gap-3 bg-white">
              <div class="text-xl font-bold">
                <p>
                  ТОП 10 регионов: {{ indicators.find((item) => item.value === selectIndicator)?.label.toLowerCase() }} {{ selectPeriod }}
                </p>
              </div>
              <ul class="flex flex-col gap-1">
                <li class="flex items-center gap-5" v-for="(value, i) in topPeriod" :key="value.id">
                  <p>{{ i + 1 }}</p>
                  <p>{{ value.name }}</p>
                  <p class="ml-auto rounded-lg bg-slate-100 p-1 px-2">{{ value.metrics }}</p>
                </li>
              </ul>
            </div> -->
          </Card>
        </div>
      </div>
    </div>
  </Card>
</template>

<style lang="scss">
.ant-collapse-header {
  align-items: center !important;
}

.ant-collapse-ghost {
  overflow: hidden;
}
</style>
