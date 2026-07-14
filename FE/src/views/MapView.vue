<script setup>
import { ref } from 'vue';

// 검색 조건 상태 관리
const searchRegion = ref('');
const selectedActivities = ref([]);

// 제공할 액티비티 목록 데이터
const activities = [
  { id: 'cafe', label: '☕ 감성 카페 탐방' },
  { id: 'trekking', label: '🥾 하이킹/트래킹' },
  { id: 'ocean', label: '🏖️ 해변/수상 레저' },
  { id: 'museum', label: '🏛️ 역사/박물관' },
  { id: 'night', label: '🌃 야경 명소' }
];

// 검색 실행 함수
const handleSearch = () => {
  alert(`검색 요청\n지역: ${searchRegion.value || '전체'}\n선택한 활동: ${selectedActivities.value.join(', ') || '없음'}`);
  // 추후 여기에 지도 API 마커 필터링 로직이 연동됩니다!
};

// 필터 초기화
const resetFilters = () => {
  searchRegion.value = '';
  selectedActivities.value = [];
};
</script>

<template>
  <div class="map-search-layout">
    
    <aside class="search-sidebar">
      <div class="sidebar-header">
        <h2>어떤 여행을 <br>원하시나요?</h2>
        <p>조건에 맞는 지역 명소를 지도에서 찾아보세요.</p>
      </div>

      <div class="filter-group">
        <div class="filter-item">
          <label class="filter-label">여행 지역</label>
          <div class="input-wrapper">
            <input 
              v-model="searchRegion" 
              type="text" 
              placeholder="예: 부산 수영구, 제주 애월읍" 
              @keyup.enter="handleSearch"
            />
          </div>
        </div>

        <div class="filter-item">
          <label class="filter-label">원하는 활동 (중복 선택)</label>
          <div class="activity-grid">
            <label 
              v-for="act in activities" 
              :key="act.id" 
              :class="['activity-checkbox-card', { checked: selectedActivities.includes(act.label) }]"
            >
              <input 
                type="checkbox" 
                :value="act.label" 
                v-model="selectedActivities"
              />
              <span>{{ act.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <div class="sidebar-actions">
        <button class="btn-reset" @click="resetFilters">필터 초기화</button>
        <button class="btn-search" @click="handleSearch">조건 검색</button>
      </div>
    </aside>

    <main class="map-viewport">
      <div class="map-placeholder">
        <div class="map-guide-card">
          <span class="map-icon">🗺️</span>
          <h3>여기는 실시간 지도 영역입니다</h3>
          <p>
            현재 선택된 필터에 매칭되는 명소들이 지도 위에 마커로 표시됩니다.<br>
            <span class="highlight">(추후 Kakao Maps 또는 Google Maps API 장착 공간)</span>
          </p>
        </div>
      </div>
    </main>

  </div>
</template>

<style scoped>
/* 좌측 고정 사이드바 + 우측 꽉 찬 지도 구성을 위한 그리드 레이아웃 */
.map-search-layout {
  display: flex;
  height: calc(100vh - 73px); /* 헤더 높이를 뺀 나머지 화면을 꽉 채움 */
  overflow: hidden;
}

/* 1. 좌측 검색 사이드바 스타일링 */
.search-sidebar {
  width: 380px;
  background-color: white;
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 32px 24px;
  box-sizing: border-box;
  z-index: 10;
  overflow-y: auto;
}

.sidebar-header h2 {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.3;
  margin-bottom: 8px;
  color: var(--color-airbnb-dark);
}

.sidebar-header p {
  font-size: 0.88rem;
  color: var(--color-airbnb-gray);
  line-height: 1.4;
}

.filter-group {
  margin-top: 32px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-label {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-airbnb-dark);
  letter-spacing: 0.5px;
}

.input-wrapper input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
  background-color: #FAFAFA;
}

.input-wrapper input:focus {
  border-color: var(--color-airbnb-red);
  background-color: white;
}

/* 액티비티 체크박스 리스트 디자인 */
.activity-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-checkbox-card {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  background-color: white;
}

.activity-checkbox-card input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-airbnb-red); /* 에어비앤비 레드 컬러 적용 */
  cursor: pointer;
}

.activity-checkbox-card span {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-airbnb-dark);
}

.activity-checkbox-card:hover {
  background-color: #FAFAFA;
  border-color: var(--color-airbnb-gray);
}

/* 체크됐을 때 카드 보더 하이라이팅 */
.activity-checkbox-card.checked {
  border-color: var(--color-airbnb-red);
  background-color: #FFF0F2;
}

/* 사이드바 하단 버튼 영역 */
.sidebar-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  border-top: 1px solid var(--color-border);
  padding-top: 20px;
}

.btn-reset {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 14px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  color: var(--color-airbnb-gray);
  transition: background-color 0.2s;
}

.btn-reset:hover {
  background-color: #F5F5F5;
  color: var(--color-airbnb-dark);
}

.btn-search {
  flex: 1;
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 14px 20px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-search:hover {
  filter: brightness(0.9);
}

/* 2. 우측 지도 영역 스타일링 (화면 꽉 차게 설정) */
.map-viewport {
  flex: 1;
  height: 100%;
  background-color: #E3ECE9; /* 세련된 미색 지도 배경 */
  position: relative;
}

.map-placeholder {
  width: 100%;
  height: 100%;
  background-image: radial-gradient(circle, #CFDDD8 10%, transparent 10.5%), radial-gradient(circle, #CFDDD8 10%, transparent 10.5%);
  background-size: 24px 24px;
  background-position: 0 0, 12px 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  box-sizing: border-box;
}

.map-guide-card {
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 40px;
  border-radius: var(--radius-airbnb);
  box-shadow: 0 20px 50px rgba(0,0,0,0.08);
  text-align: center;
  max-width: 460px;
}

.map-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 16px;
}

.map-guide-card h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin-bottom: 12px;
}

.map-guide-card p {
  font-size: 0.9rem;
  color: var(--color-airbnb-gray);
  line-height: 1.6;
}

.highlight {
  display: inline-block;
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--color-airbnb-red);
  font-weight: 600;
}

/* 모바일/태블릿 반응형 (화면이 많이 좁아지면 가로 배치에서 세로 배치 구조로 자동 전환) */
@media (max-width: 768px) {
  .map-search-layout {
    flex-direction: column;
    height: auto;
    overflow: visible;
  }
  
  .search-sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
  
  .map-viewport {
    height: 400px;
  }
}
</style>