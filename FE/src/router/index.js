// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import PostListView from '../views/PostListView.vue';
import MapView from '../views/MapView.vue';
import DetailView from '../views/DetailView.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/posts',
    name: 'PostList',
    component: PostListView
  },
  {
    path: '/map',
    name: 'Map',
    component: MapView
  },
  {
    path: '/posts/:id',
    alias: '/post/:id',
    name: 'Detail',
    component: DetailView,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;