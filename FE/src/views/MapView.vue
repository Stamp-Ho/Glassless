<script setup>
import { ref, shallowRef, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router'; 

const KAKAO_APP_KEY = import.meta.env.VITE_KAKAO_APP_KEY || '';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://glassless-be.onrender.com';
const router = useRouter(); 
const SEARCH_RADIUS_KM = 5;

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

// 🔥 길찾기(경로) 관련 상태
const routeDeparture = ref(null);
const routeArrival = ref(null);

// WCONGNAMUL 좌표 보관용 (카카오맵 웹 자동 길찾기 필수값)
const routeCoords = ref({
  depX: null, depY: null,
  arrX: null, arrY: null
});

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
    contentId: item.id || '',
    title: item.name,
    address: rawAddress || '주소 정보 없음',
    district: parsedDistrict || '기타',
    lat: isValidCoord ? lat : null,
    lng: isValidCoord ? lng : null,
    kind,
    categoryLabel,
    rating_avg: item.rating_avg ?? (item.rating && item.rating.avg) ?? item.rating_avg_value ?? null,
    rating_count: item.rating_count ?? (item.rating && item.rating.count) ?? item.rating_count_value ?? 0,
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
  return { mapx: Number(center.getLng()), mapy: Number(center.getLat()) };
}

function scheduleCenterBasedFetch(delayMs = 10) {
  if (centerFetchDebounceTimer) clearTimeout(centerFetchDebounceTimer);
  centerFetchDebounceTimer = window.setTimeout(() => { loadPlacesByFilters(); }, delayMs);
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
    let levelBasedLimit = MAX_VISIBLE_MARKERS;
    if (currentLevel >= 10) levelBasedLimit = 2;
    else if (currentLevel >= 8) levelBasedLimit = 40;

    const placesInViewport = getPlacesInBounds(filtered);
    const visiblePlaces = placesInViewport.slice(0, levelBasedLimit);
    
    const nextVisibleIds = new Set();
    const markerColorMap = {
      tourism: '#2e86de', sports: '#0ea5a4', culture: '#8b5cf6',
      shopping: '#f59e0b', stay: '#10b981', course: '#ef4444', festival: '#6366f1',
    };

    const pinnedPlace = filtered.find((place) => place.id === pinnedPlaceId);
    
    let placesToRender = [];
    if (visiblePlaces.length === 0 && filtered.length > 0) {
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
        if (!existingMarker.getMap()) existingMarker.setMap(map.value);
        nextVisibleIds.add(place.id);
        return;
      }

      const position = new window.kakao.maps.LatLng(place.lat, place.lng);
      const marker = new window.kakao.maps.Marker({
        position, map: map.value, title: place.title,
        image: createMarkerImage(markerColorMap[place.kind] || '#2e86de'),
      });

      window.kakao.maps.event.addListener(marker, 'click', async () => {
        markers.forEach(m => m.setZIndex(0));
        marker.setZIndex(9999);
        if (infoWindow) infoWindow.close();

        infoWindow = new window.kakao.maps.InfoWindow({ 
          content: `<div style="padding:14px; width:220px; box-sizing:border-box; font-family:sans-serif;">로딩 중...</div>`,
          zIndex: 10000 
        });
        infoWindow.open(map.value, marker);

        try {
          const resp = await fetch(`${API_BASE_URL}/api/locations/${encodeURIComponent(place.contentId)}`);
          let detail = null;
          if (resp.ok) detail = await resp.json();
          const avg = detail?.rating_avg ?? place.rating_avg ?? null;
          const count = detail?.rating_count ?? place.rating_count ?? 0;

          let starsHtml = '';
          if (avg) {
            const rounded = Math.round(Number(avg));
            let s = '';
            for (let i = 1; i <= 5; i++) {
              s += `<span style=\"color:${i<=rounded ? '#FFD54A' : '#dcdcdc'};font-size:14px;margin-right:2px;\">★</span>`;
            }
            starsHtml = `<div style=\"margin:6px 0; display:flex; align-items:center; gap:6px;\">${s}<small style=\"color:#666; font-size:12px;\">${Number(avg).toFixed(1)} (${count})</small></div>`;
          }

          const contentHtml = `
            <div style="padding:14px; width:260px; box-sizing:border-box; font-family:sans-serif; white-space:normal; word-break:keep-all;">
              <div 
                style="font-size:15px; font-weight:bold; color:#1a73e8; cursor:pointer; text-decoration:underline; margin-bottom:8px; line-height:1.4;" 
                onclick="window.goToPost('${place.contentId}')"
              >
                ${place.title}
              </div>
              <div style="font-size:12px; color:#555; line-height:1.5;">${place.address}</div>
              ${starsHtml}
              <div style="margin-top:12px; display:flex; gap:6px;">
                <button onclick="window.setDepartureFromMap('${place.id}')" style="flex:1; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; padding:6px; font-size:12px; font-weight:bold; color:#475569; cursor:pointer;">출발지로 설정</button>
                <button onclick="window.setArrivalFromMap('${place.id}')" style="flex:1; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; padding:6px; font-size:12px; font-weight:bold; color:#475569; cursor:pointer;">도착지로 설정</button>
              </div>
            </div>
          `;

          infoWindow.setContent(contentHtml);
        } catch (e) {
          console.error('fetch location detail failed:', e);
        }
      });

      markerById[place.id] = marker;
      markers.push(marker);
      nextVisibleIds.add(place.id);
    });

    for (const id in markerById) {
      if (!nextVisibleIds.has(id)) {
        const marker = markerById[id];
        if (marker) marker.setMap(null);
        delete markerById[id];
        markers = markers.filter(m => m !== marker);
      }
    }

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
    const initialCenter = REGION_CENTER_MAP[selectedRegion.value] || REGION_CENTER_MAP['서울'];
    
    const options = {
      center: new window.kakao.maps.LatLng(initialCenter.lat, initialCenter.lng),
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

    loadPlacesByFilters();
  } catch (error) {
    console.error('지도 초기화 실패:', error);
    mapMode.value = 'fallback';
    loadPlacesByFilters();
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
    else {
      mapMode.value = 'fallback';
      loadPlacesByFilters(); 
    }
  };
  document.head.appendChild(script);
}

