<script lang="ts" setup>
import { DownloadOutlined, InfoCircleTwoTone } from '@ant-design/icons-vue';
import { Button, Popover } from 'ant-design-vue';
import { useTemplateRef } from 'vue';

import { useStatisticsStore } from '@/app/store';
import { exportToImage, paints } from '@/utils';

import { Card } from '../card';

const topRef = useTemplateRef('topRef');

const { store } = useStatisticsStore();

const downloadChart = async () => {
  if (!topRef.value) return;

  exportToImage(topRef.value, `top`);
};
</script>

<template>
  <Card>
    <div class="flex flex-col gap-5">
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">
          <p>ТОП 10 регионов по индексу активности</p>
        </div>
        <Popover>
          <template #content>
            <div class="flex max-w-96 flex-col gap-3 p-1">
              <p>Блок представлен в виде рейтинговой таблицы, отражающей позиции регионов по убыванию индекса активности полётов БПЛА.</p>
              <p>При клике на название региона осуществляется переход на отдельную страницу с детальной аналитикой по этому региону.</p>
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

      <div class="grid grid-cols-[auto_1fr_1fr_1fr_1fr_auto] gap-x-6" ref="topRef">
        <div class="col-span-full grid grid-cols-subgrid">
          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>Место в рейтинге</p>
          </div>

          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>Индекс активности</p>
          </div>

          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>Кол-во полетов</p>
          </div>

          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>Плотность полетов</p>
          </div>

          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>∑ длит. полетов</p>
          </div>

          <div class="flex items-center text-center text-sm font-semibold text-slate-400">
            <p>Средн. / медиан. длит. полета</p>
          </div>
        </div>
        <div class="col-span-full grid grid-cols-subgrid gap-y-1 text-sm">
          <div
            v-for="(item, index) of store?.top_10_regions_overall"
            class="col-span-full grid grid-cols-subgrid items-center"
            :key="item.region_id"
          >
            <div class="col-1 flex items-center leading-none">
              <div class="flex flex-row items-center gap-4">
                <p class="min-w-5 text-center">{{ index + 1 }}</p>
                <Button type="link" style="padding: 0; text-align: left">
                  <RouterLink :to="`/dashboard/${item.region_id}`"> {{ item.region_name }} </RouterLink>
                </Button>
              </div>
            </div>

            <div class="col-2 flex items-center justify-center rounded-lg px-3 py-2 leading-none" :class="paints(item.activity_index)">
              <p>{{ item.activity_index }}</p>
            </div>

            <div class="col-3 flex items-center justify-center leading-none">
              <p>{{ item.flights_count }}</p>
            </div>

            <div class="col-4 flex items-center justify-center leading-none">
              <p>{{ item.flight_density }}</p>
            </div>

            <div class="col-5 flex items-center justify-center leading-none">
              <p>{{ item.total_duration_hours }}</p>
            </div>

            <div class="col-6 flex items-center justify-center leading-none">
              <p>{{ item.avg_duration_minutes + ' / ' + item.median_duration_minutes + ' мин' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<style lang="scss"></style>
