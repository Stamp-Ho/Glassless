<script setup>
import { ref, shallowRef, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router'; // 🔥 라우터 추가

const KAKAO_APP_KEY = 'b7b4f01e9203d5f62b2fb487cb0fdab5';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const router = useRouter(); // 🔥 인스턴스 생성
const SEARCH_RADIUS_KM = 10;

// 상태 관리
const status = ref('데이터를 불러오는 중입니다...');
const selectedCategory = ref('tourism');
const selectedRegion = ref('서울');

const mapContainer = ref(null);
const map = shallowRef(null);

const places = ref([]);
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
let fetchRequestToken = 0;
let centerFetchDebounceTimer = null;

const regionOptions = ['서울', '부산', '광주_전라권', '구미_경북권', '대전_충청권'];
const REGION_CENTER_MAP = {
  서울: { lat: 37.5665, lng: 126.9780 },
  부산: { lat: 35.1796, lng: 129.0756 },
  광주_전라권: { lat: 35.1595, lng: 126.8526 },
  구미_경북권: { lat: 36.1195, lng: 128.3446 },
  대전_충청권: { lat: 36.3504, lng: 127.3845 },
};

const CATEGORY_KIND_MAP = {
  관광지: 'tourism',
  레포츠: 'sports',
  문화시설: 'culture',
  쇼핑: 'shopping',
  숙박: 'stay',
  여행코스: 'course',
  축제공연행사: 'festival',
};

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

const CATEGORY_PARAM_MAP = {
  tourism: '관광지',
  sports: '레포츠',
  culture: '문화시설',
  shopping: '쇼핑',
  stay: '숙박',
  course: '여행코스',
  festival: '축제공연행사',
};

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

function normalizePlace(item) {
  const lat = Number(item.mapy);
  const lng = Number(item.mapx);
  const isValidCoord = lat > 30 && lat < 45 && lng > 120 && lng < 135;
  const rawAddress = item.address || '';
  const parsedDistrict = parseDistrict(rawAddress);
  const categoryLabel = item.category || '기타';
  const kind = CATEGORY_KIND_MAP[categoryLabel] || 'tourism';

  return {
    id: `${kind}-${item.id}`,
    contentId: item.id || '', // 🔥 URL 파라미터용 ID 보존
    title: item.name,
    address: rawAddress || '주소 정보 없음',
    district: parsedDistrict || '기타',
    lat: isValidCoord ? lat : null,
    lng: isValidCoord ? lng : null,
    kind,
    categoryLabel
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

function getCurrentMapCenter() {
  if (!map.value || !window.kakao || !window.kakao.maps) {
    const fallback = REGION_CENTER_MAP[selectedRegion.value] || REGION_CENTER_MAP['서울'];
    return { mapx: fallback.lng, mapy: fallback.lat };
  }

  const center = map.value.getCenter();
  return {
    mapx: Number(center.getLng()),
    mapy: Number(center.getLat()),
  };
}

function scheduleCenterBasedFetch(delayMs = 10) {
  if (centerFetchDebounceTimer) {
    clearTimeout(centerFetchDebounceTimer);
  }
  centerFetchDebounceTimer = window.setTimeout(() => {
    loadPlacesByFilters();
  }, delayMs);
}

function renderPlaces(force = false) {
  const filtered = filteredPlaces.value;
  resultCount.value = filtered.length;

  if (isRendering && !force) return;
  if (!map.value) return;

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
    const currentLevel = map.value.getLevel();
    
    // 🔥 [개선] 축소 레벨에 따라 성능 보호를 위해 화면에 그릴 마커 갯수를 유동적으로 조절합니다.
    // 지도가 아주 많이 축소(level 8 이상)되어도 무조건 최소 15개~30개의 핀은 화면에 유지되도록 합니다.
    let levelBasedLimit = MAX_VISIBLE_MARKERS;
    if (currentLevel >= 10) {
      levelBasedLimit = 2; // 초광역 축소
    } else if (currentLevel >= 8) {
      levelBasedLimit = 40; // 광역 축소
    }

    // 현재 지도 화면(Bounds) 안에 들어오는 장소 필터링
    const placesInViewport = getPlacesInBounds(filtered);
    const visiblePlaces = placesInViewport.slice(0, levelBasedLimit);
    
    const nextVisibleIds = new Set();
    const markerColorMap = {
      tourism: '#2e86de', sports: '#0ea5a4', culture: '#8b5cf6',
      shopping: '#f59e0b', stay: '#10b981', course: '#ef4444', festival: '#6366f1',
    };

    const pinnedPlace = filtered.find((place) => place.id === pinnedPlaceId);
    
    // 만약 화면 안에 들어오는 장소가 하나도 없다면? 
    // 유저가 길을 잃지 않도록 전체 검색 리스트 중 첫 번째 장소(혹은 고정된 장소) 하나라도 강제로 렌더링 목록에 포함시킵니다.
    let placesToRender = [];
    if (visiblePlaces.length === 0 && filtered.length > 0) {
      // 1순위: 고정(pinned)된 장소, 없으면 전체 리스트의 첫 번째 장소 선택
      const fallbackPlace = pinnedPlace || filtered[0];
      placesToRender = [fallbackPlace];
    } else {
      placesToRender = pinnedPlace 
        ? [pinnedPlace, ...visiblePlaces.filter((place) => place.id !== pinnedPlace.id)] 
        : visiblePlaces;
    }

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

      // 마커 클릭 이벤트 리스너
      window.kakao.maps.event.addListener(marker, 'click', () => {
        markers.forEach(m => m.setZIndex(0));
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
            <div style="font-size:12px; color:#555; line-height:1.5;">
              ${place.address}
            </div>
          </div>
        `;
        
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

    // 상태 메시지 업데이트
    if (currentLevel >= 8) {
      setStatus(`지도가 축소되어 주요 장소 ${placesToRender.length}개만 필터링하여 표시합니다.`);
    } else if (placesToRender.length) {
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
      scheduleCenterBasedFetch(200);
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

async function loadPlacesByFilters() {
  const currentToken = ++fetchRequestToken;
  try {
    setStatus('장소 데이터를 조회 중입니다...');
    const limit = 100;
    const categoryParam = CATEGORY_PARAM_MAP[selectedCategory.value] || null;
    const center = getCurrentMapCenter();

    const params = new URLSearchParams();
    params.set('region', selectedRegion.value);
    params.set('limit', String(limit));
    params.set('offset', '0');
    params.set('mapx', String(center.mapx));
    params.set('mapy', String(center.mapy));
    params.set('radius_km', String(SEARCH_RADIUS_KM));
    if (categoryParam) params.set('category', categoryParam);

    const response = await fetch(`${API_BASE_URL}/api/locations?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`locations api error: ${response.status}`);
    }

    const chunk = await response.json();
    if (currentToken !== fetchRequestToken) {
      return;
    }

    const loadedPlaces = Array.isArray(chunk) ? chunk.map((item) => normalizePlace(item)) : [];

    if (currentToken !== fetchRequestToken) {
      return;
    }

    places.value = loadedPlaces.filter((item) => item.lat !== null && item.lng !== null);

    renderPlaces();
    setStatus(`총 ${places.value.length}개 장소를 불러왔습니다.`);
  } catch (error) {
    if (currentToken !== fetchRequestToken) {
      return;
    }
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
    return categoryMatch;
  });
});

const displayedPlaces = computed(() => {
  return filteredPlaces.value.slice(0, MAX_VISIBLE_LIST_ITEMS);
});

watch([selectedCategory, selectedRegion], (newValues, oldValues) => {
  const [, newRegion] = newValues;
  const [, oldRegion] = oldValues || [null, null];

  renderVersion.value += 1;

  if (newRegion !== oldRegion && map.value) {
    const nextCenter = REGION_CENTER_MAP[newRegion] || REGION_CENTER_MAP['서울'];
    map.value.setCenter(new window.kakao.maps.LatLng(nextCenter.lat, nextCenter.lng));
    map.value.setLevel(7);
    return;
  }

  scheduleCenterBasedFetch(200);
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
    loadKakaoMapSdk();
  }, 100);
});
</script>

<template>
  <div class="map-search-layout">
    <aside class="search-sidebar">
      <div class="sidebar-header">
        <h2>{{ selectedRegion }} 여행지<br>지도 검색</h2>
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
          <select v-model="selectedRegion" class="filter-select">
            <option v-for="region in regionOptions" :key="region" :value="region">
              {{ region }}
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