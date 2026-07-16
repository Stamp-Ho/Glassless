<script setup>
import { ref } from "vue";

const showToast = ref(false);

const copyLinkToClipboard = async () => {
  try {
    // 현재 접속 중인 웹페이지의 전체 URL 주소를 가져옴
    const currentUrl = window.location.href;

    // 클립보드에 복사 수행
    await navigator.clipboard.writeText(currentUrl);

    // 복사 완료 토스트 알림 띄우기
    showToast.value = true;
    setTimeout(() => {
      showToast.value = false;
    }, 2000);
  } catch (err) {
    console.error("링크 복사 실패:", err);
    alert("링크 복사에 실패했습니다. 주소창의 링크를 직접 복사해주세요.");
  }
};
</script>

<template>
  <div class="share-container">
    <button class="btn-share" @click="copyLinkToClipboard">
      <span class="icon">🔗</span> 링크 복사하여 공유하기
    </button>

    <!-- 복사 완료 안내 토스트 팝업 -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        📋 링크가 클립보드에 복사되었습니다!
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.share-container {
  position: relative;
  display: inline-block;
}

.btn-share {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #f5f6fa;
  color: var(--color-airbnb-dark);
  border: 1px solid var(--color-border);
  padding: 10px 16px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  transition:
    background-color 0.2s,
    transform 0.1s;
}

.btn-share:hover {
  background-color: #ebebeb;
}

.btn-share:active {
  transform: scale(0.98);
}

.toast-popup {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(47, 54, 64, 0.95);
  color: white;
  padding: 12px 24px;
  border-radius: 30px;
  font-size: 0.88rem;
  font-weight: 700;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  z-index: 2000;
}

/* 토스트 애니메이션 */
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s,
    transform 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}
</style>
