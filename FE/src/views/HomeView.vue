<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const previewPosts = ref([]);

// .env 파일에 정의된 전역 환경 변수 가져오기 (https://glassless-be.onrender.com)
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  try {
    // 1. 전체 게시물 목록 엔드포인트로 단일 요청 전송
    const response = await fetch(`${BASE_URL}/api/posts`);

    // 2. 422 Validation Error 발생 시 아무것도 출력 안 하도록 빈 배열 처리 후 종료
    if (response.status === 422) {
      previewPosts.value = [];
      return;
    }

    if (!response.ok) {
      throw new Error('네트워크 응답 불안정');
    }

    const allPosts = await response.json();

    // 3. 받아온 배열 데이터가 유효하다면 상위 4개만 슬라이스(slice)하여 바인딩
    if (Array.isArray(allPosts)) {
      previewPosts.value = allPosts.slice(0, 4);
    } else {
      previewPosts.value = [];
    }

  } catch (error) {
    // 통신 실패 혹은 예외 상황 시 화면에 에러를 노출하지 않고 조용히 빈 화면 처리
    console.error("데이터 로드 실패 (422 처리 포함):", error);
    previewPosts.value = [];
  }
});

const goToPostList = () => {
  router.push('/posts');
};
</script>

<template>
  <main class="home-page">
    <section class="hero-map-section">
      <div class="map-preview">
        <button class="btn-map-sm" @click="router.push('/map')">
          📍 지도에서 찾기
        </button>
      </div>
    </section>

    <section v-if="previewPosts.length > 0" class="preview-section">
      <div class="section-header">
        <h2 class="section-title">최신 추천 지역 정보</h2>
        <span class="view-all" @click="goToPostList">모두 보기 &rarr;</span>
      </div>

      <div class="slider-container no-scrollbar">
        <div 
          v-for="post in previewPosts" 
          :key="post.id" 
          class="preview-card"
          @click="goToPostList"
        >
          <div class="card-image-placeholder">
            <span class="badge">{{ post.region || '지역 정보 없음' }}</span>
          </div>
          <div class="card-info">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.content }}</p>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  padding-bottom: 80px;
}

.hero-map-section {
  width: 100%;
  height: 320px;
  background-color: #E3ECE9;
  position: relative;
  overflow: hidden;
}

.map-preview {
  width: 100%;
  height: 100%;
  background-image: radial-gradient(circle, #CFDDD8 10%, transparent 10.5%), radial-gradient(circle, #CFDDD8 10%, transparent 10.5%);
  background-size: 20px 20px;
  background-position: 0 0, 10px 10px;
  position: relative;
}

.btn-map-sm {
  position: absolute;
  top: 24px;
  left: 24px;
  background-color: var(--color-airbnb-dark);
  color: white;
  border: none;
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s, background-color 0.2s;
}

.btn-map-sm:hover {
  background-color: #000000;
  transform: translateY(-1px);
}

.preview-section {
  max-width: 1200px;
  margin: 40px auto 0;
  padding: 0 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
}

.section-title {
  font-size: 1.35rem;
  font-weight: 700;
}

.view-all {
  color: var(--color-airbnb-red);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.slider-container {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding-bottom: 12px;
  scroll-behavior: smooth;
  snap-type: x mandatory;
}

.preview-card {
  flex: 0 0 calc(25% - 15px);
  min-width: 260px;
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  cursor: pointer;
  snap-align: start;
  transition: transform 0.2s, box-shadow 0.2s;
}

@media (max-width: 1100px) {
  .preview-card {
    flex: 0 0 280px;
  }
}

.preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.06);
}

.card-image-placeholder {
  height: 150px;
  background-color: #EBEBEB;
  position: relative;
  display: flex;
  align-items: flex-end;
  padding: 12px;
}

.badge {
  background-color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.card-info {
  padding: 16px;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: 0.85rem;
  color: var(--color-airbnb-gray);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>