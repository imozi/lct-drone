<script setup lang="ts"></script>

<template>
  <div class="portal-wrapper flex min-h-full flex-col">
    <header class="header"></header>
    <main class="main flex-1">
      <slot />
    </main>
    <footer class="footer"></footer>
  </div>
</template>

<style lang="scss"></style>
