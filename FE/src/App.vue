<script setup>
import { ref, nextTick, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import CommonHeader from "./components/CommonHeader.vue";

const route = useRoute();
const isHomePage = computed(() => route.path === "/");

// =========================================================================
// [0] 🌓 다크 모드 (Dark Mode) 설정 및 상태 관리
// =========================================================================
const isDarkMode = ref(false);

const initTheme = () => {
  const savedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
    isDarkMode.value = true;
    document.documentElement.classList.add("dark");
  } else {
    isDarkMode.value = false;
    document.documentElement.classList.remove("dark");
  }
};

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
  }
};

onMounted(() => {
  initTheme();
});

// =========================================================================
// [1] 💬 챗봇(Chatbot) 관련 스크립트 영역
// =========================================================================
const isChatOpen = ref(false);
const chatMessage = ref("");
const isLoading = ref(false);
const chatBodyRef = ref(null);
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const chatHistory = ref([
  {
    sender: "bot",
    text: "안녕하세요! GlassLESS 로컬 가이드 봇입니다.🗺️\n\n서울, 부산 같은 지역명과 함께 관광지/문화시설/축제공연행사/여행코스/레포츠/숙박/쇼핑/음식점 키워드를 입력해주시면 더욱 정확하고 상세한 맞춤 정보를 안내해 드릴 수 있습니다!",
  },
]);

const toggleChat = async () => {
  isChatOpen.value = !isChatOpen.value;
  if (isChatOpen.value) {
    isWeatherOpen.value = false;
    await scrollToBottom();
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight;
  }
};

