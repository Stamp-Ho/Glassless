<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const post = ref(null);

onMounted(() => {
  const savedPosts = JSON.parse(localStorage.getItem("localhub_posts") || "[]");
  post.value = savedPosts.find((p) => p.id === Number(route.params.id));
});
</script>

<template>
  <div class="detail-container" v-if="post">
    <button class="btn-back" @click="router.push('/posts')">
      ← 전체 목록으로 돌아가기
    </button>
    <div class="detail-card">
      <span class="detail-badge">{{ post.location }}</span>
      <h1 class="detail-title">{{ post.title }}</h1>
      <p class="detail-desc">{{ post.desc }}</p>
    </div>
  </div>
</template>

<style scoped>
.detail-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 24px;
}
.btn-back {
  background: none;
  border: none;
  color: var(--color-airbnb-red);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 20px;
}
.detail-card {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-airbnb);
  padding: 40px;
}
.detail-badge {
  display: inline-block;
  background-color: #fff0f2;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-airbnb-red);
}
.detail-title {
  font-size: 2rem;
  margin-bottom: 24px;
}
.detail-desc {
  font-size: 1.1rem;
  white-space: pre-wrap;
  line-height: 1.8;
}
</style>
