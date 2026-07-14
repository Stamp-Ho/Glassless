<!-- src/views/HomeView.vue -->
<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const previewPosts = ref([]);

onMounted(() => {
  const savedPosts = localStorage.getItem('localhub_posts');
  if (savedPosts) {
    // 깔끔하게 딱 4개만 필터링하여 노출
    previewPosts.value = JSON.parse(savedPosts).slice(0, 4);
  } else {
    const dummy = [
      { id: 1, title: '부산 광안리 드론쇼 명당 공유', location: '부산 수영구', desc: '여기 카페 2층 테라스가 숨겨진 뷰 맛집입니다.' },
      { id: 2, title: '경주 황리단길 주차 꿀팁', location: '경북 경주시', desc: '주말에는 공영주차장 말고 이 골목을 이용해보세요.' },
      { id: 3, title: '제주 애월읍 노을 숨은 포인트', location: '제주 애월읍', desc: '해안도로 끝자락 붉은 등대 옆이 제일 예쁩니다.' },
      { id: 4, title: '서울 성수동 조용한 북카페', location: '서울 성동구', desc: '골목 깊은 곳에 있어 작업하기 아주 좋습니다.' }
    ];
    previewPosts.value = dummy;
    localStorage.setItem('localhub_posts', JSON.stringify(dummy));
  }
});

const goToPostList = () => {
  router.push('/posts');
};
</script>

<template>
  <main class="home-page">
    <!-- 1. 상단 미니 맵 영역 (레이아웃 전면 축소 및 컴팩트화) -->
    <section class="hero-map-section">
      <div class="map-preview">
        <!-- 왼쪽 상단에 고정된 작고 모던한 블랙 버튼 -->
        <button class="btn-map-sm" @click="router.push('/map')">
          📍 지도에서 찾기
        </button>
      </div>
    </section>

    <!-- 2. 하단 게시물 가로 스크롤 카드 프리뷰 (마지막 액션 카드 제거) -->
    <section class="preview-section">
      <div class="section-header">
        <h2 class="section-title">최신 추천 지역 정보</h2>
        <span class="view-all" @click="goToPostList">모두 보기 &rarr;</span>
      </div>

      <div class="slider-container no-scrollbar">
        <!-- 순수하게 Vue 아이템 카드 4개만 깔끔하게 노출 -->
        <div 
          v-for="post in previewPosts" 
          :key="post.id" 
          class="preview-card"
          @click="goToPostList"
        >
          <div class="card-image-placeholder">
            <span class="badge">{{ post.location }}</span>
          </div>
          <div class="card-info">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.desc }}</p>
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

/* 상단 지도 영역 스타일 구조조정 */
.hero-map-section {
  width: 100%;
  height: 320px; /* 불필요한 시각적 피로감을 줄이기 위해 높이 축소 */
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

/* 지도의 왼쪽 상단(Top-Left)에 배치되는 미니멀한 검정 버튼 */
.btn-map-sm {
  position: absolute;
  top: 24px;
  left: 24px;
  background-color: var(--color-airbnb-dark); /* 세련된 검정색 */
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

/* 하단 카드 프리뷰 래퍼 */
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
  flex: 0 0 calc(25% - 15px); /* 화면이 넓을 때 한눈에 4개가 안정적으로 들어오도록 조절 */
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
    flex: 0 0 280px; /* 화면이 작아지면 자연스럽게 가로 스크롤 활성화 */
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