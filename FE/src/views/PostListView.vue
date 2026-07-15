<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const posts = ref([]);

// 입력 폼 상태 관리
const isFormOpen = ref(false); // 클릭 시 폼 열기/닫기 토글용
const selectedCategory = ref("잡담"); // 기본값 '잡담'
const newTitle = ref("");
const newLocation = ref("");
const newDesc = ref("");
const newPassword = ref("");

// 삭제 검증용 상태 관리
const activeDeleteId = ref(null);
const deletePassword = ref("");

onMounted(() => {
  const savedPosts = localStorage.getItem("localhub_posts");
  if (savedPosts) {
    posts.value = JSON.parse(savedPosts);
  } else {
    // 카테고리와 임시 비밀번호('1234')가 포함된 초기 데이터 세팅
    const dummy = [
      {
        id: 1,
        category: "후기",
        title: "부산 광안리 드론쇼 명당 공유",
        location: "부산 수영구",
        desc: "여기 카페 2층 테라스가 숨겨진 뷰 맛집입니다.",
        password: "1234",
        likes: 12,
      },
      {
        id: 2,
        category: "잡담",
        title: "경주 황리단길 주차 꿀팁",
        location: "경북 경주시",
        desc: "주말에는 공영주차장 말고 이 골목을 이용해보세요.",
        password: "1234",
        likes: 45,
      },
      {
        id: 3,
        category: "구인",
        title: "이번주 토요일 애월 해안가 플로깅 하실 분!",
        location: "제주 애월읍",
        desc: "오전 10시에 투썸 앞에서 모여서 가볍게 쓰레기 줍고 커피 마셔요.",
        password: "1234",
        likes: 8,
      },
    ];
    posts.value = dummy;
    localStorage.setItem("localhub_posts", JSON.stringify(dummy));
  }
});

// 게시글 추가
const addPost = () => {
  if (
    !newTitle.value ||
    !newLocation.value ||
    !newDesc.value ||
    !newPassword.value
  ) {
    alert("모든 빈칸과 비밀번호를 입력해주세요!");
    return;
  }

  const newPost = {
    id: Date.now(),
    category: selectedCategory.value,
    title: newTitle.value,
    location: newLocation.value,
    desc: newDesc.value,
    password: newPassword.value, // 비밀번호 저장
    likes: 0,
  };

  posts.value.unshift(newPost);
  localStorage.setItem("localhub_posts", JSON.stringify(posts.value));

  // 입력창 초기화 및 폼 닫기
  newTitle.value = "";
  newLocation.value = "";
  newDesc.value = "";
  newPassword.value = "";
  selectedCategory.value = "잡담";
  isFormOpen.value = false;
};

// 게시글 삭제 시도 (비밀번호 확인창 토글)
const requestDelete = (e, id) => {
  e.stopPropagation(); // 카드 클릭(상세페이지 이동) 이벤트 방지
  if (activeDeleteId.value === id) {
    activeDeleteId.value = null;
  } else {
    activeDeleteId.value = id;
    deletePassword.value = "";
  }
};

// 비밀번호 검증 후 삭제 처리
const confirmDelete = (e, id) => {
  e.stopPropagation();
  const targetPost = posts.value.find((p) => p.id === id);

  if (targetPost.password === deletePassword.value) {
    posts.value = posts.value.filter((p) => p.id !== id);
    localStorage.setItem("localhub_posts", JSON.stringify(posts.value));
    activeDeleteId.value = null;
    alert("게시글이 삭제되었습니다.");
  } else {
    alert("비밀번호가 일치하지 않습니다.");
  }
};

const goToDetail = (id) => {
  router.push(`/post/${id}`);
};
</script>

<template>
  <div class="list-container">
    <section class="write-accordion">
      <div class="accordion-header" @click="isFormOpen = !isFormOpen">
        <div class="header-text">
          <h2>명소에 대한 생각이나 이야기를 공유해주세요!</h2>
          <p>
            이곳을 클릭하여 동네의 숨겨진 이야기와 유용한 꿀팁을 들려주세요.
          </p>
        </div>
        <span class="arrow-icon" :class="{ open: isFormOpen }">▼</span>
      </div>

      <div v-if="isFormOpen" class="accordion-content">
        <div class="input-group">
          <div class="form-item">
            <label>카테고리</label>
            <div class="category-selector">
              <button
                v-for="cat in ['잡담', '구인', '후기']"
                :key="cat"
                type="button"
                :class="['category-btn', { active: selectedCategory === cat }]"
                @click="selectedCategory = cat"
              >
                {{ cat }}
              </button>
            </div>
          </div>

          <div class="form-item">
            <label>제목</label>
            <input
              v-model="newTitle"
              type="text"
              placeholder="명소를 드러내는 멋진 제목을 작성해 주세요"
            />
          </div>

          <div class="form-item">
            <label>지역 위치</label>
            <input
              v-model="newLocation"
              type="text"
              placeholder="지역 이름 (예: 서울 마포구, 부산 해운대구)"
            />
          </div>

          <div class="form-item">
            <label>이야기 본문</label>
            <textarea
              v-model="newDesc"
              placeholder="이 명소와 관련된 꿀팁이나 생각을 자유롭게 들려주세요."
            ></textarea>
          </div>

          <div class="form-item">
            <label
              >비밀번호 설정
              <span class="sub-label">(글 수정/삭제 시 필요합니다)</span></label
            >
            <input
              v-model="newPassword"
              type="password"
              placeholder="비밀번호 4자리 입력"
              maxlength="8"
            />
          </div>
        </div>

        <button class="btn-submit-airbnb" @click="addPost">
          이야기 등록하기
        </button>
      </div>
    </section>

    <section class="grid-section">
      <h2 class="section-title">지역에 대한 사람들의 생각을 확인해보세요 ✈️</h2>

      <div class="grid-container">
        <div
          v-for="post in posts"
          :key="post.id"
          class="post-card"
          @click="goToDetail(post.id)"
        >
          <div class="card-image-field">
            <span class="category-badge">{{ post.category }}</span>
            <span class="location-badge">{{ post.location }}</span>
          </div>

          <div class="card-content">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.desc }}</p>

            <div class="card-footer">
              <span class="likes">💛 {{ post.likes || 0 }}</span>
              <button
                class="btn-delete-trigger"
                @click="requestDelete($event, post.id)"
              >
                삭제
              </button>
            </div>

            <div
              v-if="activeDeleteId === post.id"
              class="delete-confirm-box"
              @click.stop
            >
              <input
                v-model="deletePassword"
                type="password"
                placeholder="비밀번호 입력"
                @keyup.enter="confirmDelete($event, post.id)"
              />
              <button
                class="btn-confirm"
                @click="confirmDelete($event, post.id)"
              >
                확인
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.list-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 24px;
}

