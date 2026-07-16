<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute(); // 쿼리 스트링 감지를 위해 추가

const posts = ref([]);
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref('');

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'https://glassless-be.onrender.com'
);

const filterRegion = ref('');
const filterCategory = ref('');
const filterLocationId = ref('');
const selectedFilterLocation = ref(null);
const page = ref(Number(route.query.page || 1));
const perPage = ref(12);
const totalCount = ref(0);

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
const rating = ref(0);
const ratingErrorMessage = ref('');

function setRating(n) {
  rating.value = n;
  // clear previous rating error message
  ratingErrorMessage.value = '';
}

const CLIENT_ID_KEY = 'app_client_id_v1';
const LOCATION_RATING_KEY_PREFIX = 'location_rating_';

async function ensureClientId() {
  let id = localStorage.getItem(CLIENT_ID_KEY);
  if (id) return id;
  // generate from IP + UA + time
  let ip = 'unknown';
  try {
    const resp = await fetch('https://api.ipify.org?format=json');
    if (resp.ok) {
      const j = await resp.json();
      ip = j.ip || ip;
    }
  } catch (e) {
    // ignore
  }
  const ua = navigator.userAgent || 'ua-unknown';
  // NOTE: do not include a timestamp per request; derive id from IP + User-Agent only
  const base = `${ip}|${ua}`;
  try {
    const enc = new TextEncoder().encode(base);
    const hashBuf = await crypto.subtle.digest('SHA-256', enc);
    const hashArray = Array.from(new Uint8Array(hashBuf));
    id = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } catch (e) {
    id = `${ip}-${Math.random().toString(36).slice(2,10)}`;
  }
  localStorage.setItem(CLIENT_ID_KEY, id);
  return id;
}

function hasSubmittedRating(locationId) {
  try {
    const key = LOCATION_RATING_KEY_PREFIX + locationId;
    return !!localStorage.getItem(key);
  } catch (e) { return false; }
}

function storeSubmittedRating(locationId, score) {
  try {
    const key = LOCATION_RATING_KEY_PREFIX + locationId;
    const payload = { score, ts: Date.now() };
    localStorage.setItem(key, JSON.stringify(payload));
  } catch (e) { /* ignore */ }
}


async function submitRatingForLocation(locationId, score) {
  if (!locationId) return;
  // do NOT block submission client-side based on localStorage — always send to server

  const clientId = await ensureClientId();
  try {
    const resp = await fetch(`${API_BASE_URL}/api/locations/${encodeURIComponent(locationId)}/ratings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score, client_id: clientId }),
    });
    if (resp.status === 429) {
      ratingErrorMessage.value = '해당 명소에 이미 별점을 남겼습니다';
      showToast(ratingErrorMessage.value, 'error');
      showRatingFailure(ratingErrorMessage.value);
      return false;
    }
    if (!resp.ok) {
      console.error('rating post failed', resp.status);
      const msg = '별점 등록에 실패했습니다.';
      showToast(msg, 'error');
      showRatingFailure(msg);
      return false;
    }
    // success: persist submission record locally
    storeSubmittedRating(locationId, score);
    showToast('별점이 등록되었습니다.', 'success');
    // refresh details for selected locations if visible
    try {
      if (selectedNewLocation.value && String(selectedNewLocation.value.id) === String(locationId)) {
        await fetchSelectedLocationInfo(locationId, 'create');
      }
      if (selectedFilterLocation.value && String(selectedFilterLocation.value.id) === String(locationId)) {
        await fetchSelectedLocationInfo(locationId, 'filter');
      }
    } catch (e) {
      // ignore
    }
    return true;
  } catch (e) {
    console.error('submitRatingForLocation error', e);
    showToast('별점 등록에 실패했습니다.', 'error');
    return false;
  }
}

// 명소 검색 모달 상태
const isLocationModalOpen = ref(false);
const locationModalScope = ref('create');
const locationSearchRegion = ref('');
const locationSearchCategory = ref('');
const locationSearchKeyword = ref('');
const loadedLocations = ref([]);
const isLocationLoading = ref(false);

// [변경] 현재 쿼리 파라미터를 기반으로 백엔드 API URL 생성
const buildPostsUrl = () => {
  const params = new URLSearchParams();
  if (route.query.region) params.set('region', route.query.region);
  if (route.query.category) params.set('category', route.query.category);
  if (route.query.location_id) params.set('location_id', route.query.location_id);
  params.set('page', String(page.value || 1));
  params.set('per_page', String(perPage.value));
  const url = `${API_BASE_URL}/api/posts?${params.toString()}`;
  console.debug('Fetching posts URL:', url);
  return url;
};

// 유틸: 카카오맵 링크 생성 (템플릿에서 호출됨 — 반드시 정의 필요)
const buildKakaoMapLink = (location) => {
  if (!location) return '#';
  const lat = location.mapy || location.lat || location.y || null;
  const lng = location.mapx || location.lng || location.x || null;
  const title = location.name || location.title || '';
  if (lat == null || lng == null) return '#';
  // format: https://map.kakao.com/link/map/{title},{lat},{lng}
  return `https://map.kakao.com/link/map/${encodeURIComponent(title)},${lat},${lng}`;
};

const fetchPosts = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const response = await fetch(buildPostsUrl());
    if (!response.ok) {
      throw new Error('게시글 목록을 불러오지 못했습니다.');
    }
    const data = await response.json();
    posts.value = Array.isArray(data) ? data : [];
    const total = response.headers.get('X-Total-Count');
    totalCount.value = total ? Number(total) : 0;
  } catch (error) {
    console.error(error);
    errorMessage.value = '게시글 목록 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.';
  } finally {
    isLoading.value = false;
  }
};

