<script setup>
import { ref } from "vue";

// 모바일 메뉴 열림/닫힘 상태 관리
const isMenuOpen = ref(false);

// Props 받기
defineProps({
  isDarkMode: Boolean,
});

// Emits 정의
const emit = defineEmits(["toggle-theme"]);

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

const closeMenu = () => {
  isMenuOpen.value = false;
};

const handleThemeToggle = () => {
  emit("toggle-theme");
};
</script>

<template>
  <header class="header">
    <div class="header-container">
      <h1
        class="logo"
        @click="
          () => {
            closeMenu();
            $router.push('/');
          }
        "
      >
        Glass<span>LESS</span>
      </h1>

      <nav class="nav-tabs">
        <router-link to="/" class="nav-item" active-class="active"
          >메인</router-link
        >
        <router-link to="/posts" class="nav-item" active-class="active"
          >게시물 목록</router-link
        >
        <router-link to="/map" class="nav-item" active-class="active"
          >지도 검색</router-link
        >
        <button
          class="theme-toggle-nav-btn"
          @click="handleThemeToggle"
          :title="isDarkMode ? '라이트 모드' : '다크 모드'"
        >
          <span v-if="isDarkMode">☀️</span>
          <span v-else>🌙</span>
        </button>
      </nav>

      <button
        class="hamburger-btn"
        @click="toggleMenu"
        :class="{ 'is-active': isMenuOpen }"
      >
        <span class="bar"></span>
        <span class="bar"></span>
        <span class="bar"></span>
      </button>

      <div class="header-right-spacer"></div>
    </div>

    <div
      class="mobile-menu-overlay"
      :class="{ 'is-open': isMenuOpen }"
      @click="closeMenu"
    >
      <nav class="mobile-nav-tabs" @click.stop>
        <router-link
          to="/"
          class="mobile-nav-item"
          active-class="active"
          @click="closeMenu"
          >메인</router-link
        >
        <router-link
          to="/posts"
          class="mobile-nav-item"
          active-class="active"
          @click="closeMenu"
          >게시물 목록</router-link
        >
        <router-link
          to="/map"
          class="mobile-nav-item"
          active-class="active"
          @click="closeMenu"
          >지도 검색</router-link
        >
        <button
          class="mobile-theme-toggle-btn"
          @click="handleThemeToggle"
          :title="isDarkMode ? '라이트 모드' : '다크 모드'"
        >
          <span v-if="isDarkMode">☀️ 라이트 모드</span>
          <span v-else>🌙 다크 모드</span>
        </button>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 16px 24px;
}

.logo {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--color-airbnb-red);
  cursor: pointer;
  letter-spacing: -0.8px;
  z-index: 1001; /* 햄버거 메뉴보다 상위 배치 */
  flex-shrink: 0;
  white-space: nowrap;
}

.logo span {
  font-weight: 400;
  color: var(--color-airbnb-dark);
}

.nav-tabs {
  display: flex;
  gap: 100px;
  flex: 1;
  justify-content: center;
}

.nav-item {
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-airbnb-gray);
  padding: 8px 4px;
  transition: color 0.2s;
  position: relative;
}

.nav-item:hover {
  color: var(--color-airbnb-dark);
}

.nav-item.active {
  color: var(--color-airbnb-red);
  font-weight: 700;
}

.nav-item.active::after {
  content: "";
  position: absolute;
  bottom: -18px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-airbnb-red);
}

.theme-toggle-nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 4px;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 12px;
}

.theme-toggle-nav-btn:hover {
  transform: scale(1.15);
}

.header-right-spacer {
  display: none;
}

/* =========================================================================
   🛠️ 모바일 햄버거 버튼 및 오버레이 메뉴 추가 스타일
   ========================================================================= */
.hamburger-btn {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  z-index: 1001;
  margin-left: auto;
}

.hamburger-btn .bar {
  width: 100%;
  height: 2px;
  background-color: var(--color-airbnb-dark);
  transition: all 0.3s ease;
}

/* 모바일 메뉴 전체 덮는 백드롭 레이어 */
.mobile-menu-overlay {
  position: fixed;
  top: 70px; /* 헤더 바로 밑에서 떨어지도록 */
  left: 0;
  width: 100vw;
  height: calc(100vh - 70px);
  background-color: rgba(0, 0, 0, 0.3);
  opacity: 0;
  visibility: hidden;
  transition:
    opacity 0.3s ease,
    visibility 0.3s ease;
  z-index: 999;
}

.mobile-menu-overlay.is-open {
  opacity: 1;
  visibility: visible;
}

/* 모바일 전용 네비게이션 서랍 */
.mobile-nav-tabs {
  position: absolute;
  top: 0;
  right: -260px;
  width: 260px;
  height: 100%;
  background-color: #ffffff;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  padding: 24px;
  gap: 16px;
  box-sizing: border-box;
  transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.mobile-menu-overlay.is-open .mobile-nav-tabs {
  right: 0;
}

.mobile-nav-item {
  text-decoration: none;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-airbnb-dark);
  padding: 12px 8px;
  border-bottom: 1px solid var(--color-border);
}

.mobile-nav-item.active {
  color: var(--color-airbnb-red);
  font-weight: 700;
}

.mobile-theme-toggle-btn {
  background: none;
  border: 1px solid var(--color-border);
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  padding: 12px 8px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  color: var(--color-airbnb-gray);
  transition: all 0.2s;
}

.mobile-theme-toggle-btn:hover {
  color: var(--color-airbnb-dark);
}

/* 🚨 1200px 이하에서 글자 밀림 시 해버거 버튼으로 변경 */
@media (max-width: 1200px) {
  .nav-tabs {
    display: none; /* 기존 데스크톱 메뉴 가리기 */
  }
  .hamburger-btn {
    display: flex; /* 햄버거 토글 버튼 노출 */
  }

  /* 클릭 애니메이션 효과 (X 표시 변환) */
  .hamburger-btn.is-active .bar:nth-child(1) {
    transform: translateY(8px) rotate(45deg);
  }
  .hamburger-btn.is-active .bar:nth-child(2) {
    opacity: 0;
  }
  .hamburger-btn.is-active .bar:nth-child(3) {
    transform: translateY(-8px) rotate(-45deg);
  }
}
</style>
