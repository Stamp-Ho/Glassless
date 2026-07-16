<script setup>
import { computed, ref } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const regionOptions = ['서울', '부산', '광주_전라권', '구미_경북권', '대전_충청권'];
const locationCategoryOptions = ['관광지', '문화시설', '축제공연행사', '여행코스', '레포츠', '숙박', '쇼핑', '음식점'];

const isSearchModalOpen = ref(false);
const selectedRegion = ref('');
const selectedLocationCategory = ref('');
const searchKeyword = ref('');

const isLoadingLocations = ref(false);
const loadedLocations = ref([]);
const selectedLocation = ref(null);

const filteredLocations = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) {
    return loadedLocations.value;
  }

  return loadedLocations.value.filter((location) => {
    const name = String(location?.name || '').toLowerCase();
    const address = String(location?.address || '').toLowerCase();
    return name.includes(keyword) || address.includes(keyword);
  });
});

const openSearchModal = () => {
  isSearchModalOpen.value = true;
};

const closeSearchModal = () => {
  if (isLoadingLocations.value) return;
  isSearchModalOpen.value = false;
};

const loadLocations = async () => {
  if (!selectedRegion.value || !selectedLocationCategory.value) {
    alert('권역과 카테고리를 먼저 선택해주세요.');
    return;
  }

  try {
    isLoadingLocations.value = true;
    loadedLocations.value = [];
    searchKeyword.value = '';

    const params = new URLSearchParams({
      region: selectedRegion.value,
      category: selectedLocationCategory.value,
      limit: '100',
      offset: '0',
    });

    const response = await fetch(`${API_BASE_URL}/api/locations?${params.toString()}`);
    if (!response.ok) {
      throw new Error('명소 목록을 불러오지 못했습니다.');
    }

    const result = await response.json();
    loadedLocations.value = Array.isArray(result) ? result : [];
  } catch (error) {
    console.error(error);
    alert(error.message || '명소 목록 조회에 실패했습니다.');
  } finally {
    isLoadingLocations.value = false;
  }
};

const selectLocation = (location) => {
  selectedLocation.value = location;
  closeSearchModal();
};

const resetSelectedLocation = () => {
  selectedLocation.value = null;
};
</script>

<template>
  <div class="map-search-layout">
    <main class="map-viewport">
      <div class="map-placeholder">
        <div class="map-guide-card">
          <span class="map-icon">🗺️</span>
          <h3>권역과 카테고리로 명소를 찾아보세요</h3>
          <p>검색 모달에서 권역 → 카테고리 순서로 목록을 불러온 뒤, 키워드로 명소를 찾을 수 있습니다.</p>
          <button class="btn-search" @click="openSearchModal">명소 검색 열기</button>

          <div v-if="selectedLocation" class="selected-location-panel">
            <div class="selected-header">
              <strong>선택된 명소</strong>
              <button class="btn-reset" @click="resetSelectedLocation">해제</button>
            </div>
            <h4>{{ selectedLocation.name }}</h4>
            <p>{{ selectedLocation.region }} · {{ selectedLocation.category }}</p>
            <small>{{ selectedLocation.address || '주소 정보 없음' }}</small>
          </div>
        </div>
      </div>
    </main>

    <div v-if="isSearchModalOpen" class="search-modal-overlay" @click.self="closeSearchModal">
      <div class="search-modal">
        <div class="search-modal-header">
          <h3>명소 검색</h3>
          <button class="btn-reset" :disabled="isLoadingLocations" @click="closeSearchModal">닫기</button>
        </div>

        <div class="search-controls-row">
          <select v-model="selectedRegion">
            <option value="" disabled>권역 선택</option>
            <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
          </select>

          <select v-model="selectedLocationCategory">
            <option value="" disabled>카테고리 선택</option>
            <option v-for="cat in locationCategoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>

          <button class="btn-search" :disabled="isLoadingLocations" @click="loadLocations">
            {{ isLoadingLocations ? '불러오는 중...' : '목록 불러오기' }}
          </button>
        </div>

        <input
          v-model="searchKeyword"
          class="keyword-input"
          type="text"
          placeholder="불러온 목록에서 명소명/주소 검색"
        />

        <p v-if="isLoadingLocations" class="helper-text">명소 데이터를 불러오는 중입니다...</p>
        <p v-else-if="loadedLocations.length === 0" class="helper-text">권역/카테고리를 선택하고 목록을 불러와 주세요.</p>
        <p v-else-if="filteredLocations.length === 0" class="helper-text">검색 결과가 없습니다.</p>

        <ul v-else class="location-results-list">
          <li v-for="location in filteredLocations" :key="location.id" @click="selectLocation(location)">
            <strong>{{ location.name }}</strong>
            <span>{{ location.region }} · {{ location.category }}</span>
            <small>{{ location.address || '주소 정보 없음' }}</small>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-search-layout {
  position: relative;
  height: calc(100vh - 73px); /* 헤더 높이를 뺀 나머지 화면을 꽉 채움 */
  overflow: hidden;
}

.btn-reset {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 14px;
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
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-search:hover {
  filter: brightness(0.9);
}

.map-viewport {
  width: 100%;
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
  margin-bottom: 18px;
}

.selected-location-panel {
  margin-top: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 12px;
  text-align: left;
  background-color: #fafafa;
}

.selected-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selected-location-panel h4 {
  margin: 0 0 6px;
}

.selected-location-panel p,
.selected-location-panel small {
  margin: 0;
  color: var(--color-airbnb-gray);
}

.search-modal-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
  padding: 20px;
}

.search-modal {
  width: min(760px, 100%);
  max-height: min(86vh, 900px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background-color: white;
  border-radius: 14px;
  border: 1px solid var(--color-border);
  padding: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.search-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.search-modal-header h3 {
  margin: 0;
}

.search-controls-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
}

.search-controls-row select,
.keyword-input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.92rem;
}

.helper-text {
  margin: 0;
  color: var(--color-airbnb-gray);
}

.location-results-list {
  margin: 0;
  padding: 0;
  list-style: none;
  overflow-y: auto;
  border-top: 1px solid #efefef;
}

.location-results-list li {
  padding: 12px 4px;
  border-bottom: 1px solid #efefef;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
}

.location-results-list li:hover {
  background-color: #f8f8f8;
}

.location-results-list span,
.location-results-list small {
  color: var(--color-airbnb-gray);
}

/* 모바일/태블릿 반응형 (화면이 많이 좁아지면 가로 배치에서 세로 배치 구조로 자동 전환) */
@media (max-width: 768px) {
  .map-viewport {
    height: 400px;
  }

  .search-controls-row {
    grid-template-columns: 1fr;
  }
}
</style>