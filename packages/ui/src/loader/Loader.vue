<script setup lang="ts">
import { Primitive } from '..';
</script>

<template>
  <Primitive class="absolute inset-0 flex items-center justify-center">
    <div class="spinner"></div>
  </Primitive>
</template>

<style lang="scss">
.spinner {
  display: grid;
  width: 56px;
  height: 56px;
  border: 4px solid #0000;
  border-radius: 50%;
  border-right-color: #004dff;
  animation: spinner-a4dj62 1s infinite linear;
}

.spinner::before,
.spinner::after {
  border: inherit;
  border-radius: 50%;
  margin: 2px;
  animation: spinner-a4dj62 2s infinite;
  content: '';
  grid-area: 1/1;
}

.spinner::after {
  margin: 8px;
  animation-duration: 3s;
}

@keyframes spinner-a4dj62 {
  100% {
    transform: rotate(1turn);
  }
}
</style>
