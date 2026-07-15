<script setup>
import { ref, nextTick } from "vue";
import CommonHeader from "./components/CommonHeader.vue";

const isChatOpen = ref(false);
const chatMessage = ref("");
const isLoading = ref(false);
const chatBodyRef = ref(null);
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const chatHistory = ref([
  {
    sender: "bot",
    text: '안녕하세요! GlassLESS 로컬 가이드 봇입니다. 🗺️\n\n"부산 수영구", "제주 애월읍"처럼 구체적인 지역명과 함께 원하는 테마나 활동을 입력해주시면 더욱 정확하고 상세한 맞춤 정보를 안내해 드릴 수 있습니다!',
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
        region: "string",
        category: "string",
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
  const regions = [
    "서울",
    "부산",
    "제주",
    "인천",
    "대구",
    "대전",
    "광주",
    "울산",
    "수영구",
    "해운대",
    "애월",
  ];
  for (const reg of regions) {
    if (text.includes(reg)) return reg;
  }
  return "";
};

const isWeatherOpen = ref(false);
const inputCity = ref("");
const isWeatherLoading = ref(false);
const weatherResult = ref(null);

const WEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY;
const WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather";

const toggleWeather = () => {
  isWeatherOpen.value = !isWeatherOpen.value;
  if (isWeatherOpen.value) {
    isChatOpen.value = false;
    weatherResult.value = null;
    inputCity.value = "";
  }
};

const convertToEnglishCity = (cityTxt) => {
  const city = cityTxt.trim();
  if (city.includes("서울")) return { eng: "Seoul", kor: "서울특별시" };
  if (city.includes("부산")) return { eng: "Busan", kor: "부산광역시" };
  if (city.includes("제주")) return { eng: "Jeju", kor: "제주특별자치도" };
  if (city.includes("인천")) return { eng: "Incheon", kor: "인천광역시" };
  if (city.includes("대구")) return { eng: "Daegu", kor: "대구광역시" };
  if (city.includes("대전")) return { eng: "Daejeon", kor: "대전광역시" };
  if (city.includes("광주")) return { eng: "Gwangju", kor: "광주광역시" };
  if (city.includes("울산")) return { eng: "Ulsan", kor: "울산광역시" };
  if (city.includes("경기") || city.includes("수원"))
    return { eng: "Suwon", kor: "경기도" };
  if (city.includes("강원") || city.includes("춘천"))
    return { eng: "Chuncheon", kor: "강원도" };
  if (city.includes("충북")) return { eng: "Cheongju", kor: "충청북도" };
  if (city.includes("충남")) return { eng: "Cheonan", kor: "충청남도" };
  if (city.includes("전북")) return { eng: "Jeonju", kor: "전라북도" };
  if (city.includes("전남")) return { eng: "Yeosu", kor: "전라남도" };
  if (city.includes("경북")) return { eng: "Pohang", kor: "경상북도" };
  return { eng: city, kor: city };
};

const getWeatherStatus = (statusInfo) => {
  const main = statusInfo.main.toLowerCase();
  if (main.includes("clear")) return "맑음 ☀️";
  if (main.includes("cloud")) return "구름 조금 ☁️";
  if (main.includes("rain")) return "비 🌧️";
  if (main.includes("drizzle")) return "이슬비 🌦️";
  if (main.includes("thunderstorm")) return "천둥 ⚡";
  if (main.includes("snow")) return "눈 ❄️";
  if (main.includes("mist") || main.includes("fog") || main.includes("haze"))
    return "안개 🌫️";
  return "맑음/흐림 🌤️";
};

const generateWeatherComment = (statusStr, tempNum) => {
  if (statusStr.includes("비"))
    return "현재 비가 내리고 있어 외출 시 우산이 필수입니다. ☕";
  if (statusStr.includes("눈"))
    return "눈이 내려 길이 미끄러울 수 있으니 이동 시 주의하세요. ☃️";
  if (tempNum >= 28)
    return `현재 기온이 ${tempNum}°C로 다소 무더운 날씨입니다.`;
  if (tempNum <= 5) return `현재 기온이 ${tempNum}°C로 날씨가 많이 춥습니다.`;
  return "야외 활동을 즐기기에 매우 쾌적한 날씨입니다! 🗺️";
};

const searchWeather = async () => {
  const cityInput = inputCity.value.trim();
  if (!cityInput) return;

  isWeatherLoading.value = true;
  weatherResult.value = null;
  const targetCity = convertToEnglishCity(cityInput);

  try {
    const url = `${WEATHER_BASE_URL}?q=${targetCity.eng}&appid=${WEATHER_API_KEY}&units=metric&lang=kr`;
    const response = await fetch(url);

    if (response.status === 401) {
      weatherResult.value = {
        city: "인증 에러 (401)",
        temp: "--°C",
        status: "키 확인 필요 🔑",
        comment: "API 키 활성화 대기 중이거나 키 입력을 확인해 주세요.",
      };
      return;
    }

    if (response.status === 404) {
      weatherResult.value = {
        city: cityInput,
        temp: "--°C",
        status: "검색 실패 🔍",
        comment: "도시 이름을 다시 확인해 주세요.",
      };
      return;
    }

    if (!response.ok) throw new Error("API 오류");

    const data = await response.json();
    const currentTemp = Math.round(data.main.temp);
    const currentStatus = getWeatherStatus(data.weather[0]);
    const dynamicComment = generateWeatherComment(currentStatus, currentTemp);

    weatherResult.value = {
      city: targetCity.kor,
      temp: `${currentTemp}°C`,
      status: currentStatus,
      comment: dynamicComment,
    };
  } catch (error) {
    console.error(error);
    weatherResult.value = {
      city: "오류",
      temp: "--°C",
      status: "연결 실패 ⚠️",
      comment: "네트워크 연결 상태를 확인해 주세요.",
    };
  } finally {
    isWeatherLoading.value = false;
  }
};
</script>

<template>
  <div class="app-layout">
    <CommonHeader />
    <router-view />

    <button
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

    <div v-if="isWeatherOpen" class="weather-modal">
      <div class="weather-header">
        <div class="header-info">
          <span class="weather-icon-mini">📍</span>
          <div>
            <h3>로컬 실시간 날씨</h3>
            <span class="sub-status">정밀 기상 정보</span>
          </div>
        </div>
      </div>

      <div class="weather-body">
        <div class="weather-input-row">
          <input
            v-model="inputCity"
            type="text"
            placeholder="예: 서울, 부산, 강원, 제주"
            @keyup.enter="searchWeather"
            :disabled="isWeatherLoading"
          />
          <button
            @click="searchWeather"
            :disabled="isWeatherLoading || !inputCity.trim()"
          >
            조회
          </button>
        </div>

        <div class="weather-result-display">
          <div v-if="isWeatherLoading" class="weather-inside-loading">
            <span class="mini-spinner"></span>
            <p>데이터를 분석하고 있습니다...</p>
          </div>
          <div v-else-if="weatherResult" class="weather-card-animate">
            <div class="main-weather-info">
              <span class="res-city">{{ weatherResult.city }}</span>
              <div class="temp-status-block">
                <span class="res-temp">{{ weatherResult.temp }}</span>
                <span class="res-status">{{ weatherResult.status }}</span>
              </div>
            </div>
            <div class="weather-comment-box">
              <p>💡 {{ weatherResult.comment }}</p>
            </div>
          </div>
          <div v-else class="weather-empty-state">
            <span>🗺️</span>
            <p>궁금한 지역을 입력해 주세요.</p>
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
        <button class="btn-close-mobile" @click="isChatOpen = false">
          닫기
        </button>
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
  background-color: var(--color-airbnb-dark);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.weather-modal {
  position: fixed;
  bottom: 176px;
  right: 32px;
  width: 360px;
  background-color: white;
  border-radius: var(--radius-airbnb);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 999;
  animation: weatherSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
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

.weather-header {
  background-color: #2bcbba;
  color: white;
  padding: 16px 20px;
}
.weather-icon-mini {
  font-size: 1.2rem;
}
.weather-body {
  padding: 20px;
  background-color: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.weather-input-row {
  display: flex;
  gap: 8px;
}
.weather-input-row input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 14px;
  outline: none;
  font-size: 0.88rem;
  background-color: white;
}
.weather-input-row input:focus {
  border-color: #2bcbba;
}
.weather-input-row button {
  background-color: #2bcbba;
  color: white;
  border: none;
  padding: 0 18px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
}

.weather-result-display {
  min-height: 150px;
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.weather-empty-state {
  text-align: center;
  color: #b2bec3;
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
  border-bottom: 1px dashed var(--color-border);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.res-city {
  font-size: 0.82rem;
  font-weight: 700;
  color: #7f8c8d;
}
.temp-status-block {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.res-temp {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--color-airbnb-dark);
}
.res-status {
  font-size: 1rem;
  font-weight: 700;
  color: #2bcbba;
}
.weather-comment-box {
  background-color: #f5f6fa;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 0.82rem;
  color: #485460;
  line-height: 1.4;
}
.weather-comment-box p {
  margin: 0;
}

.weather-inside-loading {
  text-align: center;
  color: var(--color-airbnb-gray);
  font-size: 0.82rem;
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

.chatbot-floating-btn {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: var(--color-airbnb-red);
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
  background-color: var(--color-airbnb-dark);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.chatbot-modal {
  position: fixed;
  bottom: 104px;
  right: 32px;
  width: 390px;
  height: 560px;
  background-color: white;
  border-radius: var(--radius-airbnb);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 999;
  animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.chatbot-header {
  background-color: var(--color-airbnb-dark);
  color: white;
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
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
}
.sub-status {
  font-size: 0.75rem;
  opacity: 0.7;
}
.btn-close-mobile {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 0.85rem;
  cursor: pointer;
  opacity: 0.8;
}

.chatbot-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  background-color: white;
  border: 1px solid var(--color-border);
  color: var(--color-airbnb-dark);
  border-top-left-radius: 2px;
}
.user .chat-bubble {
  background-color: var(--color-airbnb-red);
  color: white;
  border-top-right-radius: 2px;
}
.bubble-text {
  white-space: pre-line;
  word-break: break-all;
}

.reference-container {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--color-border);
}
.ref-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin-bottom: 8px;
}
.reference-card {
  background-color: #f9f9f9;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
  text-align: left;
}
.ref-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.ref-badge {
  background-color: #ebebeb;
  color: var(--color-airbnb-dark);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.ref-name {
  font-size: 0.85rem;
  color: var(--color-airbnb-dark);
}
.ref-address {
  font-size: 0.75rem;
  color: var(--color-airbnb-gray);
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
  background-color: var(--color-airbnb-gray);
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
  border-top: 1px solid var(--color-border);
  background-color: white;
  display: flex;
  gap: 8px;
  align-items: center;
}
.chatbot-footer input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 24px;
  padding: 12px 18px;
  outline: none;
  font-size: 0.9rem;
}
.chatbot-footer input:focus {
  border-color: var(--color-airbnb-red);
}
.chatbot-footer button {
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  padding: 12px 18px;
  border-radius: 24px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
}
.chatbot-footer button:disabled {
  background-color: #ebebeb;
  color: var(--color-airbnb-gray);
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .weather-floating-btn {
    bottom: 84px;
    right: 20px;
    width: 54px;
    height: 54px;
  }
  .weather-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
    border: none;
  }
  .chatbot-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
    border: none;
    z-index: 2000;
  }
  .btn-close-mobile {
    display: block;
  }
}
</style>
