<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const previewPosts = ref([]);

// .env 파일에 정의된 전역 환경 변수 가져오기
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

// 게시물 상세 페이지로 이동
const goToPostDetail = (postId) => {
  router.push(`/posts/${postId}`);
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
          @click="goToPostDetail(post.id)"
        >
          <div class="card-image-container">
            <img
              v-if="post.thumbnail_url"
              :src="post.thumbnail_url"
              :alt="post.title"
              class="card-image"
            />
            <div v-else class="card-image-placeholder-bg"></div>

            <span class="badge">{{ post.region || "지역 정보 없음" }}</span>
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

/* 🛠️ 가로 스크롤을 없애고 자리가 부족하면 다음 줄로 떨어지도록 flex-wrap 처리 */
.slider-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding-bottom: 12px;
  width: 100%;
}

/* 🛠️ 평소에는 최대 280px 크기를 유지하되, 게시물이 적어도 뚱뚱해지지 않도록 설정 */
.preview-card {
  /* 🔥 핵심 수정:
    - 기본 너비는 화면이 좁을 때 유연하게 대응하도록 calc 계산식을 유지합니다.
    - 하지만 'max-width: 280px;'을 걸어두어 게시물이 1~2개뿐이어도 절대 280px보다 커지지 않고 예쁜 비율을 유지합니다.
    - 'flex-grow: 0;'으로 설정해 남는 공간이 있어도 카드가 억지로 늘어나지 않습니다.
  */
  width: calc((100% - 60px) / 4);
  max-width: 280px; /* 👈 카드의 최대 크기를 딱 예쁜 280px로 제한! */

  flex-shrink: 1;
  flex-grow: 0; /* 👈 빈 공간이 생겨도 카드가 멋대로 커지지 않음! */

  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}
/* 이미지 컨테이너 (비율 유지용) */
.card-image-container {
  position: relative;
  width: 100%;
  height: 180px; /* 원하시는 높이로 조절하세요 */
  overflow: hidden;
  border-radius: 8px 8px 0 0; /* 카드 윗부분만 둥글게 */
  background-color: #f3f3f3; /* 이미지 로딩 전/실패 시 배경색 */
}

/* 실제 이미지 스타일 */
.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 이미지가 찌그러지지 않고 꽉 차게 비율 조절 */
  display: block;
}

/* 이미지가 없을 때 보여줄 배경 */
.card-image-placeholder-bg {
  width: 100%;
  height: 100%;
  background-color: #e0e0e0; /* 연한 회색으로 채우기 */
}

/* 2. [수정됨] 미리보기 카드 지역 배지 스타일 */
.badge {
  /* 위치 설정 */
  position: absolute; /* 중요: 부모 컨테이너 위로 올림 */
  top: 12px; /* 위에서부터 간격 */
  left: 12px; /* 왼쪽에서부터 간격 */
  z-index: 10; /* 이미지보다 위에 보이도록 설정 */

  /* 📌 버튼 모양 스타일 (이 부분을 적용하세요) */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px; /* 위아래, 좌우 여백으로 버튼 모양 생성 */

  /* 색상 및 글꼴 */
  background-color: rgba(
    59,
    130,
    246,
    0.9
  ); /* 모달 태그와 비슷한 색상 (파란색 계열) */
  color: white; /* 글자색: 흰색 */
  font-size: 12px; /* 글자 크기 */
  font-weight: 600; /* 글자 두께 */

  /* 형태 설정 */
  border-radius: 20px; /* 완전 둥근 모서리 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 약간의 그림자 효과 */

  /* 기타 설정 */
  pointer-events: none; /* 배지 클릭 시 카드가 클릭되도록 설정 */
  white-space: nowrap; /* 글자가 줄바꿈되지 않도록 설정 */
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
/* 1. 태블릿 화면 (1024px 이하) */
@media (max-width: 1024px) {
  .preview-card {
    width: calc((100% - 40px) / 3);
    max-width: 100%; /* 화면이 작아질 때는 반응형으로 꽉 차게 조절 */
  }
}

/* 2. 작은 태블릿/가로 모바일 (768px 이하) */
@media (max-width: 768px) {
  .preview-card {
    width: calc((100% - 20px) / 2);
    max-width: 100%;
  }
}

/* 3. 세로 모바일 (480px 이하) */
@media (max-width: 480px) {
  .preview-card {
    width: 100%;
    max-width: 100%;
  }
}
</style>
