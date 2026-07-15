<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const posts = ref([]);
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref('');

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const filterRegion = ref('');
const filterCategory = ref('');
const filterLocationId = ref('');
const selectedFilterLocation = ref(null);

const regionOptions = ['서울', '부산', '광주_전라권', '구미_경북권', '대전_충청권'];
const categoryOptions = ['잡담', '후기', '질문', '구인'];
const locationCategoryOptions = ['관광지', '문화시설', '축제공연행사', '여행코스', '레포츠', '숙박', '쇼핑', '음식점'];

// 입력 폼 상태 관리
const isFormOpen = ref(false);
const selectedCategory = ref('잡담');
const newTitle = ref('');
const newRegion = ref('');
const newContent = ref('');
const newLocationId = ref('');
const newThumbnailUrl = ref('');
const newPassword = ref('');
const selectedNewLocation = ref(null);

// 명소 검색 모달 상태
const isLocationModalOpen = ref(false);
const locationModalScope = ref('create');
const locationSearchRegion = ref('');
const locationSearchCategory = ref('');
const locationSearchKeyword = ref('');
const loadedLocations = ref([]);
const isLocationLoading = ref(false);

const normalizeLocationId = (value) => {
  const text = String(value ?? '').trim();
  if (!/^\d+$/.test(text)) return '';
  return Number(text) > 0 ? text : '';
};

const fetchLocationById = async (locationId) => {
  if (!locationId) return null;
  try {
    const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error(error);
    return null;
  }
};

const buildKakaoMapLink = (location) => {
  if (!location) return 'https://map.kakao.com/';

  const address = String(location.address || '').trim();
  const name = String(location.name || '').trim();

  // 주소 검색을 우선 사용해 실제 도로명/지번 위치로 이동한다.
  if (address) {
    const query = [address, name].filter(Boolean).join(' ');
    return `https://map.kakao.com/?q=${encodeURIComponent(query)}`;
  }

  const mapx = Number(location.mapx);
  const mapy = Number(location.mapy);
  if (Number.isFinite(mapx) && Number.isFinite(mapy)) {
    return `https://map.kakao.com/link/map/${encodeURIComponent(name || '명소')},${mapy},${mapx}`;
  }

  if (name) {
    return `https://map.kakao.com/?q=${encodeURIComponent(name)}`;
  }

  return 'https://map.kakao.com/';
};

const buildLocationPostsRoute = (location) => {
  const locationId = String(location?.id ?? '').trim();
  if (!/^\d+$/.test(locationId)) {
    return { path: '/posts' };
  }
  return { path: '/posts', query: { location_id: locationId } };
};

const syncLocationFilterFromRoute = async () => {
  const routeLocationId = normalizeLocationId(route.query.location_id);

  if (!routeLocationId) {
    filterLocationId.value = '';
    selectedFilterLocation.value = null;
    return;
  }

  if (filterLocationId.value !== routeLocationId) {
    filterLocationId.value = routeLocationId;
  }

  if (!selectedFilterLocation.value || String(selectedFilterLocation.value.id) !== routeLocationId) {
    selectedFilterLocation.value = await fetchLocationById(Number(routeLocationId));
  }
};

const syncRouteWithLocationFilter = async () => {
  const currentLocationId = normalizeLocationId(route.query.location_id);
  const nextLocationId = normalizeLocationId(filterLocationId.value);
  if (currentLocationId === nextLocationId) return;

  const nextQuery = { ...route.query };
  if (nextLocationId) {
    nextQuery.location_id = nextLocationId;
  } else {
    delete nextQuery.location_id;
  }

  await router.replace({
    path: '/posts',
    query: nextQuery,
  });
};

const buildPostsUrl = () => {
  const params = new URLSearchParams();
  if (filterRegion.value) params.set('region', filterRegion.value);
  if (filterCategory.value) params.set('category', filterCategory.value);
  if (filterLocationId.value) params.set('location_id', filterLocationId.value);
  return `${API_BASE_URL}/api/posts?${params.toString()}`;
};

const fetchPosts = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const response = await fetch(buildPostsUrl());
    if (!response.ok) {
      throw new Error('게시글 목록을 불러오지 못했습니다.');
    }
    posts.value = await response.json();
  } catch (error) {
    console.error(error);
    errorMessage.value = '게시글 목록 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.';
  } finally {
    isLoading.value = false;
  }
};

