<script setup>
import CommonHeader from './components/CommonHeader.vue';
</script>

<template>
  <div class="app-layout">
    <CommonHeader />
    <router-view />
  </div>
</template>

<style>
@import './assets/main.css';
</style>