<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const previewPosts = ref([]);

// 모달 및 상세 게시글 상태 관리
const isModalOpen = ref(false);
const detailedPost = ref(null);
const isDetailLoading = ref(false);

// .env 파일에 정의된 전역 환경 변수 가져오기 (https://glassless-be.onrender.com)
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  try {
    const response = await fetch(`${BASE_URL}/api/posts`);

    if (response.status === 422) {
      previewPosts.value = [];
      return;
    }

    if (!response.ok) {
      throw new Error("네트워크 응답 불안정");
    }

    const allPosts = await response.json();

    if (Array.isArray(allPosts)) {
      previewPosts.value = allPosts.slice(0, 4);
    } else {
      previewPosts.value = [];
    }
  } catch (error) {
    console.error("데이터 로드 실패 (422 처리 포함):", error);
    previewPosts.value = [];
  }
});

// 특정 게시물 클릭 시 상세 정보 모달 오픈 및 GET 요청
const openDetailModal = async (postId) => {
  isModalOpen.value = true;
  isDetailLoading.value = true;
  detailedPost.value = null;

  try {
    const response = await fetch(`${BASE_URL}/api/posts/${postId}`);

    if (response.status === 422) {
      console.warn("상세페이지 로드 실패: 422 Validation Error");
      closeModal();
      return;
    }

    if (!response.ok) {
      throw new Error("상세 정보 로드 실패");
    }

    const data = await response.json();
    detailedPost.value = data;
  } catch (error) {
    console.error("상세페이지 API 에러:", error);
    closeModal();
  } finally {
    isDetailLoading.value = false;
  }
};

// 모달 닫기
const closeModal = () => {
  isModalOpen.value = false;
  detailedPost.value = null;
};

const goToPostList = () => {
  router.push("/posts");
};

// 날짜 포맷팅 함수 (yyyy-mm-dd hh:mm)
const formatDate = (dateStr) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
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
          @click="openDetailModal(post.id)"
        >
          <div class="card-image-placeholder">
            <span class="badge">{{ post.region || "지역 정보 없음" }}</span>
          </div>
          <div class="card-info">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.content }}</p>
          </div>
        </div>
      </div>
    </section>

    <div v-if="isModalOpen" class="modal-backdrop" @click="closeModal">
      <div class="modal-window" @click.stop>
        <div v-if="isDetailLoading" class="modal-loading">
          <span class="spinner"></span>
          <p>이야기를 불러오는 중입니다...</p>
        </div>

        <div v-else-if="detailedPost" class="modal-content-wrapper">
          <div class="modal-header">
            <div class="modal-meta">
              <span class="category-tag">{{ detailedPost.category }}</span>
              <span class="location-text">📍 {{ detailedPost.region }}</span>
            </div>
            <button class="btn-close-modal" @click="closeModal">✕</button>
          </div>

          <div class="modal-body">
            <h2 class="modal-post-title">{{ detailedPost.title }}</h2>

            <div class="modal-post-date" v-if="detailedPost.created_at">
              <span class="date-label">등록일</span>
              <span class="date-value">{{
                formatDate(detailedPost.created_at)
              }}</span>
              <span
                v-if="detailedPost.created_at !== detailedPost.updated_at"
                class="updated-badge"
              >
                (수정됨: {{ formatDate(detailedPost.updated_at) }})
              </span>
            </div>

            <div class="modal-img-placeholder">
              <span>🖼️ 로컬 추천 명소</span>
            </div>

            <p class="modal-post-content">{{ detailedPost.content }}</p>
          </div>

          <div class="modal-footer">
            <div class="footer-left-placeholder"></div>
            <button class="btn-confirm-action" @click="closeModal">확인</button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.home-page {
  padding-bottom: 80px;
}

.hero-map-section {
  width: 100%;
  height: 320px;
  background-color: #e3ece9;
  position: relative;
  overflow: hidden;
}

.map-preview {
  width: 100%;
  height: 100%;
  background-image:
    radial-gradient(circle, #cfddd8 10%, transparent 10.5%),
    radial-gradient(circle, #cfddd8 10%, transparent 10.5%);
  background-size: 20px 20px;
  background-position:
    0 0,
    10px 10px;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition:
    transform 0.2s,
    background-color 0.2s;
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
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

@media (max-width: 1100px) {
  .preview-card {
    flex: 0 0 280px;
  }
}

.preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}

.card-image-placeholder {
  height: 150px;
  background-color: #ebebeb;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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

/* ==========================================
   ✨ 모달창 (Modal) 디자인
   ========================================== */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
  padding: 20px;
  box-sizing: border-box;
}

.modal-window {
  width: 100%;
  max-width: 680px;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: modalScaleUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalScaleUp {
  from {
    transform: scale(0.95) translateY(10px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.modal-loading {
  padding: 60px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--color-airbnb-gray);
  font-size: 0.95rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid var(--color-airbnb-red);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.modal-content-wrapper {
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px 28px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
}

.modal-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.category-tag {
  background-color: var(--color-airbnb-dark);
  color: white;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 6px;
}

.location-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-airbnb-gray);
}

.btn-close-modal {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--color-airbnb-gray);
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}

.btn-close-modal:hover {
  color: var(--color-airbnb-dark);
}

/* 모달 바디 */
.modal-body {
  padding: 28px;
  max-height: 440px;
  overflow-y: auto;
}

.modal-post-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--color-airbnb-dark);
  margin-bottom: 10px; /* 아래 등록일과 간격 최적화 */
  line-height: 1.3;
}

/* 📅 신규 등록일 스타일링 */
.modal-post-date {
  font-size: 0.85rem;
  color: var(--color-airbnb-gray);
  margin-bottom: 24px; /* 본문 이미지와의 간격 확보 */
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-label {
  font-weight: 700;
  color: #a8a8a8;
  font-size: 0.78rem;
  text-transform: uppercase;
  border: 1px solid #ebebeb;
  padding: 2px 6px;
  border-radius: 4px;
}

.date-value {
  font-weight: 500;
  color: #666666;
}

.updated-badge {
  font-size: 0.8rem;
  color: var(--color-airbnb-red);
  font-weight: 500;
}

.modal-img-placeholder {
  width: 100%;
  height: 240px;
  background-color: #f3f3f3;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--color-airbnb-gray);
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 24px;
  border: 1px solid var(--color-border);
}

.modal-post-content {
  font-size: 1.02rem;
  color: #333333;
  line-height: 1.7;
  white-space: pre-wrap;
}

/* 모달 푸터 */
.modal-footer {
  padding: 18px 28px;
  border-top: 1px solid var(--color-border);
  background-color: #fafafa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-confirm-action {
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-confirm-action:hover {
  filter: brightness(0.9);
}

@media (max-width: 600px) {
  .modal-window {
    border-radius: 12px;
  }
  .modal-post-title {
    font-size: 1.3rem;
  }
  .modal-img-placeholder {
    height: 180px;
  }
}
</style>
