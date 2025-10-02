<script setup lang="ts">
import { Result, Button } from 'ant-design-vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const goBack = () => {
  router.back();
};
</script>

<template>
  <div class="absolute inset-0 flex items-center justify-center">
    <Result status="500" title="Страница в разработке" sub-title="">
      <template #extra>
        <Button type="primary" @click="goBack">Вернуться</Button>
      </template>
    </Result>
  </div>
</template>

<style lang="scss"></style>
