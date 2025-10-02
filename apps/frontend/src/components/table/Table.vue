<script setup lang="ts">
import { FileTextOutlined, InfoCircleTwoTone } from '@ant-design/icons-vue';
import { axios } from '@lct/services';
import { Button, Popover } from 'ant-design-vue';
import { ArrowDownZA, ArrowUpAZ, ArrowUpDown, MoveDown, MoveUp } from 'lucide-vue-next';
import { computed, reactive, ref } from 'vue';

import { useRegionsGeneralStore } from '@/app/store';
import { paints } from '@/utils';

import { Card } from '../card';

const { store } = useRegionsGeneralStore();

const sort = reactive({
  by: 'activity_index',
  direction: 'desc',
});

const isLoading = ref(false);

const sortedData = computed(() => {
  return [...store!.regional_statistics].sort((a, b) => {
    let valueA, valueB;

    switch (sort.by) {
      case 'rating':
        valueA = a.rating;
        valueB = b.rating;
        break;
      case 'activity_index':
        valueA = a.activity_index;
        valueB = b.activity_index;
        break;
      case 'avg_duration_minutes':
        valueA = a.avg_duration_minutes;
        valueB = b.avg_duration_minutes;
        break;
      case 'flights_count_year':
        valueA = a.flights_count;
        valueB = b.flights_count;
        break;
      case 'time_distribution':
        valueA = a.flights_count;
        valueB = b.flights_count;
        break;
      case 'flight_density_year':
        valueA = a.flight_density;
        valueB = b.flight_density;
        break;
      case 'total_duration_hours':
        valueA = a.total_duration_hours;
        valueB = b.total_duration_hours;
        break;
      case 'median_duration_minutes':
        valueA = a.median_duration_minutes;
        valueB = b.median_duration_minutes;
        break;
      case 'zero_flight_days':
        valueA = a.zero_flight_days;
        valueB = b.zero_flight_days;
        break;
      default:
        valueA = a.region_name;
        valueB = b.region_name;
    }

    if (typeof valueA === 'string' && typeof valueB === 'string') {
      return sort.direction === 'asc' ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA);
    }

    return sort.direction === 'asc' ? Number(valueA) - Number(valueB) : Number(valueB) - Number(valueA);
  });
});

