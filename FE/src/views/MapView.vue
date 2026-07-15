<script setup>
import { ref, onMounted } from "vue";

// 카카오 지도 또는 다른 지도 객체용 상태 정의 (순수 자바스크립트)
const mapContainer = ref(null);
const searchQuery = ref("");

onMounted(() => {
  // 지도 초기화 로직이 들어가는 곳입니다.
  console.log("지도 컴포넌트 마운트 완료");
});

const handleSearch = () => {
  if (!searchQuery.value.trim()) return;
  console.log("검색어:", searchQuery.value);
};
</script>

<template>
  <div class="map-search-layout">
    <div class="search-bar-container">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="장소, 주소, 키워드 검색"
        @keyup.enter="handleSearch"
      />
      <button @click="handleSearch">검색</button>
    </div>

    <div ref="mapContainer" class="map-render-zone"></div>
  </div>
</template>

<style scoped>
.map-search-layout {
  position: relative;
  width: 100%;
  height: calc(100vh - 80px); /* 헤더 높이를 제외한 전체 화면 */
  display: flex;
  flex-direction: column;
}

.search-bar-container {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  display: flex;
  gap: 8px;
  background-color: white;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-bar-container input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  outline: none;
}

.search-bar-container button {
  padding: 8px 16px;
  background-color: var(--color-airbnb-red, #ff5a5f);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.map-render-zone {
  flex: 1;
  width: 100%;
  height: 100%;
  background-color: #e5e3df; /* 지도 로드 전 임시 배경색 */
}
</style>