async function loadPlacesByFilters() {
  const currentToken = ++fetchRequestToken;
  try {
    setStatus('장소 데이터를 조회 중입니다...');
    const center = getCurrentMapCenter();
    
    const createParams = (categoryName, limitValue, offset) => {
      const params = new URLSearchParams();
      params.set('region', selectedRegion.value);
      params.set('limit', String(limitValue));
      params.set('offset', String(offset));
      params.set('mapx', String(center.mapx));
      params.set('mapy', String(center.mapy));
      params.set('radius_km', String(SEARCH_RADIUS_KM));
      if (categoryName) {
        params.set('category', categoryName);
      }
      return params.toString();
    };

    let rawPlaces = [];

    if (selectedCategory.value === 'all') {
      const targetCategories = ['관광지', '레포츠', '문화시설', '쇼핑', '여행코스', '숙박', '축제공연행사'];
      const fetchPromises = targetCategories.map(cat => 
        fetch(`${API_BASE_URL}/api/locations?${createParams(cat, 30)}`)
          .then(res => res.ok ? res.json() : [])
          .catch(() => []) 
      );
      const results = await Promise.all(fetchPromises);
      if (currentToken !== fetchRequestToken) return;
      rawPlaces = results.flat();
    } else {
      const categoryParam = CATEGORY_PARAM_MAP[selectedCategory.value] || null;
      const offsets = [0, 100];
      const fetchPromises = offsets.map(offset => 
        fetch(`${API_BASE_URL}/api/locations?${createParams(categoryParam, 100, offset)}`)
          .then(res => res.ok ? res.json() : [])
          .catch(() => [])
      );
      const results = await Promise.all(fetchPromises);
      if (currentToken !== fetchRequestToken) return;
      rawPlaces = results.flat();
    }

    if (currentToken !== fetchRequestToken) return;

    const normalized = Array.isArray(rawPlaces) 
      ? rawPlaces.map((item) => normalizePlace(item)) 
      : [];

    const uniqueMap = new Map();
    normalized.forEach(item => {
      if (item.lat !== null && item.lng !== null) {
        uniqueMap.set(item.id, item); 
      }
    });

    places.value = Array.from(uniqueMap.values());
    renderPlaces();
    setStatus(`총 ${places.value.length}개 장소를 불러왔습니다.`);
  } catch (error) {
    if (currentToken !== fetchRequestToken) return;
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

  markers.forEach(m => m.setZIndex(0));
  marker.setZIndex(9999);

  if (infoWindow) infoWindow.close();
  
  infoWindow = new window.kakao.maps.InfoWindow({ 
    content: `<div style="padding:14px; width:220px; box-sizing:border-box; font-family:sans-serif;">로딩 중...</div>`,
    zIndex: 10000
  });
  infoWindow.open(map.value, marker);

  (async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/locations/${encodeURIComponent(place.contentId)}`);
      const detail = resp.ok ? await resp.json() : null;
      const avg = detail?.rating_avg ?? place.rating_avg ?? null;
      const count = detail?.rating_count ?? place.rating_count ?? 0;
      let starsSection = '';
      if (avg) {
        const rounded = Math.round(Number(avg));
        let s = '';
        for (let i = 1; i <= 5; i++) {
          s += `<span style=\"color:${i<=rounded ? '#FFD54A' : '#dcdcdc'};font-size:14px;margin-right:2px;\">★</span>`;
        }
        starsSection = `<div style=\"margin:6px 0; display:flex; align-items:center; gap:6px;\">${s}<small style=\"color:#666; font-size:12px;\">${Number(avg).toFixed(1)} (${count})</small></div>`;
      }

      // 🔥 InfoWindow 내부 출발/도착 설정 버튼 
      const contentHtml = `
        <div style="padding:14px; width:260px; box-sizing:border-box; font-family:sans-serif; white-space:normal; word-break:keep-all;">
          <div 
            style="font-size:15px; font-weight:bold; color:#1a73e8; cursor:pointer; text-decoration:underline; margin-bottom:8px; line-height:1.4;" 
            onclick="window.goToPost('${place.contentId}')"
          >
            ${place.title}
          </div>
          <div style="font-size:12px; color:#555; line-height:1.5;">${place.address}</div>
          ${starsSection}
          <div style="margin-top:12px; display:flex; gap:6px;">
            <button onclick="window.setDepartureFromMap('${place.id}')" style="flex:1; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; padding:6px; font-size:12px; font-weight:bold; color:#475569; cursor:pointer;">출발지로 설정</button>
            <button onclick="window.setArrivalFromMap('${place.id}')" style="flex:1; background:#f1f5f9; border:1px solid #cbd5e1; border-radius:6px; padding:6px; font-size:12px; font-weight:bold; color:#475569; cursor:pointer;">도착지로 설정</button>
          </div>
        </div>
      `;
      infoWindow.setContent(contentHtml);
    } catch (e) {
      console.error('fetch detail for focusPlace failed', e);
    }
  })();
  
  window.setTimeout(() => { if (map.value) map.value.relayout(); }, 0);
}