/* 1. 아코디언 스타일 글쓰기 폼 디자인 */
.write-accordion {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.02);
  margin-bottom: 48px;
  transition: box-shadow 0.2s;
}

.write-accordion:hover {
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.05);
}

.accordion-header {
  padding: 24px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background-color: #ffffff;
}

.header-text h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
  margin-bottom: 4px;
}

.header-text p {
  font-size: 0.9rem;
  color: var(--color-airbnb-gray);
}

.arrow-icon {
  font-size: 0.8rem;
  color: var(--color-airbnb-gray);
  transition: transform 0.2s;
}

.arrow-icon.open {
  transform: rotate(180deg);
}

.accordion-content {
  padding: 0 30px 30px 30px;
  border-top: 1px solid var(--color-border);
  background-color: #fcfcfc;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 24px;
  margin-bottom: 24px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-airbnb-dark);
}

.sub-label {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-airbnb-gray);
}

/* 토스 감성의 카테고리 셀렉터 */
.category-selector {
  display: flex;
  gap: 8px;
  background-color: #eeeeee;
  padding: 4px;
  border-radius: 10px;
  width: fit-content;
}

.category-btn {
  border: none;
  background: none;
  padding: 8px 20px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  color: var(--color-airbnb-gray);
  transition: all 0.2s;
}

.category-btn.active {
  background-color: white;
  color: var(--color-airbnb-dark);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.form-item input,
.form-item textarea {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.95rem;
  outline: none;
  background-color: white;
  transition: border-color 0.2s;
}

.form-item input:focus,
.form-item textarea:focus {
  border-color: var(--color-airbnb-red);
}

.form-item textarea {
  height: 120px;
  resize: vertical;
}

/* 가시성 좋은 등록 버튼 */
.btn-submit-airbnb {
  width: 100%;
  background-color: var(--color-airbnb-red);
  color: white;
  border: none;
  padding: 16px;
  font-size: 1.05rem;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
  transition: filter 0.2s;
  box-shadow: 0 4px 12px rgba(224, 26, 79, 0.2);
}

.btn-submit-airbnb:hover {
  filter: brightness(0.9);
}

/* 2. 게시물 리스트 그리드 영역 (한 줄에 3개 노출) */
.grid-section {
  margin-top: 20px;
}

.section-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 28px;
  color: var(--color-airbnb-dark);
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(
    3,
    1fr
  ); /* 넓은 화면에서 한 줄에 무조건 3개씩 배치 */
  gap: 24px;
}

/* 반응형 처리 (화면이 모바일 수준으로 좁아지면 1열로 전환) */
@media (max-width: 900px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
}

.post-card {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
}

.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}

.card-image-field {
  height: 160px;
  background-color: #ebebeb;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12px;
}

.category-badge {
  background-color: var(--color-airbnb-dark);
  color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
}

.location-badge {
  background-color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid var(--color-border);
}

.card-content {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.card-desc {
  font-size: 0.88rem;
  color: var(--color-airbnb-gray);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 16px;
  line-height: 1.4;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.likes {
  font-size: 0.85rem;
  font-weight: 600;
}

.btn-delete-trigger {
  background: none;
  border: none;
  color: var(--color-airbnb-gray);
  font-size: 0.8rem;
  cursor: pointer;
  text-decoration: underline;
}

.btn-delete-trigger:hover {
  color: var(--color-airbnb-red);
}

/* 카드 내부 비밀번호 입력박스 */
.delete-confirm-box {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: rgba(255, 255, 255, 0.96);
  padding: 12px 20px;
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 8px;
  align-items: center;
}

.delete-confirm-box input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.8rem;
  outline: none;
}

.btn-confirm {
  background-color: var(--color-airbnb-dark);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
}
</style>
