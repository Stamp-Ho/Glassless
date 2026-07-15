<script setup>
import { ref, shallowRef, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router'; // 🔥 라우터 추가

const KAKAO_APP_KEY = 'b7b4f01e9203d5f62b2fb487cb0fdab5';
const router = useRouter(); // 🔥 인스턴스 생성

// 상태 관리
const status = ref('데이터를 불러오는 중입니다...');
const selectedCategory = ref('all');
const selectedDistrict = ref('all');

const mapContainer = ref(null);
const map = shallowRef(null);

const places = ref([]);
const districts = ref([]);
const resultCount = ref(0);
const mapMode = ref('fallback');
const renderVersion = ref(0);

// 카카오맵 마커 관련 상태
let markers = [];
const markerById = {};
let infoWindow = null;

const MAX_VISIBLE_MARKERS = 150;
const MAX_VISIBLE_LIST_ITEMS = 120;
let renderToken = 0;
let mapBounds = null;
let isRendering = false;
let mapInitAttempted = false;
let pinnedPlaceId = null;

const dataSources = [
  { file: '/서울_관광지.json', kind: 'tourism', label: '관광지' },
  { file: '/서울_레포츠.json', kind: 'sports', label: '레포츠' },
  { file: '/서울_문화시설.json', kind: 'culture', label: '문화시설' },
  { file: '/서울_쇼핑.json', kind: 'shopping', label: '쇼핑' },
  { file: '/서울_숙박.json', kind: 'stay', label: '숙박' },
  { file: '/서울_여행코스.json', kind: 'course', label: '여행코스' },
  { file: '/서울_축제공연행사.json', kind: 'festival', label: '축제공연행사' },
];

const categories = [
  { value: 'all', label: '전체' },
  { value: 'tourism', label: '관광지' },
  { value: 'sports', label: '레포츠' },
  { value: 'culture', label: '문화시설' },
  { value: 'shopping', label: '쇼핑' },
  { value: 'stay', label: '숙박' },
  { value: 'course', label: '여행코스' },
  { value: 'festival', label: '축제공연행사' },
];

function setStatus(message) {
  status.value = message;
}

function parseDistrict(address) {
  if (!address || typeof address !== 'string') return null;
  const match1 = address.match(/(?:서울|서울시|서울특별시)\s*([가-힣]+구)/);
  if (match1) return match1[1];
  const match2 = address.match(/([가-힣]{2,4}구)\b/);
  if (match2) return match2[1];
  return null;
}

function normalizePlace(item, kind, label) {
  const lat = Number(item.mapy);
  const lng = Number(item.mapx);
  const isValidCoord = lat > 30 && lat < 45 && lng > 120 && lng < 135;
  const rawAddress = item.addr1 || item.addr2 || '';
  const parsedDistrict = parseDistrict(rawAddress);

  return {
    id: `${kind}-${item.contentid || item.title}`,
    contentId: item.contentid || '', // 🔥 URL 파라미터용 ID 보존
    title: item.title,
    address: rawAddress || '주소 정보 없음',
    district: parsedDistrict || '기타',
    lat: isValidCoord ? lat : null,
    lng: isValidCoord ? lng : null,
    kind,
    categoryLabel: label
  };
}

function createMarkerImage(color) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="44" viewBox="0 0 32 44">
      <path fill="${color}" d="M16 0C7.2 0 0 7.2 0 16c0 9.6 16 28 16 28s16-18.4 16-28C32 7.2 24.8 0 16 0z"/>
      <circle cx="16" cy="16" r="8" fill="#fff"/>
    </svg>`;
  return new window.kakao.maps.MarkerImage(
    `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
    new window.kakao.maps.Size(32, 44),
    { offset: new window.kakao.maps.Point(16, 44) }
  );
}

function hideAllMarkers() {
  markers.forEach(marker => marker.setMap(null));
}

function clearMarkers() {
  hideAllMarkers();
  markers = [];
  for (const key in markerById) {
    delete markerById[key];
  }
}

function getPlacesInBounds(filteredPlacesList) {
  if (!map.value || !mapBounds) return [];
  const sw = mapBounds.getSouthWest();
  const ne = mapBounds.getNorthEast();
  return filteredPlacesList.filter((place) => {
    const lat = Number(place.lat);
    const lng = Number(place.lng);
    return lat >= sw.getLat() && lat <= ne.getLat() && lng >= sw.getLng() && lng <= ne.getLng();
  });
}

