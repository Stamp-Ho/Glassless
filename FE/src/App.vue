<!-- src/App.vue -->
<script setup>
import { ref, nextTick } from 'vue';
import CommonHeader from './components/CommonHeader.vue';

// 챗봇 모달 및 메시지 상태 관리
const isChatOpen = ref(false);
const chatMessage = ref('');
const isLoading = ref(false); // 답변 대기 중 로딩 상태 표시
const chatBodyRef = ref(null); // 자동 스크롤을 위한 Ref

const chatHistory = ref([
  { sender: 'bot', text: '안녕하세요! GlassLESS 로컬 가이드 봇입니다. 🗺️\n전국의 권역별 명소, 모범음식점 위치나 로컬 축제 등 궁금한 점을 편하게 물어보세요!' }
]);

// 챗봇 토글 및 스크롤 하단 고정
const toggleChat = async () => {
  isChatOpen.value = !isChatOpen.value;
  if (isChatOpen.value) {
    await scrollToBottom();
  }
};

// 스크롤 최하단 이동 함수
const scrollToBottom = async () => {
  await nextTick();
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight;
  }
};

// 실제 FastAPI 백엔드와 통신하여 답변 수신
const sendChat = async () => {
  const userText = chatMessage.value.trim();
  if (!userText || isLoading.value) return;

  // 1. 유저 말풍선 추가
  chatHistory.value.push({ sender: 'user', text: userText });
  chatMessage.value = '';
  isLoading.value = true;
  await scrollToBottom();

  try {
    // 2. FastAPI /api/chat 엔드포인트로 POST 요청 전송
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userText }),
    });

    if (!response.ok) {
      throw new Error('서버 응답 오류가 발생했습니다.');
    }

    const data = await response.json();
    
    // 3. 챗봇 답변 말풍선 추가
    chatHistory.value.push({ sender: 'bot', text: data.reply });
  } catch (error) {
    console.error(error);
    chatHistory.value.push({ 
      sender: 'bot', 
      text: '⚠️ 현재 챗봇 서버와 연결이 원활하지 않습니다. API 서버가 켜져 있는지, .env 파일에 OpenAI 키가 올바르게 입력되었는지 확인해 주세요.' 
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
};
</script>

<template>
  <div class="app-layout">
    <CommonHeader />
    <router-view />

    <!-- 🌐 우측 하단 고정 플로팅 챗봇 버튼 -->
    <button class="chatbot-floating-btn" @click="toggleChat" :class="{ active: isChatOpen }" aria-label="챗봇 열기">
      <span v-if="!isChatOpen">💬</span>
      <span v-else>✕</span>
    </button>

    <!-- 💬 챗봇 모달창 (반응형 모바일 완벽 대응) -->
    <div v-if="isChatOpen" class="chatbot-modal">
      <div class="chatbot-header">
        <div class="header-info">
          <span class="status-dot"></span>
          <div>
            <h3>GlassLESS AI 가이드</h3>
            <span class="sub-status">실시간 인공지능 탐색 중</span>
          </div>
        </div>
        <button class="btn-close-mobile" @click="isChatOpen = false">닫기</button>
      </div>

      <!-- 대화 히스토리 출력 영역 -->
      <div class="chatbot-body" ref="chatBodyRef">
        <div 
          v-for="(msg, index) in chatHistory" 
          :key="index" 
          :class="['chat-bubble-wrapper', msg.sender]"
        >
          <div class="chat-bubble">
            <!-- 줄바꿈 반영 렌더링 -->
            <p class="bubble-text">{{ msg.text }}</p>
          </div>
        </div>

        <!-- 답변 생성 중일 때 보여줄 세련된 로딩 애니메이션 -->
        <div v-if="isLoading" class="chat-bubble-wrapper bot">
          <div class="chat-bubble loading-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- 입력부 -->
      <div class="chatbot-footer">
        <input 
          v-model="chatMessage" 
          type="text" 
          placeholder="지역 축제, 맛집, 관광지 질문하기..." 
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
@import './assets/main.css';

/* 플로팅 버튼 */
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
  transition: transform 0.2s, background-color 0.2s;
}

.chatbot-floating-btn:hover {
  transform: scale(1.05);
}

.chatbot-floating-btn.active {
  background-color: var(--color-airbnb-dark);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

/* 챗봇 모달창 기본 스타일 (데스크톱) */
.chatbot-modal {
  position: fixed;
  bottom: 104px;
  right: 32px;
  width: 380px;
  height: 540px;
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

@keyframes slideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* 헤더 영역 */
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
  display: inline-block;
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
  display: none; /* 기본 데스크톱에서는 닫기 텍스트 버튼 숨김 */
  background: none;
  border: none;
  color: white;
  font-size: 0.85rem;
  cursor: pointer;
  opacity: 0.8;
}

/* 바디 대화 영역 */
.chatbot-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #F8F9FA;
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
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
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
  white-space: pre-line; /* 백엔드로부터 넘어온 줄바꿈('\n') 지원 */
  word-break: break-all;
}

/* 점 세개짜리 챗봇 타이핑 로딩 애니메이션 */
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

.loading-bubble .dot:nth-child(1) { animation-delay: -0.32s; }
.loading-bubble .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* 푸터 입력 영역 */
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
  transition: border-color 0.2s;
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
  transition: opacity 0.2s;
}

.chatbot-footer button:disabled {
  background-color: #EBEBEB;
  color: var(--color-airbnb-gray);
  cursor: not-allowed;
}

/* 📱 완벽한 모바일 대응 (반응형 쿼리) */
@media (max-width: 600px) {
  .chatbot-floating-btn {
    bottom: 20px;
    right: 20px;
    width: 54px;
    height: 54px;
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
    z-index: 2000; /* 모바일에서는 화면을 전부 가리며 모달 최상단으로 띄움 */
  }

  .btn-close-mobile {
    display: block; /* 모바일 환경에서만 '닫기' 버튼 노출 */
  }
}
</style>