// 🔥 WGS84 좌표를 WCONGNAMUL(카카오전용)로 변환 및 상태 저장 
function setDeparture(place) { 
  routeDeparture.value = place;
  routeCoords.value.depX = null;
  routeCoords.value.depY = null;
  
  if (window.kakao && window.kakao.maps && window.kakao.maps.services) {
    const geocoder = new window.kakao.maps.services.Geocoder();
    geocoder.transCoord(place.lng, place.lat, (res, status) => {
      if (status === window.kakao.maps.services.Status.OK) {
        routeCoords.value.depX = res[0].x;
        routeCoords.value.depY = res[0].y;
      }
    }, { input_coord: window.kakao.maps.services.Coords.WGS84, output_coord: window.kakao.maps.services.Coords.WCONGNAMUL });
  }
}

function setArrival(place) { 
  routeArrival.value = place; 
  routeCoords.value.arrX = null;
  routeCoords.value.arrY = null;

  if (window.kakao && window.kakao.maps && window.kakao.maps.services) {
    const geocoder = new window.kakao.maps.services.Geocoder();
    geocoder.transCoord(place.lng, place.lat, (res, status) => {
      if (status === window.kakao.maps.services.Status.OK) {
        routeCoords.value.arrX = res[0].x;
        routeCoords.value.arrY = res[0].y;
      }
    }, { input_coord: window.kakao.maps.services.Coords.WGS84, output_coord: window.kakao.maps.services.Coords.WCONGNAMUL });
  }
}

function clearDeparture() { 
  routeDeparture.value = null; 
  routeCoords.value.depX = null;
  routeCoords.value.depY = null;
}

function clearArrival() { 
  routeArrival.value = null; 
  routeCoords.value.arrX = null;
  routeCoords.value.arrY = null;
}

