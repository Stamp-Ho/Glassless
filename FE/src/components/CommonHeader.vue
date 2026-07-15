<!-- src/components/CommonHeader.vue -->
<template>
  <header class="header">
    <div class="header-container">
      <!-- 서비스 이름 (GlassLESS - 더 단단하고 세련된 굵기로 수정) -->
      <h1 class="logo" @click="$router.push('/')">Glass<span>LESS</span></h1>

      <!-- 정돈된 중앙 네비게이션 바 -->
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
      </nav>

      <!-- 우측 여백 보정용 스페이서 -->
      <div class="header-right-spacer"></div>
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
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

/* 로고 글씨체를 더 굵고 직관적으로 개선 */
.logo {
  font-size: 1.6rem;
  font-weight: 800; /* 존재감 있는 볼드체 */
  color: var(--color-airbnb-red);
  cursor: pointer;
  letter-spacing: -0.8px;
}

.logo span {
  font-weight: 400; /* LESS 부분도 적당히 균형 잡힌 두께로 조절 */
  color: var(--color-airbnb-dark);
}

.nav-tabs {
  display: flex;
  gap: 32px;
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

/* 선택된 메뉴의 글자 색상을 시그니처 레드로 변경 */
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
  background-color: var(--color-airbnb-red); /* 하단 바 색상도 레드로 통일 */
}

.header-right-spacer {
  width: 120px;
}

@media (max-width: 768px) {
  .header-right-spacer {
    display: none;
  }
}
</style>
