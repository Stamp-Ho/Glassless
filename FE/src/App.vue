<script setup>
import { ref } from 'vue';
import CommonHeader from './components/CommonHeader.vue';

// 챗봇 모달 상태 관리
const isChatOpen = ref(false);
const chatMessage = ref('');
const chatHistory = ref([
  { sender: 'bot', text: '안녕하세요! GlassLESS 가이드 봇입니다. 찾으시는 지역 명소가 있으신가요?' }
]);

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value;
};

const sendChat = () => {
  if (!chatMessage.value.trim()) return;
  
  // 유저 메시지 등록
  chatHistory.value.push({ sender: 'user', text: chatMessage.value });
  const userText = chatMessage.value;
  chatMessage.value = '';

  // 0.8초 뒤 챗봇 가짜 답변 응답 (공공데이터 연동 시 유용하게 쓸 영역)
  setTimeout(() => {
    chatHistory.value.push({ 
      sender: 'bot', 
      text: `'${userText}'에 관련한 정보를 준비 중입니다. 자세한 게시물 정보는 상단 '게시물 목록' 탭에서 즉시 등록 및 조회가 가능합니다!` 
    });
  }, 800);
};
</script>

<template>
  <div class="app-layout">
    <CommonHeader />
    <router-view />

    <button class="chatbot-floating-btn" @click="toggleChat" :class="{ active: isChatOpen }">
      <span v-if="!isChatOpen">💬</span>
      <span v-else>✕</span>
    </button>

    <div v-if="isChatOpen" class="chatbot-modal">
      <div class="chatbot-header">
        <h3>GlassLESS 가이드 봇</h3>
        <span>실시간 안내</span>
      </div>
      <div class="chatbot-body">
        <div 
          v-for="(msg, index) in chatHistory" 
          :key="index" 
          :class="['chat-bubble', msg.sender]"
        >
          <p>{{ msg.text }}</p>
        </div>
      </div>
      <div class="chatbot-footer">
        <input 
          v-model="chatMessage" 
          type="text" 
          placeholder="메시지를 입력하세요..." 
          @keyup.enter="sendChat"
        />
        <button @click="sendChat">전송</button>
      </div>
    </div>
  </div>
</template>

<style>
@import './assets/main.css';

/* 챗봇 플로팅 버튼 */
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
  box-shadow: 0 8px 24px rgba(224, 26, 79, 0.3);
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

/* 챗봇 모달 */
.chatbot-modal {
  position: fixed;
  bottom: 104px;
  right: 32px;
  width: 360px;
  height: 480px;
  background-color: white;
  border-radius: var(--radius-airbnb);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.12);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 999;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.chatbot-header {
  background-color: var(--color-airbnb-dark);
  color: white;
  padding: 18px;
}

.chatbot-header h3 {
  font-size: 1rem;
}

.chatbot-header span {
  font-size: 0.75rem;
  opacity: 0.8;
}

.chatbot-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background-color: #F8F9FA;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.88rem;
}

.chat-bubble.bot {
  background-color: white;
  align-self: flex-start;
  border: 1px solid var(--color-border);
  color: var(--color-airbnb-dark);
}

.chat-bubble.user {
  background-color: var(--color-airbnb-red);
  align-self: flex-end;
  color: white;
}

.chatbot-footer {
  padding: 12px;
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 8px;
}

.chatbot-footer input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  padding: 8px 16px;
  outline: none;
  font-size: 0.9rem;
}

.chatbot-footer button {
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
}
</style>