function renderPlaces(force = false) {
  const filtered = filteredPlaces.value;
  resultCount.value = filtered.length;

  if (isRendering && !force) return;
  if (!map.value) return;

  if (selectedDistrict.value === 'all' && map.value.getLevel() >= 8) {
    clearMarkers();
    setStatus('지도를 조금 더 확대해 주세요. (너무 많은 장소가 있습니다)');
    isRendering = false;
    return;
  }

  isRendering = true;
  const token = ++renderToken;

  if (force) clearMarkers();

  if (!filtered.length) {
    isRendering = false;
    setStatus('표시할 장소가 없습니다. 다른 필터를 선택해 보세요.');
    return;
  }

  if (!window.kakao || !window.kakao.maps || !mapContainer.value) {
    isRendering = false;
    return;
  }

  try {
    const visiblePlaces = getPlacesInBounds(filtered).slice(0, MAX_VISIBLE_MARKERS);
    const nextVisibleIds = new Set();
    const markerColorMap = {
      tourism: '#2e86de', sports: '#0ea5a4', culture: '#8b5cf6',
      shopping: '#f59e0b', stay: '#10b981', course: '#ef4444', festival: '#6366f1',
    };

    const pinnedPlace = filtered.find((place) => place.id === pinnedPlaceId);
    const placesToRender = pinnedPlace 
      ? [pinnedPlace, ...visiblePlaces.filter((place) => place.id !== pinnedPlace.id)] 
      : visiblePlaces;

    placesToRender.forEach((place) => {
      if (token !== renderToken || !map.value) return;

      const existingMarker = markerById[place.id];
      if (existingMarker) {
        if (!existingMarker.getMap()) {
          existingMarker.setMap(map.value);
        }
        nextVisibleIds.add(place.id);
        return;
      }

      const position = new window.kakao.maps.LatLng(place.lat, place.lng);
      const marker = new window.kakao.maps.Marker({
        position, 
        map: map.value, 
        title: place.title,
        image: createMarkerImage(markerColorMap[place.kind] || '#2e86de'),
      });

      // 🔥 마커 클릭 이벤트 리스너
      window.kakao.maps.event.addListener(marker, 'click', () => {
        // 1. 모든 핀의 zIndex를 바닥(0)으로 초기화
        markers.forEach(m => m.setZIndex(0));
        
        // 2. 현재 클릭한 핀만 최상단으로 끌어올림
        marker.setZIndex(9999);

        // 3. 기존에 열려있던 정보 박스 닫기
        if (infoWindow) infoWindow.close();
        
        // 4. 정보 박스 내용 구성 (크기 고정 및 텍스트 클릭 시 라우터 연동)
        const contentHtml = `
          <div style="padding:14px; width:220px; box-sizing:border-box; font-family:sans-serif; white-space:normal; word-break:keep-all;">
            <div 
              style="font-size:15px; font-weight:bold; color:#1a73e8; cursor:pointer; text-decoration:underline; margin-bottom:8px; line-height:1.4;" 
              onclick="window.goToPost('${place.contentId}')"
            >
              ${place.title}
            </div>
            <div style="font-size:12px; color:#555; line-height:1.5;">
              ${place.address}
            </div>
          </div>
        `;
        
        // 5. 정보 박스 생성 및 띄우기 (정보 박스 자체도 최상단 레이어로 설정)
        infoWindow = new window.kakao.maps.InfoWindow({ 
          content: contentHtml,
          zIndex: 10000 
        });
        
        infoWindow.open(map.value, marker);
      });

      markerById[place.id] = marker;
      markers.push(marker);
      nextVisibleIds.add(place.id);
    });

    // 화면 밖으로 벗어난 마커 지우기
    for (const id in markerById) {
      if (!nextVisibleIds.has(id)) {
        const marker = markerById[id];
        if (marker) marker.setMap(null);
        delete markerById[id];
        markers = markers.filter(m => m !== marker);
      }
    }

    if (placesToRender.length) {
      mapMode.value = 'kakao';
      setStatus(`현재 화면 기준 ${placesToRender.length}개 장소를 표시합니다.`);
    } else {
      setStatus('현재 화면 범위 안에 표시할 장소가 없습니다.');
    }
    
    isRendering = false;
  } catch (error) {
    isRendering = false;
    mapMode.value = 'kakao';
    setStatus('지도 업데이트 중 문제가 발생했습니다.');
  }
}

//
function initMap() {
  if (mapInitAttempted && map.value) return;
  mapInitAttempted = true;

  const container = mapContainer.value;
  if (!container) {
    window.setTimeout(() => initMap(), 100);
    return;
  }

  try {
    container.innerHTML = '';
    const options = {
      center: new window.kakao.maps.LatLng(37.5665, 126.9780),
      level: 7, 
    };
    map.value = new window.kakao.maps.Map(container, options);
    mapMode.value = 'kakao';

    mapBounds = map.value.getBounds();

    let idleTimeout = null;
    window.kakao.maps.event.addListener(map.value, 'dragstart', hideAllMarkers);
    window.kakao.maps.event.addListener(map.value, 'zoom_start', hideAllMarkers);
    
    window.kakao.maps.event.addListener(map.value, 'idle', () => {
      mapBounds = map.value.getBounds();
      if (idleTimeout) clearTimeout(idleTimeout);
      idleTimeout = setTimeout(() => { renderPlaces(false); }, 200);
    });

    renderPlaces(true);
  } catch (error) {
    mapMode.value = 'kakao';
  }
}

