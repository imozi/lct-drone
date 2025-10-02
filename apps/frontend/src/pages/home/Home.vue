<script setup lang="ts">
import { Divider, Select, Button } from 'ant-design-vue';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { useStatisticsStore, useUsersStore } from '@/app/store';
import { FlyChartBar, ChartLines, Map, Indicator, Table, Top } from '@/components';

const { store } = useStatisticsStore();
const { logaut, getRole } = useUsersStore();
const router = useRouter();

const goToLoadData = () => {
  router.push({ path: '/loaddata' });
};

const selectPeriod = ref(2025);
</script>

<template>
  <div class="main-wrapper flex w-full flex-col py-14">
    <div class="flex flex-col">
      <div class="flex items-center gap-5">
        <div class="text-4xl font-bold">
          <h1>Ключевые показатели полётов БПЛА в регионах РФ</h1>
        </div>
        <div class="flex grow items-center gap-3">
          <div class="text-lg font-semibold text-slate-400">
            <p>Период:</p>
          </div>
          <Select
            v-model:value="selectPeriod"
            size="large"
            class="min-w-48"
            :options="[{ value: 2025, label: 'Текущий год' }]"
            not-found-content="Нет данных"
            placeholder="Районы"
          />
          <div class="ml-auto flex items-center gap-3">
            <Button size="large" type="primary" v-if="getRole() === 'admin'" @click="goToLoadData">Згрузить данные</Button>
            <Button size="large" @click="logaut">Выйти</Button>
          </div>
        </div>
      </div>
      <Divider />
    </div>
    <div class="flex flex-col gap-10">
      <div class="grid gap-3 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
        <Indicator name="Индекс активности">
          <template #description>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>
                Индекс активности — это условный показатель, отражающий интенсивность полётов БПЛА в регионе. Он рассчитывается на основе
                совокупности базовых метрик и служит ориентировочным индикатором уровня активности региона.
              </p>
              <p>
                Показатель разработан в целях универсального подхода к рейтингованию регионов и может быть заменён по запросу заказчика на
                любой другой согласованный рейтинг или метод оценки.
              </p>
              <p>
                <span class="font-bold text-red-500">*</span> Подробнее формулы расчета Индекса описаны в сопроводительной документации.
              </p>
            </div>
          </template>
          {{ Math.round(store?.overall_statistics.average_activity_index!) }}
        </Indicator>
        <Indicator name="Всего полетов">
          <template #description>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Суммарное количество полетов по всем регионам за отчетный период</p>
            </div>
          </template>
          {{ Math.round(store?.overall_statistics.total_flights_count!) }}
        </Indicator>
        <Indicator name="Среднее кол-во полетов">
          <template #description>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Суммарное кол-во полетов по стране / кол-во регионов</p>
            </div>
          </template>
          {{ Math.round(store?.overall_statistics.avg_flights_per_month!) }}
        </Indicator>

        <Indicator name="∑ длительность полетов">
          <template #description>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Суммарная длительность полетов в часах по всем регионам за отчетный период</p>
            </div>
          </template>
          {{ Math.round(store?.overall_statistics.total_duration_hours!) }} часов
        </Indicator>

        <Indicator name="Средн./медиан. длит. полета" description="Всего">
          <template #description>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>- Средняя длительность полетов по всем регионам</p>
              <p>- Медианная длительность полетов по всем регионам</p>
              <p>Показатели считаются по значениям указанных в плане полета</p>
            </div>
          </template>
          {{ Math.round(store?.overall_statistics.avg_duration_minutes!) }} /
          {{ Math.round(store?.overall_statistics.median_duration_minutes!) }}
        </Indicator>
      </div>

      <div class="grid grid-cols-1 gap-4 2xl:grid-cols-2">
        <Top />
        <FlyChartBar />
      </div>

      <ChartLines />

      <Map />

      <Table />
    </div>
  </div>
</template>

<style lang="scss"></style>