const sendChat = async () => {
  const userText = chatMessage.value.trim();
  if (!userText || isLoading.value) return;

  chatHistory.value.push({ sender: "user", text: userText });
  chatMessage.value = "";
  isLoading.value = true;
  await scrollToBottom();

  try {
    const detectedRegion = extractRegion(userText);
    const response = await fetch(`${BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: userText,
        region: "",
        category: "",
      }),
    });

    if (response.status === 422) {
      chatHistory.value.push({
        sender: "bot",
        text: "🤖 챗봇 답변 생성에 실패했습니다.",
      });
      return;
    }

    if (!response.ok) throw new Error("서버 불안정");

    const data = await response.json();
    chatHistory.value.push({
      sender: "bot",
      text: data.answer,
      references: data.references || [],
    });
  } catch (error) {
    console.error(error);
    chatHistory.value.push({
      sender: "bot",
      text: "🤖 죄송합니다. 답변 중 오류가 발생했습니다.",
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
};

const extractRegion = (text) => {
  const regions = ["서울", "부산", "수영구", "해운대", "대전", "구미", "광주"];
  for (const reg of regions) {
    if (text.includes(reg)) return reg;
  }
  return "";
};

// =========================================================================
// [2] ☀️ 날씨(Weather) 관련 스크립트 영역 (전국 5대 권역 확장)
// =========================================================================
const isWeatherOpen = ref(false);
const isWeatherLoading = ref(false);
const weatherResult = ref(null);

const activeTheme = ref("default");

const WEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY;
const WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather";

const selectedCity = ref("");
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

const handleCityChange = () => {
  selectedDistrict.value = "";
};

const toggleWeather = () => {
  isWeatherOpen.value = !isWeatherOpen.value;
  if (isWeatherOpen.value) {
    isChatOpen.value = false;
    weatherResult.value = null;
    selectedCity.value = "";
    selectedDistrict.value = "";
    activeTheme.value = "default";
  }
};

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
</script>

<template>
  <div class="app-layout">
    <CommonHeader 
      :isDarkMode="isDarkMode"
      @toggle-theme="toggleTheme"
    />
    <router-view />

    <!-- ✨ 고정 다크모드 버튼 (홈페이지가 아닐 때만 표시) -->
    <button
      v-if="!isHomePage"
      class="theme-toggle-btn"
      @click="toggleTheme"
      aria-label="다크 모드 토글"
    >
      <span v-if="isDarkMode">☀️</span>
      <span v-else>🌙</span>
    </button>

    <!-- 우측 아래 기존 날씨 / 챗봇 버튼 (홈페이지가 아닐 때만 표시) -->
    <button
      v-if="!isHomePage"
      class="weather-floating-btn"
      @click="toggleWeather"
      :class="{ active: isWeatherOpen }"
    >
      <span v-if="!isWeatherOpen">🌤️</span>
      <span v-else>✕</span>
    </button>

    <button
      class="chatbot-floating-btn"
      @click="toggleChat"
      :class="{ active: isChatOpen }"
    >
      <span v-if="!isChatOpen">💬</span>
      <span v-else>✕</span>
    </button>

    <div v-if="isWeatherOpen && !isHomePage" class="weather-modal">
      <div class="weather-header">
        <div class="header-info">
          <span class="weather-icon-mini">📍</span>
          <div>
            <h3>로컬 실시간 날씨</h3>
            <span class="sub-status">전국 5대 권역 상세 날씨 정보</span>
          </div>
        </div>
        <button class="btn-close-modal" @click="isWeatherOpen = false">
          ✕
        </button>
      </div>

      <div class="weather-body">
        <div class="weather-category-selectors">
          <select
            v-model="selectedCity"
            @change="handleCityChange"
            class="weather-select"
          >
            <option value="" disabled selected>권역 선택</option>
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
            <option value="" disabled selected>구/지역 선택</option>
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
            조회
          </button>
        </div>

        <div :class="['weather-result-display', `modal-theme-${activeTheme}`]">
          <div class="modal-weather-effects">
            <div v-if="activeTheme === 'rain'" class="modal-rain-effect">
              <div class="m-drop" v-for="n in 12" :key="'m-rain-' + n"></div>
            </div>

            <div v-if="activeTheme === 'clouds'" class="modal-cloud-effect">
              <div class="m-moving-cloud m-cloud-1"></div>
              <div class="m-moving-cloud m-cloud-2"></div>
            </div>

            <div v-if="activeTheme === 'snow'" class="modal-snow-effect">
              <div class="m-flake" v-for="n in 10" :key="'m-snow-' + n"></div>
            </div>

            <div v-if="activeTheme === 'clear'" class="modal-sun-flare"></div>
          </div>

          <div v-if="isWeatherLoading" class="weather-inside-loading">
            <span class="mini-spinner"></span>
            <p>날씨 데이터를 분석하고 있습니다...</p>
          </div>

          <div
            v-else-if="weatherResult"
            class="weather-card-content weather-card-animate"
          >
            <div class="main-weather-info">
              <span class="res-city">{{ weatherResult.city }}</span>
              <div class="temp-status-block">
                <span class="res-temp">{{ weatherResult.temp }}</span>
                <span class="res-status">{{ weatherResult.status }}</span>
              </div>
            </div>

            <div
              v-if="weatherResult.isFallback"
              class="weather-fallback-banner"
            >
              <span class="alert-icon">ℹ️</span>
              <p>
                해당 구는 개별 기상 데이터가 없어
                <strong>{{ weatherResult.parentCityName }} 표준 날씨</strong>로
                대체 안내해 드립니다.
              </p>
            </div>

            <div class="weather-comment-box">
              <p>💡 {{ weatherResult.comment }}</p>
            </div>
          </div>

          <div v-else class="weather-empty-state">
            <span>🗺️</span>
            <p>상단의 권역과 구/지역을 선택해 주세요.</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isChatOpen" class="chatbot-modal">
      <div class="chatbot-header">
        <div class="header-info">
          <span class="status-dot"></span>
          <div>
            <h3>GlassLESS AI 가이드</h3>
            <span class="sub-status">맞춤 검색 모드</span>
          </div>
        </div>
        <button class="btn-close-modal" @click="isChatOpen = false">✕</button>
      </div>

      <div class="chatbot-body" ref="chatBodyRef">
        <div
          v-for="(msg, index) in chatHistory"
          :key="index"
          :class="['chat-bubble-wrapper', msg.sender]"
        >
          <div class="chat-bubble">
            <p class="bubble-text">{{ msg.text }}</p>
            <div
              v-if="msg.references && msg.references.length > 0"
              class="reference-container"
            >
              <h4 class="ref-title">📍 추천 연관 장소</h4>
              <div
                v-for="refItem in msg.references"
                :key="refItem.id"
                class="reference-card"
              >
                <div class="ref-card-header">
                  <span class="ref-badge">{{ refItem.category }}</span>
                  <strong class="ref-name">{{ refItem.name }}</strong>
                </div>
                <p class="ref-address">{{ refItem.address }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="chat-bubble-wrapper bot">
          <div class="chat-bubble loading-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <div class="chatbot-footer">
        <input
          v-model="chatMessage"
          type="text"
          placeholder="지역명과 함께 질문해 주세요"
          @keyup.enter="sendChat"
          :disabled="isLoading"
        />
        <button @click="sendChat" :disabled="isLoading || !chatMessage.trim()">
          전송
        </button>
      </div>
    </div>
  </div>
</template>

<style>
@import "./assets/main.css";

/* =========================================================================
   🌓 [테마 변수 관리] 라이트 / 다크모드 색상 선언 및 부드러운 전환 구현
   ========================================================================= */
:root {
  /* 라이트 모드 (기본 테마) */
  --bg-app: #ffffff;
  --bg-modal: #ffffff;
  --bg-body: #fafafa;
  --bg-chat-body: #f8f9fa;
  --bg-bubble-bot: #ffffff;
  --bg-bubble-user: #ff385c;
  --bg-ref-card: #f9f9f9;

  --text-main: #222222;
  --text-sub: #767676;
  --text-bot: #222222;
  --text-user: #ffffff;

  --border-color: #ebebeb;
  --input-bg: #ffffff;
}

html.dark {
  /* 다크 모드 (html 클래스 적용 시 활성화) */
  --bg-app: #121212;
  --bg-modal: #1e1e1e;
  --bg-body: #181818;
  --bg-chat-body: #151515;
  --bg-bubble-bot: #2d2d2d;
  --bg-bubble-user: #e02447;
  --bg-ref-card: #252525;

  --text-main: #161515; /* 또는 부드러운 화이트 톤인 #f5f5f5 추천 */
  --text-sub: #a0a0a0;
  --text-bot: #eaeaea;
  --text-user: #ffffff;

  --border-color: #333333;
  --input-bg: #2d2d2d;
}

/* 기본 앱 구조 - CSS 변수 연동 */
.app-layout {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  background-color: var(--bg-app);
  color: var(--text-main);
  transition:
    background-color 0.3s ease,
    color 0.3s ease;
}

/* =========================================================================
   🌓 왼쪽 아래 다크모드 플로팅 버튼 스타일
   ========================================================================= */
.theme-toggle-btn {
  position: fixed;
  left: 24px; /* 왼쪽 여백 */
  bottom: 24px; /* 아래쪽 여백 (오른쪽 챗봇 버튼과 대칭 높이) */
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: var(--bg-modal); /* 다크/라이트 테마 배경색에 부드럽게 반응 */
  border: 1px solid var(--border-color);
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 999;
}

/* 마우스 호버 시 살짝 떠오르는 효과 */
.theme-toggle-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

/* =========================================================================
   📱 모바일 반응형 대응 (화면이 작아질 때 여백 및 크기 조정)
   ========================================================================= */
@media (max-width: 480px) {
  .theme-toggle-btn {
    left: 16px; /* 모바일에서는 여백을 약간 줄임 */
    bottom: 20px;
    width: 48px;
    height: 48px;
    font-size: 18px;
  }
}

/* =========================================================================
   🖼️ [모달 내부 날씨 카드 테마 스타일 및 이펙트]
   ========================================================================= */
.weather-result-display {
  position: relative;
  min-height: 170px;
  background-color: var(--bg-modal);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  transition:
    background 0.6s ease,
    border-color 0.4s ease,
    background-color 0.3s ease;
}

.weather-card-content {
  position: relative;
  z-index: 5;
}
.modal-theme-default {
  background-color: var(--bg-modal);
}
.modal-theme-clear {
  background: linear-gradient(
    135deg,
    #e0f2fe 0%,
    #fffbeb 60%,
    #fef3c7 100%
  ) !important;
  border-color: #fde047;
}
.modal-theme-clouds {
  background: linear-gradient(
    135deg,
    #f1f5f9 0%,
    #e2e8f0 70%,
    #cbd5e1 100%
  ) !important;
  border-color: #cbd5e1;
}
.modal-theme-rain {
  background: linear-gradient(
    135deg,
    #475569 0%,
    #334155 60%,
    #1e293b 100%
  ) !important;
  border-color: #475569;
}
.modal-theme-rain .res-city {
  color: #cbd5e1 !important;
}
.modal-theme-rain .res-temp {
  color: #ffffff !important;
}
.modal-theme-rain .res-status {
  color: #60a5fa !important;
}
.modal-theme-rain .weather-comment-box {
  background-color: rgba(15, 23, 42, 0.45) !important;
  color: #f1f5f9 !important;
}
.modal-theme-snow {
  background: linear-gradient(
    135deg,
    #f3e8ff 0%,
    #faf5ff 60%,
    #e9d5ff 100%
  ) !important;
  border-color: #d8b4fe;
}
.modal-theme-mist {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
  border-color: #e2e8f0;
}

/* =========================================================================
   🌧️ [모달용 날씨 이펙트 애니메이션]
   ========================================================================= */
.modal-weather-effects {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}
.modal-rain-effect {
  position: relative;
  width: 100%;
  height: 100%;
}
.modal-rain-effect .m-drop {
  position: absolute;
  background: linear-gradient(transparent, rgba(147, 197, 253, 0.7));
  width: 1.5px;
  height: 40px;
  animation: m-fall 1s infinite linear;
  opacity: 0.6;
}
.modal-rain-effect .m-drop:nth-child(4n + 1) {
  left: 10%;
  animation-delay: 0.1s;
  animation-duration: 1.2s;
}
.modal-rain-effect .m-drop:nth-child(4n + 2) {
  left: 40%;
  animation-delay: 0.4s;
  animation-duration: 0.9s;
}
.modal-rain-effect .m-drop:nth-child(4n + 3) {
  left: 70%;
  animation-delay: 0.2s;
  animation-duration: 1.1s;
}
.modal-rain-effect .m-drop:nth-child(4n + 4) {
  left: 90%;
  animation-delay: 0.6s;
  animation-duration: 0.8s;
}

@keyframes m-fall {
  0% {
    transform: translateY(-50px);
  }
  100% {
    transform: translateY(200px);
  }
}

.m-moving-cloud {
  position: absolute;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50px;
  filter: blur(4px);
}
.m-cloud-1 {
  width: 70px;
  height: 25px;
  top: 15%;
  left: -80px;
  animation: m-drift 18s infinite linear;
}
.m-cloud-2 {
  width: 90px;
  height: 30px;
  bottom: 15%;
  left: -100px;
  animation: m-drift 24s infinite linear;
  animation-delay: 4s;
  opacity: 0.7;
}
@keyframes m-drift {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(480px);
  }
}

.m-flake {
  position: absolute;
  background-color: white;
  border-radius: 50%;
  animation: m-snow 5s infinite linear;
  opacity: 0.85;
}
.m-flake:nth-child(3n + 1) {
  width: 4px;
  height: 4px;
  left: 20%;
  animation-duration: 6s;
}
.m-flake:nth-child(3n + 2) {
  width: 6px;
  height: 6px;
  left: 55%;
  animation-duration: 8s;
  animation-delay: 1s;
}
.m-flake:nth-child(3n + 3) {
  width: 3px;
  height: 3px;
  left: 85%;
  animation-duration: 4s;
  animation-delay: 0.5s;
}

@keyframes m-snow {
  0% {
    transform: translateY(-10px) translateX(0);
  }
  50% {
    transform: translateY(90px) translateX(10px);
  }
  100% {
    transform: translateY(180px) translateX(-5px);
  }
}

.modal-sun-flare {
  position: absolute;
  top: -40px;
  right: -40px;
  width: 140px;
  height: 140px;
  background: radial-gradient(
    circle,
    rgba(253, 224, 71, 0.4) 0%,
    rgba(255, 255, 255, 0) 70%
  );
  animation: m-pulse 5s infinite alternate ease-in-out;
}
@keyframes m-pulse {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

/* =========================================================================
   [UI 요소 기본 스타일링 - 테마 전면 교체]
   ========================================================================= */
.weather-category-selectors {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.weather-select {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.9rem;
  outline: none;
  background-color: var(--input-bg);
  color: var(--text-main);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23767676' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 14px;
  transition:
    background-color 0.3s,
    border-color 0.3s,
    color 0.3s;
}
.weather-select:disabled {
  background-color: var(--border-color);
  color: var(--text-sub);
  cursor: not-allowed;
}
.btn-weather-search {
  background-color: #2bcbba;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-weather-search:disabled {
  background-color: var(--border-color);
  color: var(--text-sub);
  cursor: not-allowed;
}

/* 플로팅 버튼 레이어 */
.weather-floating-btn {
  position: fixed;
  bottom: 104px;
  right: 32px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #2bcbba;
  color: white;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(43, 203, 186, 0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform 0.2s,
    background-color 0.2s;
}
.weather-floating-btn:hover {
  transform: scale(1.05);
  background-color: #20a899;
}
.weather-floating-btn.active {
  background-color: #222222;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.chatbot-floating-btn {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #ff385c;
  color: white;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(224, 26, 79, 0.35);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform 0.2s,
    background-color 0.2s;
}
.chatbot-floating-btn:hover {
  transform: scale(1.05);
}
.chatbot-floating-btn.active {
  background-color: #222222;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
/* 모달창 레이어 */
.weather-modal {
  position: fixed;
  /* ☀️기존 164px에서 180px로 올림
     날씨 플로팅 버튼(bottom 94px + 버튼 높이 54px = 148px)의 머리 위로 확실하게 띄웁니다. */
  bottom: 180px;

  right: 24px;
  width: 360px;
  background-color: var(--bg-modal);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 2000;
  animation: weatherSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  transition:
    background-color 0.3s,
    border-color 0.3s;
}

@keyframes weatherSlideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
.chatbot-modal {
  position: fixed;
  /* 💬 기존 90px에서 102px로 올림
     챗봇 플로팅 버튼(bottom 24px + 버튼 높이 54px = 78px)의 머리를 절대 가리지 않도록 조정합니다. */
  bottom: 102px;

  right: 24px;
  width: 390px;
  height: 560px;
  background-color: var(--bg-modal);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 2000;
  animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  transition:
    background-color 0.3s,
    border-color 0.3s;
}
@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* 공용 헤더 스타일링 및 닫기 버튼 */
.weather-header {
  background-color: #2bcbba;
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.weather-icon-mini {
  font-size: 1.2rem;
}
.weather-body {
  padding: 20px;
  background-color: var(--bg-body);
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: background-color 0.3s;
}
.weather-empty-state {
  text-align: center;
  color: var(--text-sub);
  z-index: 5;
}
.weather-empty-state span {
  font-size: 2rem;
  display: block;
  margin-bottom: 6px;
}
.weather-empty-state p {
  font-size: 0.82rem;
  margin: 0;
}
.weather-card-animate {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.main-weather-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-bottom: 1px dashed var(--border-color);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.res-city {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-sub);
}
.temp-status-block {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.res-temp {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--text-main);
}
.res-status {
  font-size: 1rem;
  font-weight: 700;
  color: #2bcbba;
}
.weather-fallback-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background-color: rgba(255, 249, 219, 0.15);
  border: 1px solid #ffe066;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 12px;
}
.weather-fallback-banner .alert-icon {
  font-size: 0.95rem;
  margin-top: 1px;
}
.weather-fallback-banner p {
  margin: 0;
  font-size: 0.78rem;
  color: #f08c00;
  line-height: 1.4;
  text-align: left;
}
.weather-fallback-banner strong {
  font-weight: 700;
  text-decoration: underline;
}
.weather-comment-box {
  background-color: var(--bg-body);
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 0.82rem;
  color: var(--text-main);
  line-height: 1.4;
  border: 1px solid var(--border-color);
}
.weather-comment-box p {
  margin: 0;
}
.weather-inside-loading {
  text-align: center;
  color: var(--text-sub);
  font-size: 0.82rem;
  z-index: 5;
}
.mini-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #2bcbba;
  border-radius: 50%;
  display: inline-block;
  animation: mini-spin 0.6s linear infinite;
  margin-bottom: 6px;
}
@keyframes mini-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.chatbot-header {
  background-color: #222222;
  color: white;
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-dot {
  width: 8px;
  height: 8px;
  background-color: #2ecc71;
  border-radius: 50%;
  box-shadow: 0 0 8px #2ecc71;
}
.chatbot-header h3 {
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}
.sub-status {
  font-size: 0.75rem;
  opacity: 0.7;
}

/* 닫기 버튼 */
.btn-close-modal {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  opacity: 0.8;
  transition:
    opacity 0.2s,
    transform 0.2s;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-close-modal:hover {
  opacity: 1;
  transform: scale(1.1);
}

.chatbot-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: var(--bg-chat-body);
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: background-color 0.3s;
}
.chat-bubble-wrapper {
  display: flex;
  width: 100%;
}
.chat-bubble-wrapper.bot {
  justify-content: flex-start;
}
.chat-bubble-wrapper.user {
  justify-content: flex-end;
}
.chat-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 0.9rem;
  line-height: 1.5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}
.bot .chat-bubble {
  background-color: var(--bg-bubble-bot);
  border: 1px solid var(--border-color);
  color: var(--text-bot);
  border-top-left-radius: 2px;
  transition:
    background-color 0.3s,
    border-color 0.3s,
    color 0.3s;
}
.user .chat-bubble {
  background-color: var(--bg-bubble-user);
  color: var(--text-user);
  border-top-right-radius: 2px;
}
.bubble-text {
  white-space: pre-line;
  word-break: break-all;
  margin: 0;
}
.reference-container {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}
.ref-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 8px;
}
.reference-card {
  background-color: var(--bg-ref-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
  text-align: left;
  transition:
    background-color 0.3s,
    border-color 0.3s;
}
.ref-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.ref-badge {
  background-color: var(--border-color);
  color: var(--text-main);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  transition:
    background-color 0.3s,
    color 0.3s;
}
.ref-name {
  font-size: 0.85rem;
  color: var(--text-main);
}
.ref-address {
  font-size: 0.75rem;
  color: var(--text-sub);
  margin: 0;
}
.loading-bubble {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 18px;
}
.loading-bubble .dot {
  width: 6px;
  height: 6px;
  background-color: var(--text-sub);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-bubble .dot:nth-child(1) {
  animation-delay: -0.32s;
}
.loading-bubble .dot:nth-child(2) {
  animation-delay: -0.16s;
}
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
.chatbot-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-modal);
  display: flex;
  gap: 8px;
  align-items: center;
  transition:
    background-color 0.3s,
    border-top 0.3s;
}
.chatbot-footer input {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: 12px 18px;
  outline: none;
  font-size: 0.9rem;
  background-color: var(--input-bg);
  color: var(--text-main);
  transition:
    background-color 0.3s,
    border-color 0.3s,
    color 0.3s;
}
.chatbot-footer input:focus {
  border-color: #ff385c;
}
.chatbot-footer button {
  background-color: #ff385c;
  color: white;
  border: none;
  padding: 12px 18px;
  border-radius: 24px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
}
.chatbot-footer button:disabled {
  background-color: var(--border-color);
  color: var(--text-sub);
  cursor: not-allowed;
}

/* =========================================================================
   🛠️ 모바일 화면 반응형 미디어 쿼리 (max-width: 600px) 고도화
   ========================================================================= */
@media (max-width: 600px) {
  .chatbot-floating-btn {
    bottom: 20px !important;
    right: 20px !important;
    width: 54px !important;
    height: 54px !important;
    z-index: 1000 !important;
  }

  .weather-floating-btn {
    bottom: 86px !important;
    right: 20px !important;
    width: 54px !important;
    height: 54px !important;
    z-index: 1000 !important;
  }

  .theme-toggle-btn {
    bottom: 152px !important;
    right: 20px !important;
    width: 54px !important;
    height: 54px !important;
    z-index: 1000 !important;
  }

  /* 모바일 전체화면 레이아웃 */
  .weather-modal,
  .chatbot-modal {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    height: 100% !important;
    border-radius: 0 !important;
    border: none !important;
    z-index: 2500 !important;
  }
}

/* App.vue의 <style> 태그 안쪽에 추가 */

html.dark .section-title {
  color: #f1f5f9 !important; /* 무조건 밝은 미색으로 고정 */
}

/* 추가적으로 격자(grid) 안의 다른 제목들도 어둡다면 함께 처리 */
html.dark .grid-section h2,
html.dark .grid-section .section-title {
  color: #f1f5f9 !important;
}
</style>