// 🔥 카카오맵 웹 브라우저 (PC/모바일 통합) 자동 경로 URL 생성
function openKakaoRoute() {
  if (!routeDeparture.value || !routeArrival.value) return;
  if (!routeCoords.value.depX || !routeCoords.value.arrX) {
    alert('좌표 변환이 진행 중입니다. 1~2초 뒤에 다시 시도해 주세요.');
    return;
  }
  
  const sName = encodeURIComponent(routeDeparture.value.title);
  const sX = routeCoords.value.depX;
  const sY = routeCoords.value.depY;
  
  const eName = encodeURIComponent(routeArrival.value.title);
  const eX = routeCoords.value.arrX;
  const eY = routeCoords.value.arrY;
  
  // WCONGNAMUL 좌표가 포함된 완벽한 카카오 길찾기 URL (자동 검색 수행됨)
  const url = `https://map.kakao.com/?sName=${sName}&sX=${sX}&sY=${sY}&eName=${eName}&eX=${eX}&eY=${eY}`;
  window.open(url, '_blank');
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
  window.goToPost = (contentId) => {
    if (contentId) router.push(`/posts?location_id=${contentId}`);
    else alert('이 장소와 연결된 게시물 정보가 없습니다.');
  };

  window.setDepartureFromMap = (id) => {
    const place = places.value.find(p => p.id === id);
    if (place) setDeparture(place);
  };

  window.setArrivalFromMap = (id) => {
    const place = places.value.find(p => p.id === id);
    if (place) setArrival(place);
  };

  loadKakaoMapSdk();
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

      <div class="route-panel">
        <div class="route-panel-header">
          <h3>길찾기</h3>
        </div>
        <div class="route-points">
          <div class="route-point">
            <span class="route-label dep">출발</span>
            <div class="route-value-box">
              <span v-if="routeDeparture" class="route-value">{{ routeDeparture.title }}</span>
              <span v-else class="route-placeholder">목록/지도에서 출발지를 선택하세요</span>
              <button v-if="routeDeparture" class="btn-clear-route" @click="clearDeparture">✕</button>
            </div>
          </div>
          <div class="route-point">
            <span class="route-label arr">도착</span>
            <div class="route-value-box">
              <span v-if="routeArrival" class="route-value">{{ routeArrival.title }}</span>
              <span v-else class="route-placeholder">목록/지도에서 도착지를 선택하세요</span>
              <button v-if="routeArrival" class="btn-clear-route" @click="clearArrival">✕</button>
            </div>
          </div>
        </div>
        <button 
          class="btn-find-route" 
          :disabled="!routeDeparture || !routeArrival || !routeCoords.depX || !routeCoords.arrX" 
          @click="openKakaoRoute"
        >
          카카오맵으로 경로 보기
        </button>
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
            <div class="item-rating">
              <span class="loc-stars">
                <span v-for="i in 5" :key="i" class="loc-star" :class="{ filled: i <= Math.round(place.rating_avg || 0) }">★</span>
              </span>
              <span class="rating-text">{{ place.rating_avg ? Number(place.rating_avg).toFixed(1) : '-' }} ({{ place.rating_count || 0 }})</span>
            </div>
            <div class="item-category">{{ place.categoryLabel }}</div>
            <div class="item-address">{{ place.address }}</div>
            
            <div class="item-route-actions">
              <button class="btn-set-route dep" @click.stop="setDeparture(place)">출발</button>
              <button class="btn-set-route arr" @click.stop="setArrival(place)">도착</button>
            </div>
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
  margin: 0;
}

.filter-group {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  padding: 10px 14px;
  font-size: 0.9rem;
  outline: none;
  background-color: #FAFAFA;
  cursor: pointer;
}

.filter-select:focus {
  border-color: var(--color-airbnb-red);
  background-color: white;
}

.route-panel {
  margin-top: 24px;
  background-color: #f7f9fc;
  border: 1px solid #e1e7f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.route-panel-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
}

.route-points {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-point {
  display: flex;
  align-items: center;
  gap: 10px;
}

.route-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.route-label.dep { background-color: #3b82f6; }
.route-label.arr { background-color: #ef4444; }

.route-value-box {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: white;
  border: 1px solid #e1e7f0;
  border-radius: 6px;
  padding: 6px 10px;
  min-height: 32px;
}

.route-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-airbnb-dark);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 170px;
}

.route-placeholder {
  font-size: 0.8rem;
  color: #9ca3af;
}

.btn-clear-route {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  padding: 0 4px;
}

.btn-clear-route:hover { color: #4b5563; }

.btn-find-route {
  background-color: var(--color-airbnb-dark);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-find-route:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
}

.btn-find-route:not(:disabled):hover {
  opacity: 0.9;
}

.list-section {
  margin-top: 24px;
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
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background-color: white;
  display: flex;
  flex-direction: column;
}

.place-item:hover {
  border-color: var(--color-airbnb-red);
  background-color: #FFF0F2;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.item-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-rating { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.loc-stars { display:flex; gap:4px; }
.loc-star { color: #dcdcdc; font-size:0.9rem; }
.loc-star.filled { color: #FFD54A; }
.rating-text { color: var(--color-airbnb-gray); font-size:0.8rem; }

.item-category {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-airbnb-red);
  margin-bottom: 4px;
  text-transform: uppercase;
}

.item-address {
  font-size: 0.75rem;
  color: var(--color-airbnb-gray);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-route-actions {
  margin-top: 10px;
  display: flex;
  gap: 6px;
}

.btn-set-route {
  flex: 1;
  background-color: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 6px 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-set-route.dep:hover { background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8; }
.btn-set-route.arr:hover { background-color: #fef2f2; border-color: #fca5a5; color: #b91c1c; }

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