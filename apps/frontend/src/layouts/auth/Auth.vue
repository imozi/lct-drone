<script setup lang="ts">
import { App } from 'ant-design-vue';
</script>

<template>
  <App>
    <div class="portal-wrapper flex min-h-full flex-col">
      <header class="header"></header>
      <main class="main flex-1">
        <slot />
      </main>
      <footer class="footer"></footer>
    </div>
  </App>
</template>

<style lang="scss"></style>
