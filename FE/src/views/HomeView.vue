<script setup>
import { ref } from 'vue';

const searchQuery = ref('');
const searchResult = ref(null);

const handleSearch = () => {
  if (!searchQuery.value) return;
  // 임시 검색 결과 매칭 (추후 공공데이터 API 연동 영역)
  searchResult.value = `${searchQuery.value}의 인기 명소: 🏞️ 하늘공원, 🏛️ 역사박물관, ☕ 분위기 좋은 카페 거리`;
};
</script>

<template>
  <main class="main-hero">
    <div class="hero-content">
      <h1 class="hero-title">어디로 떠나시나요?</h1>
      <p class="hero-subtitle">GlassLESS에서 공공데이터 기반 지역 명소 정보를 손쉽게 찾아보세요.</p>
      
      <div class="search-capsule">
        <div class="search-input-field">
          <label>여행지</label>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="목적지 검색 (예: 서울 마포구)" 
            @keyup.enter="handleSearch"
          />
        </div>
        <button class="search-action-btn" @click="handleSearch">
          🔍 검색
        </button>
      </div>

      <div v-if="searchResult" class="search-result-box">
        <h3>🔍 검색 결과</h3>
        <p>{{ searchResult }}</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.main-hero {
  min-height: calc(100vh - 80px);
  background: linear-gradient(180deg, #FFF0F2 0%, #FFFFFF 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 24px;
}

.hero-content {
  text-align: center;
  max-width: 800px;
  width: 100%;
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  color: var(--color-airbnb-dark);
  margin-bottom: 12px;
  letter-spacing: -1.5px;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: var(--color-airbnb-gray);
  margin-bottom: 40px;
}

/* 에어비앤비 검색 캡슐 */
.search-capsule {
  display: flex;
  align-items: center;
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: 40px;
  padding: 10px 10px 10px 32px;
  box-shadow: 0 16px 32px rgba(0,0,0,0.08);
  max-width: 600px;
  margin: 0 auto;
}

.search-input-field {
  flex: 1;
  text-align: left;
}

.search-input-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--color-airbnb-dark);
  text-transform: uppercase;
  margin-bottom: 2px;
}

.search-input-field input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 0.95rem;
  color: var(--color-airbnb-dark);
}

.search-action-btn {
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  border-radius: 24px;
  padding: 12px 24px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-action-btn:hover {
  filter: brightness(0.9);
}

.search-result-box {
  margin-top: 40px;
  padding: 24px;
  background-color: white;
  border-radius: 16px;
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  text-align: left;
}

.search-result-box h3 {
  font-size: 1.1rem;
  margin-bottom: 8px;
  color: var(--color-airbnb-dark);
}
</style>