function loadKakaoMapSdk() {
  if (!KAKAO_APP_KEY || KAKAO_APP_KEY.includes('YOUR')) return;
  if (window.kakao && window.kakao.maps) {
    window.kakao.maps.load(() => initMap());
    return;
  }
  const script = document.createElement('script');
  script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_APP_KEY}&autoload=false&libraries=services`;
  script.async = true;
  script.onload = () => {
    if (window.kakao && window.kakao.maps) window.kakao.maps.load(() => initMap());
    else mapMode.value = 'fallback';
  };
  document.head.appendChild(script);
}

async function loadPlaces() {
  try {
    const loadedPlaces = [];
    for (const source of dataSources) {
      try {
        const response = await fetch(source.file);
        if (!response.ok) continue;
        const data = await response.json();
        const sourcePlaces = (data.items || []).map((item) => normalizePlace(item, source.kind, source.label));
        loadedPlaces.push(...sourcePlaces);
      } catch (error) { }
    }

    places.value = loadedPlaces.filter((item) => item.lat !== null && item.lng !== null);
    const nextDistricts = [...new Set(places.value.map((item) => item.district))].filter(d => d !== '기타').sort();
    districts.value = nextDistricts;

    if (selectedDistrict.value !== 'all' && !nextDistricts.includes(selectedDistrict.value)) {
      selectedDistrict.value = 'all';
    }

    renderPlaces();
    setStatus(`총 ${places.value.length}개 장소를 불러왔습니다.`);
  } catch (error) {
    setStatus('장소 데이터를 불러오지 못했습니다.');
  }
}

function focusPlace(place) {
  if (!map.value) return;

  pinnedPlaceId = place.id;
  let marker = markerById[place.id];

  if (!marker) {
    const position = new window.kakao.maps.LatLng(place.lat, place.lng);
    marker = new window.kakao.maps.Marker({
      position, map: map.value, title: place.title,
      image: createMarkerImage('#ef4444'),
    });
    markerById[place.id] = marker;
    markers.push(marker);
  }

  map.value.setCenter(new window.kakao.maps.LatLng(place.lat, place.lng));
  map.value.setLevel(4);

  // 🔥 1. 모든 마커의 zIndex 초기화
  markers.forEach(m => m.setZIndex(0));
  // 🔥 2. 선택된 마커를 맨 앞으로 가져오기
  marker.setZIndex(9999);

  if (infoWindow) infoWindow.close();
  
  const contentHtml = `
    <div style="padding:14px; width:220px; box-sizing:border-box; font-family:sans-serif; white-space:normal; word-break:keep-all;">
      <div 
        style="font-size:15px; font-weight:bold; color:#1a73e8; cursor:pointer; text-decoration:underline; margin-bottom:8px; line-height:1.4;" 
        onclick="window.goToPost('${place.contentId}')"
      >
        ${place.title}
      </div>
      <div style="font-size:12px; color:#555; line-height:1.5;">${place.address}</div>
    </div>
  `;
  
  // 🔥 3. 정보 박스(InfoWindow)도 최상단 설정
  infoWindow = new window.kakao.maps.InfoWindow({ 
    content: contentHtml,
    zIndex: 10000
  });
  infoWindow.open(map.value, marker);
  
  window.setTimeout(() => { if (map.value) map.value.relayout(); }, 0);
}

const filteredPlaces = computed(() => {
  return places.value.filter((place) => {
    const categoryMatch = selectedCategory.value === 'all' || place.kind === selectedCategory.value;
    const districtMatch = selectedDistrict.value === 'all' || place.district === selectedDistrict.value;
    return categoryMatch && districtMatch;
  });
});

const displayedPlaces = computed(() => {
  return filteredPlaces.value.slice(0, MAX_VISIBLE_LIST_ITEMS);
});

watch([selectedCategory, selectedDistrict], (newValues, oldValues) => {
  const [newCat, newDist] = newValues;
  const [oldCat, oldDist] = oldValues || [null, null];

  renderVersion.value += 1;

  if (newDist !== oldDist && map.value) {
    if (newDist === 'all') {
      map.value.setCenter(new window.kakao.maps.LatLng(37.5665, 126.9780));
      map.value.setLevel(7);
      setTimeout(() => { mapBounds = map.value.getBounds(); renderPlaces(true); }, 50);
    } else {
      if (window.kakao && window.kakao.maps && window.kakao.maps.services) {
        const geocoder = new window.kakao.maps.services.Geocoder();
        geocoder.addressSearch(`서울특별시 ${newDist}`, (result, status) => {
          if (status === window.kakao.maps.services.Status.OK) {
            map.value.setCenter(new window.kakao.maps.LatLng(result[0].y, result[0].x));
            map.value.setLevel(5); 
          } else {
            const districtPlaces = places.value.filter(p => p.district === newDist && p.lat && p.lng);
            if (districtPlaces.length > 0) {
              const bounds = new window.kakao.maps.LatLngBounds();
              districtPlaces.forEach(p => bounds.extend(new window.kakao.maps.LatLng(p.lat, p.lng)));
              map.value.setBounds(bounds);
            }
          }
          setTimeout(() => { mapBounds = map.value.getBounds(); renderPlaces(true); }, 100);
        });
      }
    }
  }
});

onMounted(() => {
  // 🔥 전역 스코프에 브릿지 함수 등록 (인포윈도우의 onclick 속성에서 호출됨)
  window.goToPost = (contentId) => {
    if (contentId) {
      router.push(`/posts?location_id=${contentId}`);
    } else {
      // contentId가 없는 예외 케이스 처리 (알림 띄우기 등)
      alert('이 장소와 연결된 게시물 정보가 없습니다.');
    }
  };

  window.setTimeout(() => {
    loadPlaces();
    loadKakaoMapSdk();
  }, 100);
});
</script>

<template>
  <div class="map-search-layout">
    <aside class="search-sidebar">
      <div class="sidebar-header">
        <h2>서울 여행지<br>지도 검색</h2>
        <p>{{ status }}</p>
      </div>

      <div class="filter-group">
        <div class="filter-item">
          <label class="filter-label">카테고리</label>
          <select v-model="selectedCategory" class="filter-select">
            <option v-for="category in categories" :key="category.value" :value="category.value">
              {{ category.label }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label class="filter-label">권역</label>
          <select v-model="selectedDistrict" class="filter-select">
            <option value="all">전체</option>
            <option v-for="district in districts" :key="district" :value="district">
              {{ district }}
            </option>
          </select>
        </div>
      </div>

      <div class="list-section">
        <div class="list-header">
          <h3>표시된 장소</h3>
          <span class="result-count">{{ resultCount }}개</span>
        </div>
        <ul v-if="displayedPlaces.length" class="place-list">
          <li 
            v-for="place in displayedPlaces" 
            :key="place.id"
            class="place-item"
            @click="focusPlace(place)"
          >
            <div class="item-title">{{ place.title }}</div>
            <div class="item-category">{{ place.categoryLabel }}</div>
            <div class="item-address">{{ place.address }}</div>
          </li>
        </ul>
        <div v-else class="empty-state">표시할 장소가 없습니다. 다른 필터를 선택해 보세요.</div>
      </div>
    </aside>

    <main class="map-viewport">
      <div ref="mapContainer" class="map-container"></div>
    </main>
  </div>
</template>

<style scoped>
.map-search-layout {
  display: flex;
  height: calc(100vh - 73px);
  overflow: hidden;
}

.search-sidebar {
  width: 380px;
  background-color: white;
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: 32px 24px;
  box-sizing: border-box;
  z-index: 10;
  overflow-y: auto;
}

.sidebar-header h2 {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.3;
  margin-bottom: 8px;
  color: var(--color-airbnb-dark);
}

.sidebar-header p {
  font-size: 0.75rem;
  color: var(--color-airbnb-gray);
  line-height: 1.4;
  min-height: 20px;
}

.filter-group {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-airbnb-dark);
  letter-spacing: 0.5px;
}

.filter-select {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
  background-color: #FAFAFA;
  cursor: pointer;
}

.filter-select:focus {
  border-color: var(--color-airbnb-red);
  background-color: white;
}

.list-section {
  margin-top: 28px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 12px;
}

.list-header h3 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin: 0;
}

.result-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-airbnb-red);
}

.place-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.place-item {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background-color: white;
}

.place-item:hover {
  border-color: var(--color-airbnb-red);
  background-color: #FFF0F2;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.item-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-airbnb-dark);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-category {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-airbnb-red);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.item-address {
  font-size: 0.75rem;
  color: var(--color-airbnb-gray);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: var(--color-airbnb-gray);
  font-size: 0.9rem;
  text-align: center;
}

.map-viewport {
  flex: 1;
  height: 100%;
  background-color: #E3ECE9;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
}

.highlight {
  display: inline-block;
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--color-airbnb-red);
  font-weight: 600;
}

/* 모바일/태블릿 반응형 */
@media (max-width: 768px) {
  .map-search-layout {
    flex-direction: column;
    height: auto;
    overflow: visible;
  }
  
  .search-sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
  
  .map-viewport {
    height: 400px;
  }
}
</style>