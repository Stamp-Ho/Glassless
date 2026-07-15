<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const previewPosts = ref([]);

// --- 카카오맵 관련 상태 및 변수 ---
const mapContainer = ref(null); // 지도가 그려질 DOM 요소 (template의 ref="mapContainer")
let mapInstance = null; // 카카오맵 인스턴스를 저장할 변수
const KAKAO_APP_KEY = 'b7b4f01e9203d5f62b2fb487cb0fdab5'; // 발급받은 JS 앱 키

// 메인 페이지에 표시할 주요 랜드마크 (app.js의 데이터 로드 대신 하드코딩으로 가볍게 처리)
const landmarks = [
  { title: '서울시청', lat: 37.5665, lng: 126.9780 },
  { title: 'N서울타워', lat: 37.5511, lng: 126.9882 },
  { title: '경복궁', lat: 37.5796, lng: 126.9770 },
  { title: 'DDP', lat: 37.5665, lng: 127.0098 }
];

onMounted(() => {
  // 1. 게시물 데이터 로드 (기존 로직 유지)
  const savedPosts = localStorage.getItem('localhub_posts');
  if (savedPosts) {
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

  // 2. 카카오맵 SDK 로드 시작
  loadKakaoMapSdk();
});

onUnmounted(() => {
  // 컴포넌트 파괴 시 메모리 누수를 막기 위해 인스턴스 참조 해제
  mapInstance = null;
});

const goToPostList = () => {
  router.push('/posts');
};

// --- 카카오맵 핵심 기능 통합 부분 ---

// 1. SDK 동적 로드 (app.js의 loadKakaoMapSdk 기능)
function loadKakaoMapSdk() {
  if (window.kakao && window.kakao.maps) {
    // 이미 로드된 경우 바로 초기화
    window.kakao.maps.load(() => initMap());
    return;
  }

  const script = document.createElement('script');
  script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_APP_KEY}&autoload=false`;
  script.async = true;
  
  script.onload = () => {
    if (window.kakao && window.kakao.maps) {
      window.kakao.maps.load(() => initMap());
    } else {
      console.error('카카오맵 SDK 로드에 실패했습니다.');
    }
  };
  
  script.onerror = () => {
    console.error('카카오맵 스크립트를 불러오는 중 에러가 발생했습니다. 도메인 허용 설정을 확인하세요.');
  };
  
  document.head.appendChild(script);
}

// 2. 지도 초기화 (app.js의 initMap 기능 일부)
function initMap() {
  if (!mapContainer.value) return; // DOM 요소가 없으면 중단

  const options = {
    center: new window.kakao.maps.LatLng(37.5665, 126.9780), // 초기 중심 좌표 (서울시청)
    level: 7 // 메인 페이지 뷰에 맞게 적당한 축척으로 설정 (app.js는 9였음)
  };

  // 지도 객체 생성
  mapInstance = new window.kakao.maps.Map(mapContainer.value, options);

  // 리사이즈 및 레이아웃 틀어짐 방지 (타일 로드 지연 문제 해결)
  setTimeout(() => {
    if (mapInstance) mapInstance.relayout();
  }, 100);

  // 지도 초기화 후 마커 그리기 실행
  renderLandmarks();
}

// 3. 커스텀 마커 이미지 생성 (app.js의 createMarkerImage 기능)
function createMarkerImage() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="44" viewBox="0 0 32 44">
      <path fill="#2e86de" d="M16 0C7.2 0 0 7.2 0 16c0 9.6 16 28 16 28s16-18.4 16-28C32 7.2 24.8 0 16 0z"/>
      <circle cx="16" cy="16" r="8" fill="#fff"/>
    </svg>`;
    
  return new window.kakao.maps.MarkerImage(
    `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
    new window.kakao.maps.Size(32, 44),
    { offset: new window.kakao.maps.Point(16, 44) } // 마커 좌표에 일치시킬 이미지 안의 좌표
  );
}

// 4. 지도 위에 핀(마커) 그리기 (app.js의 마커 렌더링 로직 단순화)
function renderLandmarks() {
  if (!mapInstance) return;

  const markerImage = createMarkerImage();

  landmarks.forEach(place => {
    const position = new window.kakao.maps.LatLng(place.lat, place.lng);
    
    // 마커 생성
    const marker = new window.kakao.maps.Marker({
      position: position,
      map: mapInstance,
      title: place.title,
      image: markerImage
    });

    // 마커 클릭 시 툴팁(인포윈도우) 띄우기 기능 추가
    const infowindow = new window.kakao.maps.InfoWindow({
      content: `<div style="padding:5px; font-size:12px; font-family:sans-serif; color:#333;">${place.title}</div>`
    });

    window.kakao.maps.event.addListener(marker, 'click', () => {
      infowindow.open(mapInstance, marker);
    });
  });
}
</script>

<template>
  <main class="home-page">
    <section class="hero-map-section">
      <div class="map-preview" ref="mapContainer"></div>
      
      <button class="btn-map-sm" @click="router.push('/map')">
        📍 지도에서 찾기
      </button>
    </section>

    <section class="preview-section">
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

.hero-map-section {
  width: 100%;
  height: 320px;
  position: relative;
  overflow: hidden;
  background-color: #E3ECE9;
}

.map-preview {
  width: 100%;
  height: 100%;
}

.btn-map-sm {
  position: absolute;
  top: 24px;
  left: 24px;
  background-color: var(--color-airbnb-dark, #222222);
  color: white;
  border: none;
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s, background-color 0.2s;
  z-index: 10; /* 버튼이 지도 위에 표시되도록 z-index 설정 */
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
  color: var(--color-airbnb-red, #ff385c);
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

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.preview-card {
  flex: 0 0 calc(25% - 15px);
  min-width: 260px;
  background-color: white;
  border: 1px solid var(--color-border, #e5e5e5);
  border-radius: var(--radius-airbnb, 12px);
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
  color: var(--color-airbnb-gray, #717171);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>