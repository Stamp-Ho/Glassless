<script setup>
import { ref, onMounted } from "vue";

// 1. 상태 정의 (사이드바 검색 필터용)
const searchRegion = ref("");
const selectedActivities = ref([]);

const activities = [
  { id: "cafe", label: "☕ 감성 카페 탐방" },
  { id: "trekking", label: "🥾 하이킹/트래킹" },
  { id: "ocean", label: "🏖️ 해변/수상 레저" },
  { id: "museum", label: "🏛️ 역사/박물관" },
  { id: "night", label: "🌃 야경 명소" },
];

// 2. 지도 컨테이너 상태 정의 (추후 API 연결용)
const mapContainer = ref(null);

onMounted(() => {
  console.log("지도 뷰포트 준비 완료");
});

// 3. 기능 처리 함수들
const handleSearch = () => {
  alert(
    `검색 요청\n지역: ${searchRegion.value || "전체"}\n선택한 활동: ${selectedActivities.value.join(", ") || "없음"}`,
  );
};

const resetFilters = () => {
  searchRegion.value = "";
  selectedActivities.value = [];
};
</script>

<template>
  <div class="map-search-layout">
    <aside class="search-sidebar">
      <div class="sidebar-header">
        <h2>어떤 여행을 <br />원하시나요?</h2>
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
              :class="[
                'activity-checkbox-card',
                { checked: selectedActivities.includes(act.label) },
              ]"
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
        <button class="btn-search" @click="handleSearch">검색</button>
      </div>
    </aside>

    <main class="map-viewport" ref="mapContainer">
      <div class="map-placeholder">
        <div class="map-guide-card">
          <span class="map-icon">🗺️</span>
          <h3>여기는 실시간 지도 영역입니다</h3>
          <p>
            현재 선택된 필터에 매칭되는 명소들이 지도 위에 마커로 표시됩니다.<br />
            <span class="highlight"
              >(추후 Kakao Maps 또는 Google Maps API 장착 공간)</span
            >
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* 메인 아웃라인 레이아웃 설정 */
.map-search-layout {
  display: flex;
  width: 100%;
  height: calc(100vh - 73px);
  overflow: hidden;
}

/* 왼쪽 사이드바 디자인 */
.search-sidebar {
  width: 380px;
  background-color: white;
  border-right: 1px solid var(--color-border, #ebebeb);
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
  color: var(--color-airbnb-dark, #222222);
}

.sidebar-header p {
  font-size: 0.88rem;
  color: var(--color-airbnb-gray, #767676);
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
  color: var(--color-airbnb-dark, #222222);
  letter-spacing: 0.5px;
}

/* 지역 입력 박스 */
.input-wrapper input {
  width: 100%;
  border: 1px solid var(--color-border, #ebebeb);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 0.95rem;
  outline: none;
  transition:
    border-color 0.2s,
    background-color 0.2s;
  background-color: #fafafa;
  box-sizing: border-box;
}

.input-wrapper input:focus {
  border-color: var(--color-airbnb-red, #ff5a5f);
  background-color: white;
}

/* 체크박스 목록 */
.activity-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-checkbox-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--color-border, #ebebeb);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: white;
}

.activity-checkbox-card input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-airbnb-red, #ff5a5f);
  cursor: pointer;
}

.activity-checkbox-card span {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-airbnb-dark, #222222);
}

.activity-checkbox-card:hover {
  background-color: #fafafa;
  border-color: var(--color-airbnb-gray, #767676);
}

.activity-checkbox-card.checked {
  border-color: var(--color-airbnb-red, #ff5a5f);
  background-color: #fff0f2;
}

/* 하단 버튼 및 액션 스타일 */
.sidebar-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  border-top: 1px solid var(--color-border, #ebebeb);
  padding-top: 20px;
}

.btn-reset {
  flex: 1;
  background: white;
  border: 1px solid var(--color-border, #ebebeb);
  padding: 14px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-reset:hover {
  background-color: #f5f5f5;
}

.btn-search {
  flex: 2;
  background-color: var(--color-airbnb-red, #ff5a5f);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(255, 90, 95, 0.2);
  transition:
    transform 0.1s,
    filter 0.2s;
}
.btn-search:hover {
  filter: brightness(0.9);
}
.btn-search:active {
  transform: scale(0.98);
}

/* 오른쪽 지도 전용 뷰포트 스타일 */
.map-viewport {
  flex: 1;
  height: 100%;
  background-color: #e3ece9;
  position: relative;
}

.map-placeholder {
  width: 100%;
  height: 100%;
  background-image:
    radial-gradient(circle, #cfddd8 10%, transparent 10.5%),
    radial-gradient(circle, #cfddd8 10%, transparent 10.5%);
  background-size: 24px 24px;
  background-position:
    0 0,
    12px 12px;
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
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08);
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
  color: var(--color-airbnb-dark, #222222);
  margin-bottom: 12px;
}

.map-guide-card p {
  font-size: 0.9rem;
  color: var(--color-airbnb-gray, #767676);
  line-height: 1.6;
}

.highlight {
  display: inline-block;
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--color-airbnb-red, #ff5a5f);
  font-weight: 600;
}

/* 태블릿 및 모바일용 반응형 스타일 */
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
    border-bottom: 1px solid var(--color-border, #ebebeb);
  }

  .map-viewport {
    height: 400px;
  }
}
</style>