const getExportData = async () => {
  try {
    isLoading.value = true;
    const response = await axios.get('/flights/statistics/export_regional_annual_excel/', {
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    let fileName = `fly-drone-export-${new Date().toISOString().slice(0, 10)}.xlsx`;

    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();

    window.URL.revokeObjectURL(url);
    link.remove();

    isLoading.value = false;
  } catch (error) {
    isLoading.value = false;
    console.error('Ошибка при скачивании файла:', error);
  }
};
</script>

<template>
  <Card>
    <div class="mb-5 flex flex-col gap-8">
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">
          <p>Сводная таблица по всем регионам</p>
        </div>
        <Popover>
          <template #content>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Сводная таблица ключевых показателей регионов РФ.</p>
              <p>
                Таблицу можно сортировать по любому столбцу, при этом позиция региона в рейтинге (первый столбец) всегда отображается в
                соответствии с его местом по индексу активности, независимо от текущей сортировки.
              </p>
            </div>
          </template>

          <InfoCircleTwoTone />
        </Popover>
        <Button
          type="primary"
          class="ml-auto"
          :style="{ boxShadow: '0 6px 16px 0 rgba(1,134,244,0.3)' }"
          :loading="isLoading"
          @click="getExportData"
        >
          Выгрузить отчет
          <template #icon>
            <FileTextOutlined :style="{ verticalAlign: 'middle', fontSize: '16px' }" />
          </template>
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-[auto_auto_auto_auto_auto_auto_auto_auto] gap-x-5 gap-y-3 overflow-x-auto text-xs text-slate-400">
      <div class="col-span-full grid shrink-0 grid-cols-subgrid border-b border-slate-100 pb-3">
        <div class="flex items-center gap-x-10">
          <div class="flex items-center gap-x-1">
            <p>Место в рейтинге</p>
            <Button
              type="ghost"
              size="small"
              @click="
                () => {
                  if (sort.by === 'rating') {
                    sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                  } else {
                    sort.by = 'rating';
                    sort.direction = 'desc';
                  }
                }
              "
            >
              <MoveDown
                v-if="sort.by === 'rating' && sort.direction === 'desc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'rating' && sort.direction === 'desc' }"
              />
              <MoveUp
                v-else-if="sort.by === 'rating' && sort.direction === 'asc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'rating' && sort.direction === 'asc' }"
              />
              <ArrowUpDown v-else class="size-3.5 text-slate-400" />
            </Button>
          </div>
          <Button
            type="ghost"
            size="small"
            class="ml-auto"
            @click="
              () => {
                if (sort.by === 'name') {
                  sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                  sort.by = 'name';
                  sort.direction = 'desc';
                }
              }
            "
          >
            <ArrowDownZA v-if="sort.by === 'name' && sort.direction === 'desc'" class="size-4" />
            <ArrowUpAZ v-else class="size-4" />
          </Button>
        </div>
        <div class="flex items-center gap-x-2">
          <p class="flex shrink-0 items-center">Индекс активности</p>
          <div class="shrink-0">
            <Button
              type="ghost"
              size="small"
              @click="
                () => {
                  if (sort.by === 'activity_index') {
                    sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                  } else {
                    sort.by = 'activity_index';
                    sort.direction = 'desc';
                  }
                }
              "
            >
              <MoveDown
                v-if="sort.by === 'activity_index' && sort.direction === 'desc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'activity_index' && sort.direction === 'desc' }"
              />
              <MoveUp
                v-else-if="sort.by === 'activity_index' && sort.direction === 'asc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'activity_index' && sort.direction === 'asc' }"
              />
              <ArrowUpDown v-else class="size-3.5 text-slate-400" />
            </Button>
          </div>
        </div>
        <div class="flex items-center gap-x-2">
          <p class="flex shrink-0 items-center gap-x-2">Кол-во полетов</p>
          <Button
            type="ghost"
            size="small"
            @click="
              () => {
                if (sort.by === 'flights_count_year') {
                  sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                  sort.by = 'flights_count_year';
                  sort.direction = 'desc';
                }
              }
            "
          >
            <MoveDown
              v-if="sort.by === 'flights_count_year' && sort.direction === 'desc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'flights_count_year' && sort.direction === 'desc' }"
            />
            <MoveUp
              v-else-if="sort.by === 'flights_count_year' && sort.direction === 'asc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'flights_count_year' && sort.direction === 'asc' }"
            />
            <ArrowUpDown v-else class="size-3.5 text-slate-400" />
          </Button>
        </div>
        <div class="flex items-center gap-x-2">
          <p class="flex shrink-0 items-center gap-x-2">Плотность полетов</p>

          <Button
            type="ghost"
            size="small"
            @click="
              () => {
                if (sort.by === 'flight_density_year') {
                  sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                  sort.by = 'flight_density_year';
                  sort.direction = 'desc';
                }
              }
            "
          >
            <MoveDown
              v-if="sort.by === 'flight_density_year' && sort.direction === 'desc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'flight_density_year' && sort.direction === 'desc' }"
            />
            <MoveUp
              v-else-if="sort.by === 'flight_density_year' && sort.direction === 'asc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'flight_density_year' && sort.direction === 'asc' }"
            />
            <ArrowUpDown v-else class="size-3.5 text-slate-400" />
          </Button>
        </div>
        <div class="flex items-center gap-x-2">
          <p class="flex shrink-0 items-center gap-x-2">∑ длит. полетов</p>

          <Button
            type="ghost"
            size="small"
            @click="
              () => {
                if (sort.by === 'total_duration_hours') {
                  sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                  sort.by = 'total_duration_hours';
                  sort.direction = 'desc';
                }
              }
            "
          >
            <MoveDown
              v-if="sort.by === 'total_duration_hours' && sort.direction === 'desc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'total_duration_hours' && sort.direction === 'desc' }"
            />
            <MoveUp
              v-else-if="sort.by === 'total_duration_hours' && sort.direction === 'asc'"
              class="size-3.5"
              :class="{ 'text-slate-900': sort.by === 'total_duration_hours' && sort.direction === 'asc' }"
            />
            <ArrowUpDown v-else class="size-3.5 text-slate-400" />
          </Button>
        </div>

        <div class="flex flex-col items-center gap-x-2">
          <p class="flex shrink-0 items-center gap-x-2">Длит.полета, мин</p>
          <div class="flex gap-2 text-xs">
            <div class="flex items-center gap-x-2">
              <p>Средн.</p>
              <div class="shrink-0">
                <Button
                  type="ghost"
                  size="small"
                  @click="
                    () => {
                      if (sort.by === 'avg_duration_minutes') {
                        sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                      } else {
                        sort.by = 'avg_duration_minutes';
                        sort.direction = 'desc';
                      }
                    }
                  "
                >
                  <MoveDown
                    v-if="sort.by === 'avg_duration_minutes' && sort.direction === 'desc'"
                    class="size-3.5"
                    :class="{ 'text-slate-900': sort.by === 'avg_duration_minutes' && sort.direction === 'desc' }"
                  />
                  <MoveUp
                    v-else-if="sort.by === 'avg_duration_minutes' && sort.direction === 'asc'"
                    class="size-3.5"
                    :class="{ 'text-slate-900': sort.by === 'avg_duration_minutes' && sort.direction === 'asc' }"
                  />
                  <ArrowUpDown v-else class="size-3.5 text-slate-400" />
                </Button>
              </div>
            </div>
            <div class="flex items-center gap-x-2">
              <p>Медиан.</p>
              <Button
                type="ghost"
                size="small"
                @click="
                  () => {
                    if (sort.by === 'median_duration_minutes') {
                      sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                    } else {
                      sort.by = 'median_duration_minutes';
                      sort.direction = 'desc';
                    }
                  }
                "
              >
                <MoveDown
                  v-if="sort.by === 'median_duration_minutes' && sort.direction === 'desc'"
                  class="size-3.5"
                  :class="{ 'text-slate-900': sort.by === 'median_duration_minutes' && sort.direction === 'desc' }"
                />
                <MoveUp
                  v-else-if="sort.by === 'median_duration_minutes' && sort.direction === 'asc'"
                  class="size-3.5"
                  :class="{ 'text-slate-900': sort.by === 'median_duration_minutes' && sort.direction === 'asc' }"
                />
                <ArrowUpDown v-else class="size-3.5 text-slate-400" />
              </Button>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-x-2">
          <p class="flex shrink-0 items-center gap-x-2">Нулевые дни</p>
          <div class="shrink-0">
            <Button
              type="ghost"
              size="small"
              @click="
                () => {
                  if (sort.by === 'zero_flight_days') {
                    sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                  } else {
                    sort.by = 'zero_flight_days';
                    sort.direction = 'desc';
                  }
                }
              "
            >
              <MoveDown
                v-if="sort.by === 'zero_flight_days' && sort.direction === 'desc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'zero_flight_days' && sort.direction === 'desc' }"
              />
              <MoveUp
                v-else-if="sort.by === 'zero_flight_days' && sort.direction === 'asc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'zero_flight_days' && sort.direction === 'asc' }"
              />
              <ArrowUpDown v-else class="size-3.5 text-slate-400" />
            </Button>
          </div>
        </div>
        <div class="flex items-center gap-x-2">
          <div class="flex flex-col items-center">
            <p class="flex shrink-0 items-center gap-x-2">Активность</p>
            <p>утро/день/вечер</p>
          </div>
          <div class="shrink-0">
            <Button
              type="ghost"
              size="small"
              @click="
                () => {
                  if (sort.by === 'time_distribution') {
                    sort.direction = sort.direction === 'asc' ? 'desc' : 'asc';
                  } else {
                    sort.by = 'time_distribution';
                    sort.direction = 'desc';
                  }
                }
              "
            >
              <MoveDown
                v-if="sort.by === 'time_distribution' && sort.direction === 'desc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'time_distribution' && sort.direction === 'desc' }"
              />
              <MoveUp
                v-else-if="sort.by === 'time_distribution' && sort.direction === 'asc'"
                class="size-3.5"
                :class="{ 'text-slate-900': sort.by === 'time_distribution' && sort.direction === 'asc' }"
              />
              <ArrowUpDown v-else class="size-3.5 text-slate-400" />
            </Button>
          </div>
        </div>
      </div>
      <TransitionGroup tag="div" name="table-list" class="col-span-full grid shrink-0 grid-cols-subgrid gap-y-2 text-black">
        <div v-for="region of sortedData" :key="region.region_id" class="col-span-full grid grid-cols-subgrid items-center">
          <div class="col-1 grid grid-cols-[minmax(40px,auto)_1fr] items-center gap-5">
            <span class="text-center">{{ region.rating }}</span>
            <Button type="link" style="padding: 0; text-align: left">
              <RouterLink :to="`/dashboard/${region.region_id}`"> {{ region.region_name }} </RouterLink>
            </Button>
          </div>

          <div class="col-2">
            <div class="flex h-7 w-auto items-center justify-center rounded-md px-2 text-sm" :class="paints(region.activity_index)">
              <p>{{ region.activity_index }}</p>
            </div>
          </div>

          <div class="col-3">
            <div class="flex h-7 w-auto items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.flights_count }}</p>
            </div>
          </div>

          <div class="col-4">
            <div class="flex h-7 w-auto items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.flight_density }}</p>
            </div>
          </div>

          <div class="col-5">
            <div class="flex h-7 w-auto items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.total_duration_hours }}</p>
            </div>
          </div>

          <div class="col-6 flex w-full items-center gap-2">
            <div class="flex h-7 w-full items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.avg_duration_minutes }}</p>
            </div>
            <div class="flex h-7 w-full items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.median_duration_minutes }}</p>
            </div>
          </div>

          <div class="col-7">
            <div class="flex h-7 w-auto items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>{{ region.zero_flight_days }}</p>
            </div>
          </div>
          <div class="col-8">
            <div class="flex h-7 w-auto items-center justify-center rounded-md bg-[#EBF1FB] px-2 text-sm">
              <p>
                {{ region.time_distribution.morning_flights }} / {{ region.time_distribution.day_flights }} /
                {{ region.time_distribution.evening_flights }}
              </p>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Card>
</template>

<style lang="scss">
.table-list-move,
.table-list-enter-active,
.table-list-leave-active {
  transition: all 0.3s ease-in-out;
}

.table-list-enter-from,
.table-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.table-list-leave-active {
  position: absolute;
  display: none;
}
</style>
