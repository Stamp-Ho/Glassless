<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const post = ref(null);
const isLoading = ref(false);
const errorMessage = ref('');
const isEditMode = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const isDeleteModalOpen = ref(false);

const categoryOptions = ['잡담', '후기', '질문', '구인'];

const editTitle = ref('');
const editContent = ref('');
const editCategory = ref('잡담');
const editLocationId = ref('');
const editPassword = ref('');
const deletePassword = ref('');

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const formatDateTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR');
};

const fetchPostDetail = async () => {
  const postId = Number(route.params.id);
  if (!Number.isInteger(postId) || postId <= 0) {
    errorMessage.value = '유효하지 않은 게시글 ID입니다.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`);
    if (response.status === 404) {
      throw new Error('존재하지 않는 게시글입니다.');
    }
    if (!response.ok) {
      throw new Error('게시글 상세 정보를 불러오지 못했습니다.');
    }

    post.value = await response.json();
    syncEditForm();
  } catch (error) {
    console.error(error);
    errorMessage.value = error.message || '상세 조회 중 오류가 발생했습니다.';
  } finally {
    isLoading.value = false;
  }
};

const syncEditForm = () => {
  if (!post.value) return;
  editTitle.value = post.value.title || '';
  editContent.value = post.value.content || '';
  editCategory.value = post.value.category || '잡담';
  editLocationId.value = post.value.location_id != null ? String(post.value.location_id) : '';
  editPassword.value = '';
};

const startEdit = () => {
  syncEditForm();
  isEditMode.value = true;
};

const cancelEdit = () => {
  isEditMode.value = false;
  syncEditForm();
};

const openDeleteModal = () => {
  deletePassword.value = '';
  isDeleteModalOpen.value = true;
};

const closeDeleteModal = () => {
  if (isDeleting.value) return;
  isDeleteModalOpen.value = false;
  deletePassword.value = '';
};

const saveEdit = async () => {
  if (isSaving.value || !post.value) return;

  if (!editTitle.value.trim() || !editContent.value.trim()) {
    alert('제목과 본문은 필수입니다.');
    return;
  }
  if (!editPassword.value.trim()) {
    alert('수정을 위해 비밀번호를 입력해주세요.');
    return;
  }

  const payload = {
    password: editPassword.value,
    title: editTitle.value.trim(),
    content: editContent.value.trim(),
    category: editCategory.value,
  };

  if (editLocationId.value.trim()) {
    payload.location_id = Number(editLocationId.value);
  }

  try {
    isSaving.value = true;
    const response = await fetch(`${API_BASE_URL}/api/posts/${post.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody?.detail || '수정에 실패했습니다.');
    }

    post.value = await response.json();
    isEditMode.value = false;
    syncEditForm();
    alert('게시글이 수정되었습니다.');
  } catch (error) {
    console.error(error);
    alert(error.message || '수정에 실패했습니다.');
  } finally {
    isSaving.value = false;
  }
};

const deletePost = async () => {
  if (isDeleting.value || !post.value) return;
  if (!deletePassword.value.trim()) {
    alert('삭제를 위해 비밀번호를 입력해주세요.');
    return;
  }

  try {
    isDeleting.value = true;
    const response = await fetch(`${API_BASE_URL}/api/posts/${post.value.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: deletePassword.value }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody?.detail || '삭제에 실패했습니다.');
    }

    alert('게시글이 삭제되었습니다.');
    isDeleteModalOpen.value = false;
    router.push('/posts');
  } catch (error) {
    console.error(error);
    alert(error.message || '삭제에 실패했습니다.');
  } finally {
    isDeleting.value = false;
  }
};

onMounted(async () => {
  await fetchPostDetail();
});
</script>

