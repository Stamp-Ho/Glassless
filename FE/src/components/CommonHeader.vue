<template>
  <header class="header">
    <div class="header-container">
      <h1 class="logo" @click="$router.push('/')">Glass<span>LESS</span></h1>
      
      <nav class="nav-tabs">
        <router-link to="/" class="nav-item" active-class="active">명소 검색</router-link>
        <router-link to="/posts" class="nav-item" active-class="active">게시물 보기</router-link>
        <router-link to="/map" class="nav-item" active-class="active">지도</router-link>
      </nav>
      
      <div class="user-menu">
        <span class="menu-item">호스트 되기</span>
        <div class="profile-icon">👤</div>
      </div>
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
  padding: 20px 24px;
}

.logo {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--color-airbnb-red);
  cursor: pointer;
  letter-spacing: -1px;
}

.logo span {
  color: var(--color-airbnb-dark);
}

/* 네비게이션 바 디자인 */
.nav-tabs {
  display: flex;
  gap: 32px;
}

.nav-item {
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-airbnb-gray);
  padding: 8px 4px;
  transition: color 0.2s;
  position: relative;
}

.nav-item:hover {
  color: var(--color-airbnb-dark);
}

/* 에어비앤비 스타일 밑줄 활성화 */
.nav-item.active {
  color: var(--color-airbnb-dark);
  font-weight: 600;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-airbnb-dark);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-item {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-airbnb-dark);
  cursor: pointer;
}

.profile-icon {
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  cursor: pointer;
}
</style>