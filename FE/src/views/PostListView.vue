<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const posts = ref([]);
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref('');

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const filterRegion = ref('');
const filterCategory = ref('');
const filterLocationId = ref('');

const regionOptions = ['서울', '부산', '광주_전라권', '구미_경북권', '대전_충청권'];
const categoryOptions = ['잡담', '후기', '질문', '구인'];

// 입력 폼 상태 관리
const isFormOpen = ref(false);
const selectedCategory = ref('잡담');
const newTitle = ref('');
const newRegion = ref('');
const newContent = ref('');
const newLocationId = ref('');
const newPassword = ref('');

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

onMounted(async () => {
  await fetchPosts();
});

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
          <h2>명소에 대한 생각이나 이야기를 공유해주세요!</h2>
          <p>이곳을 클릭하여 동네의 숨겨진 이야기와 유용한 꿀팁을 들려주세요.</p>
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
            <label>연결할 명소 ID <span class="sub-label">(선택값)</span></label>
            <input v-model="newLocationId" type="number" min="1" placeholder="예: 1" />
          </div>

          <div class="form-item">
            <label>이야기 본문</label>
            <textarea v-model="newContent" placeholder="이 명소와 관련된 꿀팁이나 생각을 자유롭게 들려주세요."></textarea>
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

        <input
          v-model="filterLocationId"
          type="number"
          min="1"
          placeholder="명소 ID"
          @keyup.enter="fetchPosts"
        />

        <button type="button" class="btn-refresh" @click="fetchPosts">검색</button>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="isLoading" class="state-text">게시글을 불러오는 중입니다...</p>
      <p v-else-if="posts.length === 0" class="state-text">조건에 맞는 게시글이 없습니다.</p>
      
      <div class="grid-container">
        <div v-for="post in posts" :key="post.id" class="post-card" @click="goToDetail(post.id)">
          <div class="card-image-field">
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
}
@media (max-width: 600px) {
  .grid-container {
    grid-template-columns: 1fr;
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
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #9d9d9d;
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
</style>