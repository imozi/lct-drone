<script setup lang="ts">
import { Primitive } from '..';
</script>

<template>
  <Primitive class="absolute inset-0 flex items-center justify-center bg-slate-50">
    <div class="relative flex size-36 items-center justify-center">
      <div class="l1 color"></div>
      <div class="l2 color"></div>
      <div class="e1 color animation-effect-light"></div>
      <div class="e2 color animation-effect-light-d"></div>
      <div class="e3 animation-effect-rot">X</div>
      <div class="e4 color animation-effect-light"></div>
      <div class="e5 color animation-effect-light-d"></div>
      <div class="e6 animation-effect-scale">*</div>
      <div class="e7 color"></div>
      <div class="e8 color"></div>
    </div>
  </Primitive>
</template>

<style lang="scss">
.color {
  background-color: #4285f4;
}

.l1 {
  position: absolute;
  width: 15px;
  height: 65px;
  animation: move-h 1.2s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
  background-color: #f4b400;
}

.l2 {
  position: absolute;
  width: 15px;
  height: 60px;
  animation: move-v 1.2s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
  background-color: #db4437;
  transform: rotate(90deg);
}

@keyframes move-h {
  0% {
    top: 0;
    opacity: 0;
  }

  25% {
    opacity: 1;
  }

  50% {
    top: 30%;
    opacity: 1;
  }

  75% {
    opacity: 1;
  }

  100% {
    top: 100%;
    opacity: 0;
  }
}

@keyframes move-v {
  0% {
    left: 0;
    opacity: 0;
  }

  25% {
    opacity: 1;
  }

  50% {
    left: 45%;
    opacity: 1;
  }

  75% {
    opacity: 1;
  }

  100% {
    left: 100%;
    opacity: 0;
  }
}

.animation-effect-light {
  animation: effect 0.2s 0.1s infinite linear;
}

.animation-effect-light-d {
  animation: effect 0.3s 0.2s infinite linear;
}

.animation-effect-rot {
  animation: rot 0.8s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
}

.animation-effect-scale {
  animation: scale 0.8s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
}

@keyframes effect {
  0% {
    opacity: 0;
  }

  50% {
    opacity: 1;
  }

  100% {
    opacity: 0;
  }
}

@keyframes rot {
  0% {
    transform: rotate(0deg);
  }

  50% {
    transform: rotate(180deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes scale {
  0% {
    scale: 1;
  }

  50% {
    scale: 1.9;
  }

  100% {
    scale: 1;
  }
}

.e1 {
  position: absolute;
  top: 0;
  left: 8%;
  width: 1px;
  height: 40px;
  background-color: #0f9d58;
  opacity: 0.3;
}

.e2 {
  position: absolute;
  top: 8%;
  left: 0;
  width: 60px;
  height: 1px;
  background-color: #4285f4;
  opacity: 0.8;
}

.e3 {
  position: absolute;
  top: 10%;
  left: 12%;
  color: #4285f4;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 18px;
  font-weight: 900;
}

.e4 {
  position: absolute;
  top: 90%;
  right: 10%;
  width: 1px;
  height: 40px;
  background-color: #db4437;
  opacity: 0.3;
}

.e5 {
  position: absolute;
  top: 100%;
  right: 0;
  width: 40px;
  height: 1px;
  background-color: #f4b400;
  opacity: 0.3;
}

.e6 {
  position: absolute;
  top: 100%;
  right: 0;
  color: #0f9d58;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 32px;
}

.e7 {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 1px;
  height: 20px;
  animation: height 1s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
  background-color: #f4b400;
  transform: rotate(45deg);
}

@keyframes height {
  0% {
    bottom: 0%;
    left: 0%;
    height: 0;
  }

  25% {
    height: 90px;
  }

  50% {
    bottom: 100%;
    left: 100%;
    height: 90px;
  }

  75% {
    height: 0;
  }

  100% {
    bottom: 0%;
    left: 0%;
    height: 0;
  }
}

.e8 {
  position: absolute;
  bottom: 50%;
  left: 0;
  width: 20px;
  height: 1px;
  animation: width 1.5s infinite cubic-bezier(0.65, 0.05, 0.36, 1);
  background-color: #0f9d58; /* Google Green */
}

@keyframes width {
  0% {
    left: 0%;
    width: 0;
  }

  50% {
    left: 100%;
    width: 90px;
  }

  100% {
    left: 0%;
    width: 0;
  }
}
</style>
