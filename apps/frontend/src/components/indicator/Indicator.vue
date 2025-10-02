<script setup lang="ts">
import { InfoCircleTwoTone } from '@ant-design/icons-vue';
import { Popover } from 'ant-design-vue';

import { Card } from '../card';

type IndicatorProps = {
  name: string;
};

const props = defineProps<IndicatorProps>();
</script>

<template>
  <Card>
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <div class="text-sm">
          <p>{{ props.name }}</p>
        </div>
        <Popover>
          <template #content>
            <slot name="description" />
          </template>
          <InfoCircleTwoTone />
        </Popover>
      </div>
      <div class="">
        <div class="text-4xl font-extrabold">
          <slot />
        </div>
      </div>
    </div>
  </Card>
</template>

<style lang="scss"></style>
