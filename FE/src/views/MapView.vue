<template>
  <div class="map-container">
    <div class="map-placeholder">
      <h2>🗺️ 지도 영역</h2>
      <p>여기에 카카오맵, 구글맵 혹은 네이버 지도 API를 활용해 <br>지역별 공공데이터 정보를 핀(Pin) 형태로 시각화할 수 있습니다.</p>
    </div>
  </div>
</template>

<style scoped>
.map-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 24px;
}
.map-placeholder {
  height: 500px;
  background-color: #F7F7F7;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-airbnb);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  gap: 16px;
  color: var(--color-airbnb-gray);
}
</style>