<template>
  <div class="detail-container">
    <button class="btn-back" @click="router.push('/posts')">← 전체 목록으로 돌아가기</button>

    <div v-if="isLoading" class="state-message">게시글을 불러오는 중입니다...</div>
    <div v-else-if="errorMessage" class="state-message error">{{ errorMessage }}</div>

    <div v-else-if="post" class="detail-card">
      <div class="detail-meta-row top-actions">
        <div class="left-meta">
          <select v-if="isEditMode" v-model="editCategory" class="detail-badge-select">
            <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <span v-else class="detail-badge">{{ post.category }}</span>
          <span class="detail-sub">지역: {{ post.region || '미지정' }}</span>
        </div>
        <div class="action-buttons">
          <button v-if="!isEditMode" class="btn-secondary" @click="startEdit">수정</button>
          <template v-else>
            <button class="btn-secondary" @click="cancelEdit">취소</button>
            <button class="btn-primary" :disabled="isSaving" @click="saveEdit">
              {{ isSaving ? '저장 중...' : '수정 확정' }}
            </button>
          </template>
        </div>
      </div>
      <h1 v-if="!isEditMode" class="detail-title">{{ post.title }}</h1>
      <input v-else v-model="editTitle" class="detail-title-input" type="text" maxlength="200" />

      <div class="detail-info">
        <span>게시글 ID: {{ post.id }}</span>
        <span>작성 시각: {{ formatDateTime(post.created_at) }}</span>
        <span>수정 시각: {{ formatDateTime(post.updated_at) }}</span>
      </div>

      <p v-if="!isEditMode" class="detail-desc">{{ post.content }}</p>
      <textarea v-else v-model="editContent" class="detail-desc-input" rows="8" maxlength="5000"></textarea>

      <div v-if="isEditMode" class="edit-password-row">
        <label>수정 비밀번호</label>
        <input v-model="editPassword" type="password" maxlength="100" placeholder="작성 시 비밀번호 입력" />
      </div>

      <div class="card-bottom-actions">
        <button class="btn-danger" @click="openDeleteModal">삭제</button>
      </div>
    </div>

    <div v-if="isDeleteModalOpen" class="delete-modal-overlay" @click.self="closeDeleteModal">
      <div class="delete-modal">
        <h3>게시글 삭제</h3>
        <p>삭제하려면 비밀번호를 입력한 뒤 확인을 눌러주세요.</p>
        <input
          v-model="deletePassword"
          type="password"
          maxlength="100"
          placeholder="작성 시 비밀번호 입력"
          @keyup.enter="deletePost"
        />
        <div class="modal-actions">
          <button class="btn-secondary" :disabled="isDeleting" @click="closeDeleteModal">취소</button>
          <button class="btn-danger" :disabled="isDeleting" @click="deletePost">
            {{ isDeleting ? '삭제 중...' : '확인' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-container { max-width: 800px; margin: 40px auto; padding: 0 24px; }
.btn-back { background: none; border: none; color: var(--color-airbnb-red); font-size: 1rem; font-weight: 600; cursor: pointer; margin-bottom: 20px; }
.state-message { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); padding: 24px; color: var(--color-airbnb-gray); }
.state-message.error { color: #b42318; }
.detail-card { background-color: white; border: 1px solid var(--color-border); border-radius: var(--radius-airbnb); padding: 40px; position: relative; }
.detail-meta-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.top-actions { align-items: flex-start; }
.left-meta { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.detail-badge { display: inline-block; background-color: #FFF0F2; padding: 6px 14px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; color: var(--color-airbnb-red); }
.detail-badge-select {
  background-color: #FFF0F2;
  color: var(--color-airbnb-red);
  border: 1px solid #f0b8c5;
  border-radius: 20px;
  padding: 6px 10px;
  font-size: 0.9rem;
  font-weight: 700;
}
.detail-sub { color: var(--color-airbnb-gray); font-size: 0.9rem; }
.detail-title { font-size: 2rem; margin-bottom: 24px; }
.detail-title-input {
  width: 100%;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 24px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 12px;
}
.detail-info { display: flex; flex-wrap: wrap; gap: 10px 16px; margin-bottom: 20px; font-size: 0.88rem; color: var(--color-airbnb-gray); }
.detail-desc { font-size: 1.1rem; white-space: pre-wrap; line-height: 1.8; }
.detail-desc-input {
  width: 100%;
  font-size: 1.1rem;
  line-height: 1.8;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px 14px;
  resize: vertical;
}

.inline-edit-id {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.inline-edit-id input {
  width: 110px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 6px 8px;
}

.edit-password-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.edit-password-row label {
  font-size: 0.9rem;
  font-weight: 700;
}

.edit-password-row input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 10px 12px;
}

.action-buttons { display: flex; gap: 8px; }
.btn-primary,
.btn-secondary,
.btn-danger {
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  background-color: var(--color-airbnb-red);
  color: white;
  border: 2px solid #8f0d2f;
}

.btn-secondary {
  background-color: white;
  color: var(--color-airbnb-dark);
  border: 2px solid #444;
}

.btn-danger {
  background-color: #fff5f5;
  color: #b42318;
  border: 2px solid #b42318;
}

.btn-primary:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-bottom-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.delete-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.delete-modal {
  width: min(92vw, 420px);
  background: white;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.delete-modal h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
}

.delete-modal p {
  margin: 0 0 12px;
  color: var(--color-airbnb-gray);
  font-size: 0.9rem;
}

.delete-modal input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 11px 12px;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 640px) {
  .modal-actions,
  .edit-password-row,
  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .btn-primary,
  .btn-secondary,
  .btn-danger {
    width: 100%;
  }
}
</style>