const filteredLocations = computed(() => {
  const keyword = locationSearchKeyword.value.trim().toLowerCase();
  if (!keyword) {
    return loadedLocations.value;
  }

  return loadedLocations.value.filter((location) => {
    const name = String(location?.name || '').toLowerCase();
    const address = String(location?.address || '').toLowerCase();
    return name.includes(keyword) || address.includes(keyword);
  });
});

const resetModalLocations = () => {
  loadedLocations.value = [];
  locationSearchKeyword.value = '';
};

const openLocationModal = (scope) => {
  locationModalScope.value = scope;
  isLocationModalOpen.value = true;

  if (scope === 'create') {
    locationSearchRegion.value = newRegion.value || '';
  } else {
    locationSearchRegion.value = filterRegion.value || '';
  }

  locationSearchCategory.value = '';
  resetModalLocations();
};

const closeLocationModal = () => {
  if (isLocationLoading.value) {
    return;
  }
  isLocationModalOpen.value = false;
};

const loadLocationsByRegionAndCategory = async () => {
  if (!locationSearchRegion.value || !locationSearchCategory.value) {
    alert('권역과 카테고리를 먼저 선택해주세요.');
    return;
  }

  try {
    isLocationLoading.value = true;
    resetModalLocations();

    const params = new URLSearchParams({
      region: locationSearchRegion.value,
      category: locationSearchCategory.value,
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
    isLocationLoading.value = false;
  }
};

const selectLocation = async (location) => {
  if (locationModalScope.value === 'create') {
    newRegion.value = location.region;
    newLocationId.value = String(location.id);
    newThumbnailUrl.value = location.image_url || '';
    selectedNewLocation.value = location;
  } else {
    filterRegion.value = location.region;
    filterLocationId.value = String(location.id);
    selectedFilterLocation.value = location;
    await syncRouteWithLocationFilter();
    await fetchPosts();
  }

  closeLocationModal();
};

const clearSelectedLocation = async (scope) => {
  if (scope === 'create') {
    newLocationId.value = '';
    newThumbnailUrl.value = '';
    selectedNewLocation.value = null;
    return;
  }

  filterLocationId.value = '';
  selectedFilterLocation.value = null;
  await syncRouteWithLocationFilter();
  await fetchPosts();
};

watch(newRegion, (nextRegion) => {
  if (!selectedNewLocation.value) return;
  if (selectedNewLocation.value.region !== nextRegion) {
    newLocationId.value = '';
    newThumbnailUrl.value = '';
    selectedNewLocation.value = null;
  }
});

watch(filterRegion, async (nextRegion) => {
  if (!selectedFilterLocation.value) return;
  if (selectedFilterLocation.value.region !== nextRegion) {
    filterLocationId.value = '';
    selectedFilterLocation.value = null;
    await syncRouteWithLocationFilter();
    await fetchPosts();
  }
});

watch(
  () => route.query.location_id,
  async () => {
    await syncLocationFilterFromRoute();
    await fetchPosts();
  },
  { immediate: true }
);

// 게시글 추가
const addPost = async () => {
  if (isSubmitting.value) {
    return;
  }

  if (!newTitle.value || !newRegion.value || !newContent.value || !newPassword.value) {
    alert('카테고리, 제목, 지역, 본문, 비밀번호를 모두 입력해주세요!');
    return;
  }

  if (!regionOptions.includes(newRegion.value)) {
    alert('지역은 지정된 5개 권역 중에서 선택해야 합니다.');
    return;
  }

  const payload = {
    title: newTitle.value.trim(),
    content: newContent.value.trim(),
    password: newPassword.value,
    category: selectedCategory.value,
  };

  payload.region = newRegion.value;
  if (newLocationId.value.trim()) {
    payload.location_id = Number(newLocationId.value.trim());
    payload.thumbnail_url = newThumbnailUrl.value || null;
  }

  try {
    isSubmitting.value = true;
    const response = await fetch(`${API_BASE_URL}/api/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const detail = errorBody?.detail || '게시글 등록에 실패했습니다.';
      throw new Error(String(detail));
    }

    await fetchPosts();
  } catch (error) {
    console.error(error);
    alert(error.message || '게시글 등록에 실패했습니다.');
    return;
  } finally {
    isSubmitting.value = false;
  }

  // 입력창 초기화 및 폼 닫기
  newTitle.value = '';
  newRegion.value = '';
  newContent.value = '';
  newLocationId.value = '';
  newThumbnailUrl.value = '';
  selectedNewLocation.value = null;
  newPassword.value = '';
  selectedCategory.value = '잡담';
  isFormOpen.value = false;
};

const goToDetail = (id) => {
  const locationId = normalizeLocationId(filterLocationId.value);
  router.push({
    path: `/posts/${id}`,
    query: locationId ? { location_id: locationId } : {},
  });
};
</script>

<template>
  <div class="list-container">
    
    <section class="write-accordion">
      <div class="accordion-header" @click="isFormOpen = !isFormOpen">
        <div class="header-text">
          <h2>명소에 대한 이야기를 남겨주세요!</h2>
          <p>이곳을 클릭하여 이야기와 유용한 꿀팁을 들려주세요.</p>
        </div>
        <span class="arrow-icon" :class="{ open: isFormOpen }">▼</span>
      </div>

      <div v-if="isFormOpen" class="accordion-content">
        <div class="input-group">
          <div class="form-item">
            <label>카테고리</label>
            <div class="category-selector">
              <button 
                v-for="cat in categoryOptions" 
                :key="cat"
                type="button"
                :class="['category-btn', { active: selectedCategory === cat }]"
                @click="selectedCategory = cat"
              >
                {{ cat }}
              </button>
            </div>
          </div>

          <div class="form-item">
            <label>제목</label>
            <input v-model="newTitle" type="text" placeholder="명소를 드러내는 멋진 제목을 작성해 주세요" />
          </div>

          <div class="form-item">
            <label>지역 위치</label>
            <select v-model="newRegion">
              <option value="" disabled>권역을 선택하세요</option>
              <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>연결할 명소 <span class="sub-label">(선택값)</span></label>
            <div class="location-picker-row">
              <button type="button" class="btn-location-picker" @click="openLocationModal('create')">
                권역/카테고리로 명소 찾기
              </button>
              <button
                v-if="selectedNewLocation"
                type="button"
                class="btn-clear-selection"
                @click="clearSelectedLocation('create')"
              >
                선택 해제
              </button>
            </div>
            <div v-if="selectedNewLocation" class="selected-location-card">
              <strong>{{ selectedNewLocation.name }}</strong>
              <span>{{ selectedNewLocation.region }} · {{ selectedNewLocation.category }}</span>
              <small>{{ selectedNewLocation.address || '주소 정보 없음' }}</small>\
              <a
                class="location-link"
                :href="buildKakaoMapLink(selectedNewLocation)"
                target="_blank"
                rel="noopener noreferrer"
              >
                카카오지도로 이동
              </a>\
            </div>
            <p v-else class="sub-label">명소를 선택하지 않아도 게시글 등록이 가능합니다.</p>
          </div>

          <div class="form-item">
            <label>이야기 본문</label>
            <textarea v-model="newContent" placeholder="꿀팁이나 생각을 자유롭게 들려주세요."></textarea>
          </div>

          <div class="form-item">
            <label>비밀번호 설정 <span class="sub-label">(글 수정/삭제 시 필요합니다)</span></label>
            <input v-model="newPassword" type="password" placeholder="비밀번호 4자리 입력" maxlength="8" />
          </div>
        </div>

        <button class="btn-submit-airbnb" :disabled="isSubmitting" @click="addPost">
          {{ isSubmitting ? '등록 중...' : '이야기 등록하기' }}
        </button>
      </div>
    </section>

    <section class="grid-section">
      <h2 class="section-title">지역에 대한 사람들의 생각을 확인해보세요 ✈️</h2>

      <div class="filter-toolbar">
        <select v-model="filterRegion" @change="fetchPosts">
          <option value="">전체 권역</option>
          <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
        </select>

        <select v-model="filterCategory" @change="fetchPosts">
          <option value="">전체 카테고리</option>
          <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
        </select>

        <button type="button" class="btn-location-picker" @click="openLocationModal('filter')">
          명소 조건 선택
        </button>

        <button
          v-if="selectedFilterLocation"
          type="button"
          class="btn-clear-selection"
          @click="clearSelectedLocation('filter')"
        >
          명소 조건 해제
        </button>

        <button type="button" class="btn-refresh" @click="fetchPosts">검색</button>
      </div>

      <div v-if="selectedFilterLocation" class="selected-location-card filter-card">
        <strong>명소 조건: {{ selectedFilterLocation.name }}</strong>
        <span>{{ selectedFilterLocation.region }} · {{ selectedFilterLocation.category }}</span>
        <small>{{ selectedFilterLocation.address || '주소 정보 없음' }}</small>
        <a
          class="location-link"
          :href="buildKakaoMapLink(selectedFilterLocation)"
          target="_blank"
          rel="noopener noreferrer"
        >
          카카오지도로 이동
        </a>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="isLoading" class="state-text">게시글을 불러오는 중입니다...</p>
      <p v-else-if="posts.length === 0" class="state-text">조건에 맞는 게시글이 없습니다.</p>
      
      <div class="grid-container">
          <div v-for="post in posts" :key="post.id" class="post-card" @click="goToDetail(post.id)">
            <div
              class="card-image-field"
              :class="{ 'with-thumb': !!post.thumbnail_url }"
              :style="post.thumbnail_url ? { backgroundImage: `url(${post.thumbnail_url})` } : {}"
            >
            <span class="category-badge">{{ post.category }}</span>
            <span class="location-badge">{{ post.region || '지역 미지정' }}</span>
          </div>
          
          <div class="card-content">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.content.slice(0, 25) }}{{ post.content.length > 25 ? '...' : '' }}</p>
            
            <div class="card-footer">
              <span class="view-detail-text">클릭하여 상세 보기</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="isLocationModalOpen" class="location-modal-overlay" @click.self="closeLocationModal">
      <div class="location-modal">
        <div class="location-modal-header">
          <h3>명소 검색</h3>
          <button type="button" class="btn-close-modal" :disabled="isLocationLoading" @click="closeLocationModal">닫기</button>
        </div>

        <p class="sub-label">권역과 카테고리를 선택해 목록을 불러온 뒤, 키워드로 빠르게 찾을 수 있어요.</p>

        <div class="location-modal-controls">
          <select v-model="locationSearchRegion">
            <option value="" disabled>권역 선택</option>
            <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
          </select>

          <select v-model="locationSearchCategory">
            <option value="" disabled>카테고리 선택</option>
            <option v-for="cat in locationCategoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>

          <button type="button" class="btn-refresh" :disabled="isLocationLoading" @click="loadLocationsByRegionAndCategory">
            {{ isLocationLoading ? '불러오는 중...' : '목록 불러오기' }}
          </button>
        </div>

        <div class="location-modal-search">
          <input
            v-model="locationSearchKeyword"
            type="text"
            placeholder="불러온 목록에서 명소명/주소 검색"
          />
        </div>

        <p v-if="isLocationLoading" class="state-text">명소 목록을 조회 중입니다...</p>
        <p v-else-if="loadedLocations.length === 0" class="state-text">먼저 권역/카테고리를 선택하고 목록을 불러와 주세요.</p>
        <p v-else-if="filteredLocations.length === 0" class="state-text">검색 결과가 없습니다.</p>

        <ul v-else class="location-results">
          <li
            v-for="location in filteredLocations"
            :key="location.id"
            class="location-result-item"
            @click="selectLocation(location)"
          >
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
.list-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 24px;
}

/* 1. 아코디언 스타일 글쓰기 폼 디자인 */
.write-accordion {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(0,0,0,0.02);
  margin-bottom: 48px;
  transition: box-shadow 0.2s;
}

.write-accordion:hover {
  box-shadow: 0 10px 24px rgba(0,0,0,0.05);
}

.accordion-header {
  padding: 24px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background-color: #ffffff;
}

.header-text h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin-bottom: 4px;
}

.header-text p {
  font-size: 0.9rem;
  color: var(--color-airbnb-gray);
}

.arrow-icon {
  font-size: 0.8rem;
  color: var(--color-airbnb-gray);
  transition: transform 0.2s;
}

.arrow-icon.open {
  transform: rotate(180deg);
}

.accordion-content {
  padding: 0 30px 30px 30px;
  border-top: 1px solid var(--color-border);
  background-color: #FCFCFC;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 24px;
  margin-bottom: 24px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
}

.sub-label {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-airbnb-gray);
}

/* 토스 감성의 카테고리 셀렉터 */
.category-selector {
  display: flex;
  gap: 8px;
  background-color: #EEEEEE;
  padding: 4px;
  border-radius: 10px;
  width: fit-content;
}

.category-btn {
  border: 1px solid transparent;
  background: none;
  padding: 8px 20px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  color: var(--color-airbnb-gray);
  transition: all 0.2s;
}

.category-btn.active {
  background-color: white;
  color: var(--color-airbnb-dark);
  border-color: #333;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

.form-item input, .form-item textarea, .form-item select {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.95rem;
  outline: none;
  background-color: white;
  transition: border-color 0.2s;
}

.form-item input:focus, .form-item textarea:focus, .form-item select:focus {
  border-color: var(--color-airbnb-red);
}

.form-item textarea {
  height: 120px;
  resize: vertical;
}

.location-picker-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-location-picker {
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  background-color: white;
  color: #1f1f1f;
  padding: 10px 14px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-clear-selection {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-color: #f7f7f7;
  color: #575757;
  padding: 10px 12px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
}

.selected-location-card {
  margin-top: 10px;
  border: 1px solid #d9d9d9;
  background-color: #fafafa;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-location-card strong {
  font-size: 0.92rem;
  color: var(--color-airbnb-dark);
}

.selected-location-card span,
.selected-location-card small {
  color: var(--color-airbnb-gray);
  line-height: 1.4;
}

.location-link {
  color: var(--color-airbnb-red);
  font-size: 0.84rem;
  font-weight: 700;
  text-decoration: none;
}

.location-link:hover {
  text-decoration: underline;
}

.location-link-row {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.location-link-btn {
  color: var(--color-airbnb-dark);
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 4px 10px;
  background-color: #f7f7f7;
}

.location-link-btn:hover {
  background-color: #efefef;
}

.filter-card {
  margin-top: -6px;
  margin-bottom: 14px;
}

/* 가시성 좋은 등록 버튼 */
.btn-submit-airbnb {
  width: 100%;
  background-color: var(--color-airbnb-red);
  color: white;
  border: 2px solid #8f0d2f;
  padding: 16px;
  font-size: 1.05rem;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
  transition: filter 0.2s;
  box-shadow: 0 4px 12px rgba(224, 26, 79, 0.2);
}

.btn-submit-airbnb:hover {
  filter: brightness(0.9);
}

.btn-submit-airbnb:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* 2. 게시물 리스트 그리드 영역 (한 줄에 3개 노출) */
.grid-section {
  margin-top: 20px;
}

.section-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 28px;
  color: var(--color-airbnb-dark);
}

.filter-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.filter-toolbar select,
.filter-toolbar input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.9rem;
  min-width: 150px;
}

.btn-refresh {
  border: 2px solid #1f1f1f;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.9rem;
  font-weight: 700;
  background-color: var(--color-airbnb-dark);
  color: white;
  cursor: pointer;
}

.state-text {
  margin: 0 0 14px;
  font-size: 0.92rem;
  color: var(--color-airbnb-gray);
}

.error-text {
  margin: 0 0 14px;
  font-size: 0.92rem;
  color: #b42318;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 넓은 화면에서 한 줄에 무조건 3개씩 배치 */
  gap: 24px;
}

/* 반응형 처리 (화면이 모바일 수준으로 좁아지면 1열로 전환) */
@media (max-width: 900px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
  }
  .location-link {
    align-self: flex-end;
    margin-right:4px;
  }
}
@media (max-width: 600px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
  
  .location-link {
    align-self: flex-end;
    margin-right:4px;
  }
}

.post-card {
  background-color: white;
  border: 2px solid #8d8d8d;
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
  border-color: #2f2f2f;
}

.card-image-field {
  height: 160px;
  background-color: #EBEBEB;
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #9d9d9d;
}

.card-image-field.with-thumb::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.28), rgba(0, 0, 0, 0.05));
}

.card-image-field .category-badge,
.card-image-field .location-badge {
  position: relative;
  z-index: 1;
}

.category-badge {
  background-color: var(--color-airbnb-dark);
  color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
}

.location-badge {
  background-color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid var(--color-border);
}

.card-content {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.card-desc {
  font-size: 0.88rem;
  color: var(--color-airbnb-gray);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 16px;
  line-height: 1.4;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #d2d2d2;
}

.likes {
  font-size: 0.85rem;
  font-weight: 600;
}

.view-detail-text {
  font-size: 0.82rem;
  color: var(--color-airbnb-gray);
  font-weight: 600;
}

.location-modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 20px;
}

.location-modal {
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

.location-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.location-modal-header h3 {
  margin: 0;
  font-size: 1.15rem;
}

.btn-close-modal {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-color: #f7f7f7;
  padding: 8px 12px;
  cursor: pointer;
}

.location-modal-controls {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
}

.location-modal-controls select,
.location-modal-search input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.92rem;
}

.location-results {
  margin: 0;
  padding: 0;
  list-style: none;
  overflow-y: auto;
  border-top: 1px solid #efefef;
}

.location-result-item {
  padding: 12px 4px;
  border-bottom: 1px solid #efefef;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
}

.location-result-item:hover {
  background-color: #f8f8f8;
}

.location-result-item strong {
  font-size: 0.96rem;
}

.location-result-item span,
.location-result-item small {
  color: var(--color-airbnb-gray);
  line-height: 1.4;
}

@media (max-width: 700px) {
  .location-modal-controls {
    grid-template-columns: 1fr;
  }
}
</style>