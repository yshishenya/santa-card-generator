<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const deliveryEnv = computed(() => route.query.env === 'prod' ? 'prod' : 'staging')
const messageId = computed(() => {
  const rawValue = route.query.message_id
  return typeof rawValue === 'string' && rawValue.length > 0 ? rawValue : null
})

let redirectTimeout: ReturnType<typeof setTimeout> | null = null

function goHome(): void {
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
  router.push('/')
}

onMounted(() => {
  redirectTimeout = setTimeout(() => {
    goHome()
  }, 5000)
})

onUnmounted(() => {
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
})
</script>

<template>
  <section class="success-page">
    <header class="success-topline">
      <div class="success-topline__brand">
        <span>P4.0 Alter Ego</span>
        <span>/</span>
        <span>Delivery Complete</span>
      </div>

      <span class="app-chip" :class="deliveryEnv === 'prod' ? 'app-chip--blue' : 'app-chip--accent'">
        {{ deliveryEnv }}
      </span>
    </header>

    <div class="success-layout">
      <article class="app-panel app-panel--strong success-card">
        <div class="success-card__mark">
          <span class="material-symbols-outlined" aria-hidden="true">check</span>
        </div>

        <div class="success-card__copy">
          <p class="app-kicker">Portrait Successfully Transmitted</p>
          <h1 class="app-display success-card__title">Карточка отправлена</h1>
          <p class="app-subtle">
            Финальный квадрат ушёл в Telegram, а исходный PNG уже сохранён в print archive для печати.
          </p>
        </div>

        <div class="app-meta-grid">
          <div class="app-meta-item">
            <p class="app-meta-term">Окружение</p>
            <p class="app-meta-value">{{ deliveryEnv }}</p>
          </div>
          <div class="app-meta-item">
            <p class="app-meta-term">Message ID</p>
            <p class="app-meta-value">{{ messageId ?? 'не передан' }}</p>
          </div>
        </div>

        <div class="success-card__actions">
          <button class="app-button" @click="goHome">
            <span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>
            Сгенерировать ещё одну
          </button>

          <p class="success-card__hint">
            Автоматический возврат на главный экран через 5 секунд.
          </p>
        </div>
      </article>

      <aside class="success-side">
        <article class="app-panel success-side__card">
          <p class="app-kicker">Telegram</p>
          <h2>В тему уходит только картинка + имя</h2>
          <p>
            Описание alter ego остаётся внутри production-данных и не добавляется в публичную подпись.
          </p>
        </article>

        <article class="app-panel success-side__card">
          <p class="app-kicker">Print Archive</p>
          <h2>Original PNG сохранён</h2>
          <p>
            Организаторы могут скачать файл отдельно или собрать весь архив одним ZIP из защищённого раздела.
          </p>
        </article>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.success-page {
  display: grid;
  gap: 1.25rem;
}

.success-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1.5px solid var(--black);
}

.success-topline__brand {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.success-layout {
  display: grid;
  gap: 1rem;
}

.success-card,
.success-side__card {
  padding: 1.25rem;
}

.success-card {
  display: grid;
  gap: 1rem;
}

.success-card__mark {
  display: grid;
  place-items: center;
  width: 4.5rem;
  height: 4.5rem;
  border: 1.5px solid var(--black);
  background: var(--digital-mint);
}

.success-card__mark .material-symbols-outlined {
  font-size: 2rem;
  font-weight: 700;
}

.success-card__copy {
  display: grid;
  gap: 0.65rem;
}

.success-card__title {
  max-width: 9ch;
}

.success-card__actions {
  display: grid;
  gap: 0.75rem;
}

.success-card__hint {
  margin: 0;
  font-size: 0.72rem;
  line-height: 1.6;
  color: var(--text-soft);
}

.success-side {
  display: grid;
  gap: 1rem;
}

.success-side__card {
  display: grid;
  gap: 0.5rem;
}

.success-side__card h2,
.success-side__card p {
  margin: 0;
}

.success-side__card h2 {
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.35;
  text-transform: uppercase;
}

.success-side__card p:last-child {
  font-size: 0.78rem;
  line-height: 1.65;
  color: var(--text-soft);
}

@media (min-width: 980px) {
  .success-layout {
    grid-template-columns: minmax(0, 38rem) 18rem;
    align-items: start;
  }
}

@media (max-width: 767px) {
  .success-topline {
    flex-direction: column;
    align-items: flex-start;
  }

  .success-card,
  .success-side__card {
    padding: 1rem;
  }
}
</style>
