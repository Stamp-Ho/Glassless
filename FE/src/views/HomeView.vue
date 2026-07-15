<script setup>
import { ref, onMounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const previewPosts = ref([]);

// .env 파일에 정의된 전역 환경 변수 가져오기
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

// =========================================================================
// 날씨(Weather) 관련 상태 및 로직
// =========================================================================
const isWeatherLoading = ref(false);
const weatherResult = ref(null);
const activeTheme = ref("default");

const WEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY;
const WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather";

const selectedCity = ref("seoul");
const selectedDistrict = ref("");

const regionsData = {
  seoul: {
    name: "서울특별시",
    fallbackQuery: "Seoul",
    districts: [
      { eng: "Gangnam-gu", kor: "강남구" },
      { eng: "Gangdong-gu", kor: "강동구" },
      { eng: "Gangbuk-gu", kor: "강북구" },
      { eng: "Gangseo-gu", kor: "강서구" },
      { eng: "Gwanak-gu", kor: "관악구" },
      { eng: "Gwangjin-gu", kor: "광진구" },
      { eng: "Guro-gu", kor: "구로구" },
      { eng: "Geumcheon-gu", kor: "금천구" },
      { eng: "Nowon-gu", kor: "노원구" },
      { eng: "Dobong-gu", kor: "도봉구" },
      { eng: "Dongdaemun-gu", kor: "동대문구" },
      { eng: "Dongjak-gu", kor: "동작구" },
      { eng: "Mapo-gu", kor: "마포구" },
      { eng: "Seodaemun-gu", kor: "서대문구" },
      { eng: "Seocho-gu", kor: "서초구" },
      { eng: "Seongdong-gu", kor: "성동구" },
      { eng: "Seongbuk-gu", kor: "성북구" },
      { eng: "Songpa-gu", kor: "송파구" },
      { eng: "Yangcheon-gu", kor: "양천구" },
      { eng: "Yeongdeungpo-gu", kor: "영등포구" },
      { eng: "Yongsan-gu", kor: "용산구" },
      { eng: "Eunpyeong-gu", kor: "은평구" },
      { eng: "Jongno-gu", kor: "종로구" },
      { eng: "Jung-gu,kr", kor: "중구" },
      { eng: "Jungnang-gu", kor: "중랑구" },
    ],
  },
  busan: {
    name: "부산광역시",
    fallbackQuery: "Busan",
    districts: [
      { eng: "Gangseo-gu,busan", kor: "강서구" },
      { eng: "Geumjeong-gu", kor: "금정구" },
      { eng: "Gijang-gun", kor: "기장군" },
      { eng: "Nam-gu,busan", kor: "남구" },
      { eng: "Dong-gu,busan", kor: "동구" },
      { eng: "Dongnae-gu", kor: "동래구" },
      { eng: "Busanjin-gu", kor: "부산진구" },
      { eng: "Buk-gu,busan", kor: "북구" },
      { eng: "Sasang-gu", kor: "사상구" },
      { eng: "Saha-gu", kor: "사하구" },
      { eng: "Seo-gu,busan", kor: "서구" },
      { eng: "Suyeong-gu", kor: "수영구" },
      { eng: "Yeonje-gu", kor: "연제구" },
      { eng: "Yeongdo-gu", kor: "영도구" },
      { eng: "Jung-gu,busan", kor: "중구" },
      { eng: "Haeundae", kor: "해운대구" },
    ],
  },
  daejeon_chungcheong: {
    name: "대전/충청권",
    fallbackQuery: "Daejeon",
    districts: [
      { eng: "Dong-gu,daejeon", kor: "대전 동구" },
      { eng: "Jung-gu,daejeon", kor: "대전 중구" },
      { eng: "Seo-gu,daejeon", kor: "대전 서구" },
      { eng: "Yuseong-gu", kor: "대전 유성구" },
      { eng: "Daedeok-gu", kor: "대전 대덕구" },
      { eng: "Cheongju", kor: "청주시" },
      { eng: "Chungho", kor: "충주시" },
      { eng: "Cheonan", kor: "천안시" },
      { eng: "Asan", kor: "아산시" },
    ],
  },
  gumi_gyeongbuk: {
    name: "구미/경북권",
    fallbackQuery: "Gumi",
    districts: [
      { eng: "Gumi", kor: "구미시" },
      { eng: "Jung-gu,daegu", kor: "대구 중구" },
      { eng: "Dong-gu,daegu", kor: "대구 동구" },
      { eng: "Seo-gu,daegu", kor: "대구 서구" },
      { eng: "Nam-gu,daegu", kor: "대구 남구" },
      { eng: "Buk-gu,daegu", kor: "대구 북구" },
      { eng: "Suseong-gu", kor: "대구 수성구" },
      { eng: "Dalseo-gu", kor: "대구 달서구" },
      { eng: "Pohang", kor: "포항시" },
      { eng: "Gyeongju", kor: "경주시" },
      { eng: "Andong", kor: "안동시" },
    ],
  },
  gwangju_jeolla: {
    name: "광주/전라권",
    fallbackQuery: "Gwangju",
    districts: [
      { eng: "Dong-gu,gwangju", kor: "광주 동구" },
      { eng: "Seo-gu,gwangju", kor: "광주 서구" },
      { eng: "Nam-gu,gwangju", kor: "광주 남구" },
      { eng: "Buk-gu,gwangju", kor: "광주 북구" },
      { eng: "Gwangsan-gu", kor: "광주 광산구" },
      { eng: "Jeonju", kor: "전주시" },
      { eng: "Iksan", kor: "익산시" },
      { eng: "Mokpo", kor: "목포시" },
      { eng: "Yeosu", kor: "여수시" },
      { eng: "Suncheon", kor: "순천시" },
    ],
  },
};

const availableDistricts = computed(() => {
  if (!selectedCity.value) return [];
  return regionsData[selectedCity.value].districts;
});

const processWeatherTheme = (statusInfo) => {
  const main = statusInfo.main.toLowerCase();
  if (main.includes("clear")) {
    activeTheme.value = "clear";
    return "맑음 ☀️";
  }
  if (main.includes("cloud")) {
    activeTheme.value = "clouds";
    return "구름 조금 ☁️";
  }
  if (
    main.includes("rain") ||
    main.includes("drizzle") ||
    main.includes("thunderstorm")
  ) {
    activeTheme.value = "rain";
    return "비 🌧️";
  }
  if (main.includes("snow")) {
    activeTheme.value = "snow";
    return "눈 ❄️";
  }
  if (main.includes("mist") || main.includes("fog") || main.includes("haze")) {
    activeTheme.value = "mist";
    return "안개 🌫️";
  }
  activeTheme.value = "default";
  return "맑음/흐림 🌤️";
};

const generateWeatherComment = (statusStr, tempNum) => {
  if (statusStr.includes("비"))
    return "현재 비가 내리고 있어 외출 시 우산이 필수입니다. ☕";
  if (statusStr.includes("눈"))
    return "눈이 내려 길이 미끄러울 수 있으니 안전에 주의하세요. ☃️";
  if (tempNum >= 28)
    return `현재 기온이 ${tempNum}°C로 다소 무덥습니다. 시원한 실내 코스를 추천합니다.`;
  if (tempNum <= 5)
    return `현재 기온이 ${tempNum}°C로 꽤 춥습니다. 실내 가이드 위주로 관람해 보세요.`;
  return "야외 활동을 즐기기에 매우 쾌적하고 좋은 날씨입니다! 🗺️";
};

const searchWeather = async () => {
  if (!selectedCity.value || !selectedDistrict.value) return;

  isWeatherLoading.value = true;
  weatherResult.value = null;

  const currentCityData = regionsData[selectedCity.value];
  const targetDistrict = currentCityData.districts.find(
    (d) => d.eng === selectedDistrict.value,
  );

  try {
    let url = `${WEATHER_BASE_URL}?q=${targetDistrict.eng}&appid=${WEATHER_API_KEY}&units=metric&lang=kr`;
    let response = await fetch(url);
    let isFallback = false;

    if (response.status === 404) {
      const fallbackQuery = currentCityData.fallbackQuery;
      url = `${WEATHER_BASE_URL}?q=${fallbackQuery}&appid=${WEATHER_API_KEY}&units=metric&lang=kr`;
      response = await fetch(url);
      isFallback = true;
    }

    if (response.status === 401) {
      weatherResult.value = {
        city: "인증 에러 (401)",
        temp: "--°C",
        status: "키 확인 필요 🔑",
        comment: "OpenWeather API 키값을 확인해 주세요.",
        isFallback: false,
      };
      activeTheme.value = "default";
      return;
    }

    if (!response.ok) throw new Error("API 오류");

    const data = await response.json();
    const currentTemp = Math.round(data.main.temp);
    const currentStatus = processWeatherTheme(data.weather[0]);
    const dynamicComment = generateWeatherComment(currentStatus, currentTemp);

    weatherResult.value = {
      city: `${currentCityData.name} ${targetDistrict.kor}`,
      temp: `${currentTemp}°C`,
      status: currentStatus,
      comment: dynamicComment,
      isFallback: isFallback,
      parentCityName: currentCityData.name,
    };
  } catch (error) {
    console.error(error);
    weatherResult.value = {
      city: "오류",
      temp: "--°C",
      status: "연결 실패 ⚠️",
      comment: "날씨 서버 응답이 원활하지 않습니다.",
      isFallback: false,
    };
    activeTheme.value = "default";
  } finally {
    isWeatherLoading.value = false;
  }
};

onMounted(async () => {
  try {
    const response = await fetch(`${BASE_URL}/api/posts`);

    if (response.status === 422) {
      previewPosts.value = [];
    } else if (response.ok) {
      const allPosts = await response.json();
      if (Array.isArray(allPosts)) {
        previewPosts.value = allPosts.slice(0, 6); // 3개씩 2줄
      }
    }
  } catch (error) {
    console.error("데이터 로드 실패:", error);
    previewPosts.value = [];
  }

  // 초기 날씨 검색 (서울 강남구)
  if (selectedDistrict.value === "") {
    selectedDistrict.value = "Gangnam-gu";
    await nextTick();
    searchWeather();
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

    <!-- 날씨 + 최신 추천 지역 정보 섹션 -->
    <section class="weather-preview-section">
      <!-- 왼쪽: 고정 날씨 패널 -->
      <div class="fixed-weather-panel">
        <div class="weather-header">
          <h3>📍 로컬 실시간 날씨</h3>
          <span class="weather-subtitle">전국 5대 권역</span>
        </div>

        <div class="weather-controls">
          <select v-model="selectedCity" class="weather-select">
            <option value="seoul">서울특별시</option>
            <option value="busan">부산광역시</option>
            <option value="daejeon_chungcheong">대전/충청권</option>
            <option value="gumi_gyeongbuk">구미/경북권</option>
            <option value="gwangju_jeolla">광주/전라권</option>
          </select>

          <select
            v-model="selectedDistrict"
            :disabled="!selectedCity"
            class="weather-select"
          >
            <option value="" disabled>구/지역 선택</option>
            <option
              v-for="dist in availableDistricts"
              :key="dist.eng"
              :value="dist.eng"
            >
              {{ dist.kor }}
            </option>
          </select>

          <button
            @click="searchWeather"
            :disabled="isWeatherLoading || !selectedCity || !selectedDistrict"
            class="btn-weather-search"
          >
            {{ isWeatherLoading ? "조회 중..." : "조회" }}
          </button>
        </div>

        <div :class="['weather-display', `theme-${activeTheme}`]">
          <div v-if="isWeatherLoading" class="weather-loading">
            <span class="mini-spinner"></span>
            <p>데이터 분석 중...</p>
          </div>

          <div v-else-if="weatherResult" class="weather-result">
            <div class="temp-box">
              <span class="temp">{{ weatherResult.temp }}</span>
              <span class="status">{{ weatherResult.status }}</span>
            </div>
            <div class="city-info">
              <p class="city-name">{{ weatherResult.city }}</p>
              <p class="comment">{{ weatherResult.comment }}</p>
            </div>
            <div v-if="weatherResult.isFallback" class="fallback-note">
              ℹ️ 대표 날씨로 표시됨
            </div>
          </div>

          <div v-else class="weather-empty">
            <p>구/지역을 선택하고 조회해주세요.</p>
          </div>
        </div>
      </div>

      <!-- 오른쪽: 최신 추천 지역 정보 (3개씩 2줄) -->
      <div class="preview-content">
        <h2 class="preview-title">✨ 최신 추천 지역 정보</h2>

        <div class="preview-grid">
          <div
            v-for="post in previewPosts"
            :key="post.id"
            class="preview-card"
            @click="goToPostDetail(post.id)"
          >
            <div class="card-image-container">
              <img
                :src="post.thumbnail_url || '/images/og-thumbnail.jpg'"
                :alt="post.title"
                class="card-image"
              />
              <span class="badge">{{ post.region || "지역 정보 없음" }}</span>
            </div>
            <div class="card-info">
              <h3 class="card-title">{{ post.title }}</h3>
              <p class="card-desc">{{ post.content }}</p>
            </div>
          </div>
        </div>

        <div v-if="previewPosts.length === 0" class="empty-state">
          <p>게시물이 없습니다.</p>
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

/* =========================================================================
   🌤️ 날씨 + 프리뷰 섹션 (고정 레이아웃)
   ========================================================================= */
.weather-preview-section {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 32px;
  align-items: stretch;
}

/* 왼쪽: 고정 날씨 패널 */
.fixed-weather-panel {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  padding: 24px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 100px;
  height: 100%;
}

.weather-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-radius: 10px;
  border-bottom: 2px solid #2bcbba;
}

.weather-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin: 0 0 4px 0;
}

.weather-subtitle {
  font-size: 0.8rem;
  color: var(--color-airbnb-gray);
}

.weather-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.weather-select {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.9rem;
  outline: none;
  background-color: white;
  color: var(--color-airbnb-dark);
  cursor: pointer;
  transition: border-color 0.2s;
}

.weather-select:focus {
  border-color: #2bcbba;
}

.weather-select:disabled {
  background-color: #f5f5f5;
  color: var(--color-airbnb-gray);
  cursor: not-allowed;
}

.btn-weather-search {
  background-color: #2bcbba;
  color: white;
  border: none;
  padding: 10px 12px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-weather-search:hover:not(:disabled) {
  background-color: #20a899;
}

.btn-weather-search:disabled {
  background-color: #d0d0d0;
  cursor: not-allowed;
}

.weather-display {
  min-height: 200px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: all 0.3s ease;
}

.weather-display.theme-clear {
  background: linear-gradient(135deg, #e0f2fe 0%, #fffbeb 100%);
  border-color: #fde047;
}

.weather-display.theme-clouds {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
}

.weather-display.theme-rain {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  border-color: #475569;
}

.weather-display.theme-snow {
  background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #d8b4fe;
}

.weather-display.theme-mist {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-color: #e2e8f0;
}

.weather-loading,
.weather-empty {
  text-align: center;
  color: var(--color-airbnb-gray);
}

.weather-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.mini-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #2bcbba;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.weather-result {
  text-align: center;
}

.temp-box {
  margin-bottom: 16px;
}

.temp {
  display: block;
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--color-airbnb-dark);
  line-height: 1.2;
}

.status {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: #2bcbba;
  margin-top: 4px;
}

.city-info {
  border-top: 1px dashed var(--color-border);
  padding-top: 12px;
}

.city-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin: 0 0 8px 0;
}

.comment {
  font-size: 0.85rem;
  color: var(--color-airbnb-gray);
  line-height: 1.5;
  margin: 0;
}

.fallback-note {
  margin-top: 12px;
  padding: 8px;
  background-color: rgba(255, 249, 219, 0.3);
  border: 1px solid #ffe066;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #f08c00;
}

/* 오른쪽: 최신 추천 지역 정보 */
.preview-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preview-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin: 0;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.preview-card {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}

.card-image-container {
  position: relative;
  width: 100%;
  height: 160px;
  overflow: hidden;
  border-radius: 8px 8px 0 0;
  background-color: #f3f3f3;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.badge {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  background-color: rgba(59, 130, 246, 0.9);
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  pointer-events: none;
  white-space: nowrap;
}

.card-info {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.card-desc {
  font-size: 0.85rem;
  color: var(--color-airbnb-gray);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-airbnb-gray);
}

/* =========================================================================
   📱 반응형 처리 (태블릿 및 모바일)
   ========================================================================= */
@media (max-width: 1200px) {
  .weather-preview-section {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .fixed-weather-panel {
    position: static;
    top: auto;
  }

  .preview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .preview-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .fixed-weather-panel {
    padding: 16px;
  }

  .weather-header h3 {
    font-size: 1rem;
  }

  .preview-title {
    font-size: 1.1rem;
  }
}

@media (max-width: 640px) {
  .weather-preview-section {
    padding: 0 16px;
    margin: 24px auto;
  }

  .preview-grid {
    grid-template-columns: 1fr;
  }

  .card-image-container {
    height: 140px;
  }

  .weather-display {
    min-height: 160px;
  }
}
</style>
