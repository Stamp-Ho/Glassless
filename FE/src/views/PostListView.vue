<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const posts = ref([]);
const newTitle = ref('');
const newLocation = ref('');
const newDesc = ref('');

onMounted(() => {
  const savedPosts = localStorage.getItem('localhub_posts');
  if (savedPosts) {
    posts.value = JSON.parse(savedPosts);
  } else {
    const dummy = [
      { id: 1, title: '부산 광안리 드론쇼 명당 공유', location: '부산 수영구', desc: '여기 카페 2층 테라스가 숨겨진 뷰 맛집입니다.', likes: 12 },
      { id: 2, title: '경주 황리단길 주차 꿀팁', location: '경북 경주시', desc: '주말에는 공영주차장 말고 이 골목을 이용해보세요.', likes: 45 }
    ];
    posts.value = dummy;
    localStorage.setItem('localhub_posts', JSON.stringify(dummy));
  }
});

const addPost = () => {
  if (!newTitle.value || !newLocation.value) return;

  const newPost = {
    id: Date.now(),
    title: newTitle.value,
    location: newLocation.value,
    desc: newDesc.value,
    likes: 0
  };

  posts.value.unshift(newPost);
  localStorage.setItem('localhub_posts', JSON.stringify(posts.value));

  newTitle.value = '';
  newLocation.value = '';
  newDesc.value = '';
};

const goToDetail = (id) => {
  router.push(`/post/${id}`);
};
</script>

<template>
  <div class="list-container">
    <section class="write-card">
      <h2>📌 우리 동네 꿀정보 공유하기</h2>
      <div class="input-group">
        <input v-model="newTitle" type="text" placeholder="제목 (예: 숨겨진 산책로 발견)" />
        <input v-model="newLocation" type="text" placeholder="지역 (예: 서울 마포구)" />
        <textarea v-model="newDesc" placeholder="내용을 입력해주세요."></textarea>
      </div>
      <button class="btn-airbnb" @click="addPost">등록하기</button>
    </section>

    <section class="grid-section">
      <h2 class="section-title">최근 올라온 지역 정보</h2>
      <div class="grid-container">
        <div v-for="post in posts" :key="post.id" class="post-card" @click="goToDetail(post.id)">
          <div class="card-image">
            <span class="location-badge">{{ post.location }}</span>
          </div>
          <div class="card-content">
            <h3 class="card-title">{{ post.title }}</h3>
            <p class="card-desc">{{ post.desc }}</p>
            <div class="card-footer">
              <span class="likes">💛 {{ post.likes }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.list-container { max-width: 1200px; margin: 40px auto; padding: 0 24px; }
.write-card { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); padding: 30px; margin-bottom: 40px; }
.write-card h2 { font-size: 1.3rem; margin-bottom: 20px; }
.input-group { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.input-group input, .input-group textarea { border: 1px solid var(--color-border); border-radius: 8px; padding: 14px; font-size: 1rem; outline: none; }
.input-group input:focus, .input-group textarea:focus { border-color: var(--color-airbnb-red); }
.section-title { font-size: 1.5rem; margin-bottom: 24px; }
.grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
.post-card { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); overflow: hidden; cursor: pointer; transition: all 0.2s; }
.post-card:hover { transform: translateY(-3px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
.card-image { height: 180px; background-color: #f1f1f1; position: relative; display: flex; align-items: flex-end; padding: 16px; }
.location-badge { background-color: white; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; border: 1px solid var(--color-border); }
.card-content { padding: 20px; }
.card-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }
.card-desc { font-size: 0.9rem; color: var(--color-airbnb-gray); margin-bottom: 16px; }
.card-footer { display: flex; justify-content: flex-end; }
</style>