// Simple toast
const toast = ref({ message: '', type: '', visible: false });
function showToast(message, type = 'info', ms = 3000) {
  toast.value = { message, type, visible: true };
  setTimeout(() => {
    toast.value.visible = false;
  }, ms);
}

const ratingFailureModal = ref({ visible: false, message: '' });

function showRatingFailure(message) {
  ratingFailureModal.value = { visible: true, message };
}

function closeRatingFailure() {
  ratingFailureModal.value = { visible: false, message: '' };
}

// [추가] 쿼리 파라미터에 location_id가 있을 때, 또는 선택된 명소의 상세 정보를 가져오는 함수
const fetchSelectedLocationInfo = async (id, target = 'filter') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/locations/${id}`);
    if (response.ok) {
      const data = await response.json();
      if (target === 'create') {
        selectedNewLocation.value = data;
      } else {
        selectedFilterLocation.value = data;
      }
    }
  } catch (error) {
    console.error('명소 정보를 불러오지 못했습니다:', error);
  }
};

// [변경] 필터 상태가 변경되면 URL을 업데이트하는 함수 (메모리 직접 수정 대신 URL 변경)
const updateFilterRoute = () => {
  const query = {};
  if (filterRegion.value) query.region = filterRegion.value;
  if (filterCategory.value) query.category = filterCategory.value;
  if (filterLocationId.value) query.location_id = filterLocationId.value;

  router.push({ path: route.path, query });
};

// [변경] 명소 선택 시, 메모리를 거치지 않고 바로 URL의 쿼리를 변경하도록 수정
const selectLocation = (location) => {
  if (locationModalScope.value === 'create') {
    newRegion.value = location.region;
    newLocationId.value = String(location.id);
    newThumbnailUrl.value = location.image_url || '';
    // fetch full details for the selected new location so rating info is available
    fetchSelectedLocationInfo(location.id, 'create');
  } else {
    filterRegion.value = location.region;
    filterLocationId.value = String(location.id);
    selectedFilterLocation.value = location;
    updateFilterRoute(); // URL 업데이트
  }
  closeLocationModal();
};

// [변경] 선택 해제 시에도 라우터를 거치도록 수정
const clearSelectedLocation = (scope) => {
  if (scope === 'create') {
    newLocationId.value = '';
    newThumbnailUrl.value = '';
    selectedNewLocation.value = null;
    return;
  }

  filterLocationId.value = '';
  selectedFilterLocation.value = null;
  updateFilterRoute(); // URL 업데이트
};

// [추가] 라우터 쿼리 스트링의 변화를 감지하여 상태를 동기화하고 API 호출
watch(
  () => route.query,
  async (newQuery) => {
    filterRegion.value = newQuery.region || '';
    filterCategory.value = newQuery.category || '';
    filterLocationId.value = newQuery.location_id || '';
    page.value = Number(newQuery.page || 1);

    // URL에 location_id는 있는데 상세 정보 오브젝트가 매핑되어 있지 않다면 백엔드에서 조회
    if (newQuery.location_id && (!selectedFilterLocation.value || String(selectedFilterLocation.value.id) !== String(newQuery.location_id))) {
      await fetchSelectedLocationInfo(newQuery.location_id);
    } else if (!newQuery.location_id) {
      selectedFilterLocation.value = null;
    }

    await fetchPosts();
  },
  { deep: true }
);

// [변경] 온마운트 시점에는 현재 주소창의 쿼리를 먼저 메모리에 대입한 뒤 데이터 페칭 수행
onMounted(async () => {
  filterRegion.value = route.query.region || '';
  filterCategory.value = route.query.category || '';
  filterLocationId.value = route.query.location_id || '';
  page.value = Number(route.query.page || 1);

  if (filterLocationId.value) {
    await fetchSelectedLocationInfo(filterLocationId.value);
  }
  await fetchPosts();
});

const totalPages = computed(() => Math.max(1, Math.ceil((totalCount.value || 0) / perPage.value)));

const goToPage = (p) => {
  if (p < 1) p = 1;
  if (p > totalPages.value) p = totalPages.value;
  page.value = p;
  // update route query
  const q = { ...route.query, page: String(page.value) };
  router.push({ path: route.path, query: q });
};

// 이하 기존 코드와 동일 (기타 비즈니스 로직 유지)
const filteredLocations = computed(() => {
  const keyword = locationSearchKeyword.value.trim().toLowerCase();
  if (!keyword) return loadedLocations.value;
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
  if (isLocationLoading.value) return;
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
    if (!response.ok) throw new Error('명소 목록을 불러오지 못했습니다.');
    const result = await response.json();
    loadedLocations.value = Array.isArray(result) ? result : [];
  } catch (error) {
    console.error(error);
    alert(error.message || '명소 목록 조회에 실패했습니다.');
  } finally {
    isLocationLoading.value = false;
  }
};

watch(newRegion, (nextRegion) => {
  if (!selectedNewLocation.value) return;
  if (selectedNewLocation.value.region !== nextRegion) {
    newLocationId.value = '';
    newThumbnailUrl.value = '';
    selectedNewLocation.value = null;
  }
});

watch(filterRegion, (nextRegion) => {
  if (!selectedFilterLocation.value) return;
  if (selectedFilterLocation.value.region !== nextRegion) {
    filterLocationId.value = '';
    selectedFilterLocation.value = null;
  }
});

const addPost = async () => {
  if (isSubmitting.value) return;
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
    region: newRegion.value
  };
  if (newLocationId.value.trim()) {
    payload.location_id = Number(newLocationId.value.trim());
    payload.thumbnail_url = newThumbnailUrl.value || null;
  }
  try {
    isSubmitting.value = true;
    // If this is a review ('후기') and user selected a location and provided a rating,
    // submit the rating first to the locations ratings API. If it fails, abort post creation.
    if (selectedCategory.value === '후기' && newLocationId.value && rating.value > 0) {
      const ok = await submitRatingForLocation(String(newLocationId.value), rating.value);
      if (!ok) {
        throw new Error('별점 등록 실패로 게시글 등록이 취소되었습니다.');
      }
      // include rating in post payload as well
      payload.rating = rating.value;
    }

    console.debug('Post payload:', payload);
    if (selectedCategory.value === '후기' && rating.value > 0 && payload.rating == null) {
      console.warn('Expected rating to be present in payload but it is missing', { selectedCategory: selectedCategory.value, rating: rating.value });
      showToast('별점이 포함되지 않았습니다 (디버그).', 'error');
    }
    const response = await fetch(`${API_BASE_URL}/api/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(String(errorBody?.detail || '게시글 등록에 실패했습니다.'));
    }
    await fetchPosts();
  } catch (error) {
    console.error(error);
    alert(error.message || '게시글 등록에 실패했습니다.');
    return;
  } finally {
    isSubmitting.value = false;
  }
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
  router.push(`/post/${id}`);
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
            <input
              v-model="newTitle"
              type="text"
              placeholder="명소를 드러내는 멋진 제목을 작성해 주세요"
            />
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
              <small>{{ selectedNewLocation.address || '주소 정보 없음' }}</small>
              <a
                class="location-link"
                :href="buildKakaoMapLink(selectedNewLocation)"
                target="_blank"
                rel="noopener noreferrer"
              >
                카카오지도로 이동
              </a>
            </div>

            <div v-if="selectedNewLocation && selectedCategory === '후기'" class="form-item rating-item">
              <label>별점 남기기</label>
              <div class="star-rating" role="radiogroup" aria-label="별점">
                <span
                  v-for="n in 5"
                  :key="n"
                  role="radio"
                  :aria-checked="n <= rating"
                  class="star"
                  :class="{ filled: n <= rating }"
                  @click="setRating(n)"
                >
                  ★
                </span>
              </div>
              <div v-if="ratingErrorMessage" class="rating-error">{{ ratingErrorMessage }}</div>
            </div>
            <!-- <p v-else class="sub-label">명소를 선택하지 않아도 게시글 등록이 가능합니다.</p> -->
          </div>

          <div class="form-item">
            <label>이야기 본문</label>
            <textarea v-model="newContent" placeholder="꿀팁이나 생각을 자유롭게 들려주세요."></textarea>
          </div>

          <div class="form-item">
            <label
              >비밀번호 설정
              <span class="sub-label">(글 수정/삭제 시 필요합니다)</span></label
            >
            <input
              v-model="newPassword"
              type="password"
              placeholder="비밀번호 4자리 입력"
              maxlength="8"
            />
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
        <select v-model="filterRegion" @change="updateFilterRoute">
          <option value="">전체 권역</option>
          <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
        </select>

        <select v-model="filterCategory" @change="updateFilterRoute">
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

        <button type="button" class="btn-refresh" @click="updateFilterRoute">검색</button>
      </div>

      <div v-if="selectedFilterLocation" class="selected-location-card filter-card">
        <strong>명소 조건: {{ selectedFilterLocation.name }}</strong>
        <span>{{ selectedFilterLocation.region }} · {{ selectedFilterLocation.category }}</span>
        <div class="selected-rating" v-if="selectedFilterLocation.rating_avg || selectedFilterLocation.rating_count">
          <span class="loc-stars-inline">
            <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(selectedFilterLocation.rating_avg || 0) }">★</span>
          </span>
          <small class="rating-text">{{ selectedFilterLocation.rating_avg ? Number(selectedFilterLocation.rating_avg).toFixed(1) : '-' }} ({{ selectedFilterLocation.rating_count || 0 }})</small>
        </div>
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

      <div v-if="selectedNewLocation" class="selected-location-card">
        <strong>{{ selectedNewLocation.name }}</strong>
        <span>{{ selectedNewLocation.region }} · {{ selectedNewLocation.category }}</span>
        <div class="selected-rating" v-if="selectedNewLocation.rating_avg || selectedNewLocation.rating_count">
          <span class="loc-stars-inline">
            <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(selectedNewLocation.rating_avg || 0) }">★</span>
          </span>
          <small class="rating-text">{{ selectedNewLocation.rating_avg ? Number(selectedNewLocation.rating_avg).toFixed(1) : '-' }} ({{ selectedNewLocation.rating_count || 0 }})</small>
        </div>
        <small>{{ selectedNewLocation.address || '주소 정보 없음' }}</small>
        <a
          class="location-link"
          :href="buildKakaoMapLink(selectedNewLocation)"
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
            <div v-if="post.category === '후기'" class="post-rating">
              <span class="post-stars">
                <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(post.rating || 0) }">★</span>
              </span>
              <span class="rating-text">{{ post.rating ? Number(post.rating).toFixed(1) : '-' }}</span>
            </div>
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.content.slice(0, 25) }}{{ post.content.length > 25 ? '...' : '' }}</p>
            
            <div class="card-footer">
              <span class="view-detail-text">클릭하여 상세 보기</span>
              <span class="comments-count" aria-hidden="true">💬 {{ post.comments_count ?? 0 }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="pagination-controls" style="display:flex; justify-content:center; gap:12px; margin-top:16px;">
        <button class="btn-secondary" :disabled="page<=1" @click="goToPage(page-1)">이전</button>
        <div class="page-indicator">페이지 {{ page }} / {{ totalPages }}</div>
        <button class="btn-secondary" :disabled="page>=totalPages" @click="goToPage(page+1)">다음</button>
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
            <div class="location-meta">
              <span>{{ location.region }} · {{ location.category }}</span>
              <div class="location-rating-inline">
                <span class="loc-stars">
                  <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(location.rating_avg || 0) }">★</span>
                </span>
                <small class="rating-text">{{ location.rating_avg ? Number(location.rating_avg).toFixed(1) : '-' }} ({{ location.rating_count || 0 }})</small>
              </div>
            </div>
            <small>{{ location.address || '주소 정보 없음' }}</small>
          </li>
        </ul>
      </div>
    </div>
    <div v-if="ratingFailureModal.visible" class="modal-overlay" @click.self="closeRatingFailure">
      <div class="modal">
        <h3>별점 등록 실패</h3>
        <p>{{ ratingFailureModal.message }}</p>
        <div class="modal-actions" style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
          <button class="btn-secondary" @click="closeRatingFailure">닫기</button>
        </div>
      </div>
    </div>
    <div v-if="toast.visible" :class="['toast', toast.type]">{{ toast.message }}</div>
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
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.02);
  margin-bottom: 48px;
  transition: box-shadow 0.2s;
}

