<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const post = ref(null);
const isLoading = ref(false);
const errorMessage = ref('');
const isEditMode = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const isDeleteModalOpen = ref(false);
const isLocationModalOpen = ref(false);
const isLocationLoading = ref(false);

const categoryOptions = ['잡담', '후기', '질문', '구인'];
const regionOptions = ['서울', '부산', '광주_전라권', '구미_경북권', '대전_충청권'];
const locationCategoryOptions = ['관광지', '문화시설', '축제공연행사', '여행코스', '레포츠', '숙박', '쇼핑', '음식점'];

const editTitle = ref('');
const editContent = ref('');
const editCategory = ref('잡담');
const editLocationId = ref('');
const editThumbnailUrl = ref('');
const selectedEditLocation = ref(null);
const hasLocationChanged = ref(false);

const locationSearchRegion = ref('');
const locationSearchCategory = ref('');
const locationSearchKeyword = ref('');
const loadedLocations = ref([]);

const editPassword = ref('');
const deletePassword = ref('');

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://glassless-be.onrender.com';

const buildListRouteTarget = () => {
  const locationIdText = String(route.query.location_id ?? '').trim();
  if (/^\d+$/.test(locationIdText) && Number(locationIdText) > 0) {
    return { path: '/posts', query: { location_id: locationIdText } };
  }
  return { path: '/posts' };
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR');
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

const fetchPostDetail = async () => {
  const postId = Number(route.params.id);
  if (!Number.isInteger(postId) || postId <= 0) {
    errorMessage.value = '유효하지 않은 게시글 ID입니다.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`);
    if (response.status === 404) {
      throw new Error('존재하지 않는 게시글입니다.');
    }
    if (!response.ok) {
      throw new Error('게시글 상세 정보를 불러오지 못했습니다.');
    }

    post.value = await response.json();
    await syncEditForm();
  } catch (error) {
    console.error(error);
    errorMessage.value = error.message || '상세 조회 중 오류가 발생했습니다.';
  } finally {
    isLoading.value = false;
  }
};

const syncEditForm = async () => {
  if (!post.value) return;
  editTitle.value = post.value.title || '';
  editContent.value = post.value.content || '';
  editCategory.value = post.value.category || '잡담';
  editLocationId.value = post.value.location_id != null ? String(post.value.location_id) : '';
  editThumbnailUrl.value = post.value.thumbnail_url || '';
  selectedEditLocation.value = post.value.location_id ? await fetchLocationById(post.value.location_id) : null;
  hasLocationChanged.value = false;
  editPassword.value = '';
};

const startEdit = async () => {
  await syncEditForm();
  isEditMode.value = true;
};

const cancelEdit = async () => {
  isEditMode.value = false;
  await syncEditForm();
};

const resetModalLocations = () => {
  loadedLocations.value = [];
  locationSearchKeyword.value = '';
};

const openLocationModal = () => {
  locationSearchRegion.value = post.value?.region || '';
  locationSearchCategory.value = '';
  resetModalLocations();
  isLocationModalOpen.value = true;
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

const selectLocationForEdit = (location) => {
  editLocationId.value = String(location.id);
  editThumbnailUrl.value = location.image_url || '';
  selectedEditLocation.value = location;
  hasLocationChanged.value = true;
  closeLocationModal();
};

const clearSelectedLocationForEdit = () => {
  editLocationId.value = '';
  editThumbnailUrl.value = '';
  selectedEditLocation.value = null;
  hasLocationChanged.value = true;
};

const openDeleteModal = () => {
  deletePassword.value = '';
  isDeleteModalOpen.value = true;
};

const closeDeleteModal = () => {
  if (isDeleting.value) return;
  isDeleteModalOpen.value = false;
  deletePassword.value = '';
};

const saveEdit = async () => {
  if (isSaving.value || !post.value) return;

  if (!editTitle.value.trim() || !editContent.value.trim()) {
    alert('제목과 본문은 필수입니다.');
    return;
  }
  if (!editPassword.value.trim()) {
    alert('수정을 위해 비밀번호를 입력해주세요.');
    return;
  }

  const payload = {
    password: editPassword.value,
    title: editTitle.value.trim(),
    content: editContent.value.trim(),
    category: editCategory.value,
  };

  if (hasLocationChanged.value) {
    payload.location_id = editLocationId.value.trim() ? Number(editLocationId.value) : null;
    payload.thumbnail_url = editThumbnailUrl.value || null;
  }

  try {
    isSaving.value = true;
    const response = await fetch(`${API_BASE_URL}/api/posts/${post.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody?.detail || '수정에 실패했습니다.');
    }

    post.value = await response.json();
    isEditMode.value = false;
    await syncEditForm();
    alert('게시글이 수정되었습니다.');
  } catch (error) {
    console.error(error);
    alert(error.message || '수정에 실패했습니다.');
  } finally {
    isSaving.value = false;
  }
};

const deletePost = async () => {
  if (isDeleting.value || !post.value) return;
  if (!deletePassword.value.trim()) {
    alert('삭제를 위해 비밀번호를 입력해주세요.');
    return;
  }

  try {
    isDeleting.value = true;
    const response = await fetch(`${API_BASE_URL}/api/posts/${post.value.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: deletePassword.value }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody?.detail || '삭제에 실패했습니다.');
    }

    alert('게시글이 삭제되었습니다.');
    isDeleteModalOpen.value = false;
    router.push(buildListRouteTarget());
  } catch (error) {
    console.error(error);
    alert(error.message || '삭제에 실패했습니다.');
  } finally {
    isDeleting.value = false;
  }
};

onMounted(async () => {
  await fetchPostDetail();
});
</script>

<template>
  <div class="detail-container">
    <button class="btn-back" @click="router.push(buildListRouteTarget())">← 전체 목록으로 돌아가기</button>

    <div v-if="isLoading" class="state-message">게시글을 불러오는 중입니다...</div>
    <div v-else-if="errorMessage" class="state-message error">{{ errorMessage }}</div>

    <div v-else-if="post" class="detail-card">
      <div class="detail-meta-row top-actions">
        <div class="left-meta">
          <select v-if="isEditMode" v-model="editCategory" class="detail-badge-select">
            <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <span v-else class="detail-badge">{{ post.category }}</span>
          <span class="detail-sub location-top">{{ post.region || '미지정' }}</span>
        </div>
        <div class="right-top-meta">
          <div class="action-buttons" :class="{ 'mobile-corner': !isEditMode }">
            <div v-if="!isEditMode" class="read-actions">
              <button  class="btn-secondary btn-edit-compact" @click="startEdit">수정</button>
              <button class="btn-danger" @click="openDeleteModal">삭제</button>
            </div>
            <template v-else>
              <button class="btn-secondary" @click="cancelEdit">취소</button>
              <button class="btn-primary" :disabled="isSaving" @click="saveEdit">
                {{ isSaving ? '저장 중...' : '수정 확정' }}
              </button>
            </template>
          </div>
        </div>
      </div>
      <h1 v-if="!isEditMode" class="detail-title">{{ post.title }}</h1>
      <div v-if="!isEditMode && post && post.category === '후기'" class="post-detail-rating">
        <span class="post-stars">
          <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(post.rating || 0) }">★</span>
        </span>
        <small class="rating-text">{{ post.rating ? Number(post.rating).toFixed(1) : '-' }}</small>
      </div>
      <input v-else v-model="editTitle" class="detail-title-input" type="text" maxlength="200" />

      <div class="detail-info">
        <span>작성 시각: {{ formatDateTime(post.created_at) }}</span>
        <span>수정 시각: {{ formatDateTime(post.updated_at) }}</span>
      </div>

      

      <div v-if="post.thumbnail_url" class="detail-thumbnail-wrap">
        <img :src="post.thumbnail_url" alt="게시글 썸네일" class="detail-thumbnail" />
      </div>

      <p v-if="!isEditMode" class="detail-desc">{{ post.content }}</p>
      <textarea v-else v-model="editContent" class="detail-desc-input" rows="8" maxlength="5000"></textarea>


      <div v-if="!isEditMode && (selectedEditLocation || post.location_id)" class="selected-location-card detail-location-card">
        <template v-if="selectedEditLocation">
          <strong>{{ selectedEditLocation.name }}</strong>
          <span>{{ selectedEditLocation.region }} · {{ selectedEditLocation.category }}</span>
          <div class="selected-rating" v-if="selectedEditLocation.rating_avg || selectedEditLocation.rating_count">
            <span class="loc-stars-inline">
              <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(selectedEditLocation.rating_avg || 0) }">★</span>
            </span>
            <small class="rating-text">{{ selectedEditLocation.rating_avg ? Number(selectedEditLocation.rating_avg).toFixed(1) : '-' }} ({{ selectedEditLocation.rating_count || 0 }})</small>
          </div>
          <small>{{ selectedEditLocation.address || '주소 정보 없음' }}</small>
          <div class="location-link-row">
            <router-link class="location-link-btn" :to="buildLocationPostsRoute(selectedEditLocation)">
              게시글 모아보기
            </router-link>
            <a
              class="location-link"
              :href="buildKakaoMapLink(selectedEditLocation)"
              target="_blank"
              rel="noopener noreferrer"
            >
              카카오지도로 이동
            </a>
          </div>
        </template>
        <template v-else>
          <span>명소 정보를 불러오지 못했습니다.</span>
        </template>
      </div>

      <div v-if="isEditMode" class="edit-location-block">
        <label>연결 명소</label>
        <div class="location-picker-row">
          <button type="button" class="btn-secondary" @click="openLocationModal">권역/카테고리로 찾기</button>
          <button v-if="selectedEditLocation || editLocationId" type="button" class="btn-clear-selection" @click="clearSelectedLocationForEdit">
            연결 해제
          </button>
        </div>

        <div v-if="selectedEditLocation" class="selected-location-card">
          <strong>{{ selectedEditLocation.name }}</strong>
          <span>{{ selectedEditLocation.region }} · {{ selectedEditLocation.category }}</span>
          <small>{{ selectedEditLocation.address || '주소 정보 없음' }}</small>
        </div>

        <div v-else-if="editLocationId" class="selected-location-card">
          <strong>기존 연결된 명소</strong>
          <span>명소 정보를 불러오지 못했습니다.</span>
        </div>
      </div>

      <div v-if="isEditMode" class="edit-password-row">
        <label>수정 비밀번호</label>
        <input v-model="editPassword" type="password" maxlength="100" placeholder="작성 시 비밀번호 입력" />
      </div>
    </div>

    <div v-if="isDeleteModalOpen" class="delete-modal-overlay" @click.self="closeDeleteModal">
      <div class="delete-modal">
        <h3>게시글 삭제</h3>
        <p>삭제하려면 비밀번호를 입력한 뒤 확인을 눌러주세요.</p>
        <input
          v-model="deletePassword"
          type="password"
          maxlength="100"
          placeholder="작성 시 비밀번호 입력"
          @keyup.enter="deletePost"
        />
        <div class="modal-actions">
          <button class="btn-secondary" :disabled="isDeleting" @click="closeDeleteModal">취소</button>
          <button class="btn-danger" :disabled="isDeleting" @click="deletePost">
            {{ isDeleting ? '삭제 중...' : '확인' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="isLocationModalOpen" class="location-modal-overlay" @click.self="closeLocationModal">
      <div class="location-modal">
        <div class="location-modal-header">
          <h3>명소 검색</h3>
          <button type="button" class="btn-secondary" :disabled="isLocationLoading" @click="closeLocationModal">닫기</button>
        </div>

        <p class="detail-sub">권역과 카테고리를 선택해 목록을 불러오고, 키워드로 명소를 찾으세요.</p>

        <div class="location-modal-controls">
          <select v-model="locationSearchRegion">
            <option value="" disabled>권역 선택</option>
            <option v-for="region in regionOptions" :key="region" :value="region">{{ region }}</option>
          </select>

          <select v-model="locationSearchCategory">
            <option value="" disabled>카테고리 선택</option>
            <option v-for="cat in locationCategoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>

          <button type="button" class="btn-primary" :disabled="isLocationLoading" @click="loadLocationsByRegionAndCategory">
            {{ isLocationLoading ? '불러오는 중...' : '목록 불러오기' }}
          </button>
        </div>

        <input
          v-model="locationSearchKeyword"
          class="location-modal-search-input"
          type="text"
          placeholder="불러온 목록에서 명소명/주소 검색"
        />

        <p v-if="isLocationLoading" class="detail-sub">명소 목록을 불러오는 중입니다...</p>
        <p v-else-if="loadedLocations.length === 0" class="detail-sub">권역/카테고리 선택 후 목록을 불러와 주세요.</p>
        <p v-else-if="filteredLocations.length === 0" class="detail-sub">검색 결과가 없습니다.</p>

        <ul v-else class="location-results">
          <li
            v-for="location in filteredLocations"
            :key="location.id"
            class="location-result-item"
            @click="selectLocationForEdit(location)"
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
.detail-container { max-width: 800px; margin: 40px auto; padding: 0 24px; }
.btn-back { background: none; border: none; color: var(--color-airbnb-red); font-size: 1rem; font-weight: 600; cursor: pointer; margin-bottom: 20px; }
.state-message { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); padding: 24px; color: var(--color-airbnb-gray); }
.state-message.error { color: #b42318; }
.detail-card { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); padding: 40px; position: relative; }
.detail-meta-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.top-actions { align-items: flex-start; }
.left-meta { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.right-top-meta { display: flex; flex-direction: row; align-items: flex-end; gap: 8px; }
.location-top { text-align: right; }
.read-actions { display: flex; gap: 8px; }
.detail-badge { display: inline-block; background-color: #FFF0F2; padding: 6px 14px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; color: var(--color-airbnb-red); }
.detail-badge-select {
  background-color: #FFF0F2;
  color: var(--color-airbnb-red);
  border: 1px solid #f0b8c5;
  border-radius: 20px;
  padding: 6px 10px;
  font-size: 0.9rem;
  font-weight: 700;
}
.detail-sub { color: var(--color-airbnb-gray); font-size: 0.9rem; }
.detail-title { font-size: 2rem; margin-bottom: 24px; }
.detail-title-input {
  width: 100%;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 24px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 12px;
}
.detail-info { display: flex; flex-wrap: wrap; gap: 10px 16px; margin-bottom: 20px; font-size: 0.88rem; color: var(--color-airbnb-gray); }
.detail-thumbnail-wrap {
  margin-bottom: 20px;
}

.detail-thumbnail {
  width: 100%;
  max-height: 340px;
  object-fit: cover;
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.detail-desc { font-size: 1.1rem; white-space: pre-wrap; line-height: 1.8; }
.detail-desc-input {
  width: 100%;
  font-size: 1.1rem;
  line-height: 1.8;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px 14px;
  resize: vertical;
}

.edit-location-block {
  margin-top: 16px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-location-block label {
  font-size: 0.9rem;
  font-weight: 700;
}

.location-picker-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
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

.loc-stars-inline { display:flex; gap:6px; margin-left:6px; align-items:center }
.selected-rating { display:flex; align-items:center; gap:8px; margin-top:6px; }
.loc-star { color: #dcdcdc; font-size:1rem; }
.loc-star.filled { color: #FFD54A; }
.rating-text { color: var(--color-airbnb-gray); font-size:0.85rem; }

.post-detail-rating { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
.post-detail-rating .post-stars { display:flex; gap:6px; }
.post-detail-rating .loc-star { color:#dcdcdc; }
.post-detail-rating .loc-star.filled { color:#FFD54A; }

.detail-location-card {
  margin-top: 18px;
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

.location-link {
  color: var(--color-airbnb-red);
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 4px 10px;
}

.location-link:hover {
  text-decoration: underline;
}

.inline-edit-id {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.inline-edit-id input {
  width: 110px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 6px 8px;
}

.edit-password-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.edit-password-row label {
  font-size: 0.9rem;
  font-weight: 700;
}

.edit-password-row input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
}

.action-buttons { display: flex; gap: 8px; flex-wrap: nowrap; align-items: center; }
.btn-primary,
.btn-secondary,
.btn-danger {
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  background-color: var(--color-airbnb-red);
  color: white;
  border: 2px solid #8f0d2f;
}

.btn-secondary {
  background-color: white;
  color: var(--color-airbnb-dark);
  border: 2px solid #444;
}

.btn-danger {
  background-color: #fff5f5;
  color: #b42318;
  border: 2px solid #b42318;
}

.btn-primary:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-bottom-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.delete-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.delete-modal {
  width: min(92vw, 420px);
  background: white;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.delete-modal h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
}

.delete-modal p {
  margin: 0 0 12px;
  color: var(--color-airbnb-gray);
  font-size: 0.9rem;
}

.delete-modal input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 11px 12px;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.location-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
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
}

.location-modal-controls {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
}

.location-modal-controls select,
.location-modal-search-input {
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

.location-result-item span,
.location-result-item small {
  color: var(--color-airbnb-gray);
}

@media (max-width: 640px) {
  .modal-actions,
  .edit-password-row,
  .location-picker-row {
    flex-direction: column;
    width: 100%;
  }

  .location-modal-controls {
    grid-template-columns: 1fr;
  }

  .modal-actions .btn-primary,
  .modal-actions .btn-secondary,
  .modal-actions .btn-danger {
    width: 100%;
  }

  .top-actions { position: relative; flex-wrap: nowrap; }

  .right-top-meta {
    align-items: flex-end;
    width: auto;
    flex-shrink: 0;
  }

  .left-meta {
    min-width: 0;
  }

  .action-buttons.mobile-corner {
    position: absolute;
    top: 0;
    right: 0;
  }

  .btn-edit-compact,
  .read-actions .btn-danger,
  .action-buttons .btn-primary,
  .action-buttons .btn-secondary {
    border-width: 1px;
    padding: 6px 9px;
    font-size: 0.78rem;
    line-height: 1.2;
  }
  
  .location-link {
    align-self: flex-end;
    margin-left:auto;
  }
}
</style>