.write-accordion:hover {
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.05);
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
  background-color: #fcfcfc;
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
  background-color: #eeeeee;
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

.rating-item .star-rating {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.rating-item .star {
  font-size: 1.6rem;
  color: #dcdcdc;
  cursor: pointer;
  user-select: none;
  transition: color 0.12s ease-in-out, transform 0.08s ease;
}
.rating-item .star:hover {
  transform: scale(1.08);
}
.rating-item .star.filled {
  color: #FFD54A; /* 밝은 노란색 */
  text-shadow: 0 1px 0 rgba(0,0,0,0.1);
}

.rating-error {
  margin-top: 6px;
  color: #b42318;
  font-size: 0.9rem;
}

.location-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.location-rating-inline { display:flex; align-items:center; gap:6px; }
.loc-stars { display:flex; gap:4px; }
.loc-star { color: #dcdcdc; font-size:1rem; }
.loc-star.filled { color: #FFD54A; }
.rating-text { color: var(--color-airbnb-gray); font-size:0.85rem; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.modal {
  width: min(92vw, 420px);
  background: white;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 30px rgba(0,0,0,0.2);
}
.modal h3 { margin: 0 0 8px; }
.modal p { margin: 0; color: var(--color-airbnb-gray); }

.loc-stars-inline { display:flex; gap:6px; margin-left:6px; align-items:center }
.selected-rating { display:flex; align-items:center; gap:8px; margin-top:6px; }

/* toast */
.toast {
  position: fixed;
  right: 18px;
  bottom: 18px;
  padding: 12px 16px;
  background: rgba(0,0,0,0.85);
  color: white;
  border-radius: 8px;
  z-index: 9999;
}
.toast.success { background: #16a34a; }
.toast.error { background: #b42318; }

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
  grid-template-columns: repeat(
    3,
    1fr
  ); /* 넓은 화면에서 한 줄에 무조건 3개씩 배치 */
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
  transition:
    transform 0.2s,
    box-shadow 0.2s;
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

.post-rating { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.post-stars { display:flex; gap:4px; }
.post-stars .loc-star { color:#dcdcdc; font-size:0.95rem; }
.post-stars .loc-star.filled { color:#FFD54A; }
.post-card .rating-text { color: var(--color-airbnb-gray); font-size:0.85rem; }

.comments-count {
  margin-left: 12px;
  color: var(--color-airbnb-gray);
  font-weight: 600;
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
