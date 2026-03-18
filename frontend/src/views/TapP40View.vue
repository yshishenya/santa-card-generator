<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { apiClient, APIError } from '@/api/client'
import type { TapP40LeaderboardEntry } from '@/types'
import { loadPlayerName, savePlayerName } from '@/utils/playerIdentity'

type TileKind = 'target' | 'distractor' | 'empty'
type DistractorKind = 'spark' | 'frame' | 'swirl' | 'flash'

interface GameTile {
  id: number
  kind: TileKind
  distractorKind: DistractorKind | null
}

const GRID_SIZE = 12
const DISTRACTOR_COUNT = 5
const ROUND_DURATION_MS = 25000
const INITIAL_SHIFT_MS = 850
const GAME_VERSION = 'v1'

const playerName = ref(loadPlayerName())
const phase = ref<'idle' | 'playing' | 'finished'>('idle')
const score = ref(0)
const correctTaps = ref(0)
const wrongTaps = ref(0)
const timeLeftMs = ref(ROUND_DURATION_MS)
const board = ref<GameTile[]>(buildBoard())
const feedback = ref<'good' | 'miss' | null>(null)
const lastRank = ref<number | null>(null)
const personalBest = ref(false)
const isSaving = ref(false)
const leaderboardPeriod = ref<'all' | 'day'>('day')
const leaderboard = ref<TapP40LeaderboardEntry[]>([])
const leaderboardLoading = ref(false)
const leaderboardError = ref<string | null>(null)
const submitError = ref<string | null>(null)

let roundStartTs = 0
let frameHandle: number | null = null
let shiftHandle: ReturnType<typeof setTimeout> | null = null
let feedbackHandle: ReturnType<typeof setTimeout> | null = null

const hasIdentity = computed(() => playerName.value.trim().length > 0)
const canStart = computed(() => playerName.value.trim().length > 0 && phase.value !== 'playing')
const accuracy = computed(() => {
  const totalTaps = correctTaps.value + wrongTaps.value
  if (totalTaps === 0) {
    return 100
  }
  return Math.round((correctTaps.value / totalTaps) * 100)
})
const bestScore = computed(() => leaderboard.value[0]?.score ?? null)
const bestScoreLabel = computed(() => leaderboardPeriod.value === 'day' ? 'Лучший счёт дня' : 'Лучший счёт за всё время')
const playerNameHint = computed(() => playerName.value.trim() || 'Игрок P4.0')

function buildBoard(targetIndex = 0, distractorIndexes: number[] = []): GameTile[] {
  const distractorKinds: DistractorKind[] = ['spark', 'frame', 'swirl', 'flash']
  return Array.from({ length: GRID_SIZE }, (_, index) => {
    if (index === targetIndex) {
      return { id: index, kind: 'target', distractorKind: null }
    }
    if (distractorIndexes.includes(index)) {
      return {
        id: index,
        kind: 'distractor',
        distractorKind: distractorKinds[index % distractorKinds.length],
      }
    }
    return { id: index, kind: 'empty', distractorKind: null }
  })
}

function randomIndexes(): { targetIndex: number; distractorIndexes: number[] } {
  const slots = Array.from({ length: GRID_SIZE }, (_, index) => index)
  const targetIndex = slots.splice(Math.floor(Math.random() * slots.length), 1)[0]
  const distractorIndexes: number[] = []

  while (distractorIndexes.length < DISTRACTOR_COUNT && slots.length > 0) {
    const randomIndex = Math.floor(Math.random() * slots.length)
    distractorIndexes.push(slots.splice(randomIndex, 1)[0])
  }

  return { targetIndex, distractorIndexes }
}

function reshuffleBoard(): void {
  const { targetIndex, distractorIndexes } = randomIndexes()
  board.value = buildBoard(targetIndex, distractorIndexes)
}

function showFeedback(value: 'good' | 'miss'): void {
  feedback.value = value
  if (feedbackHandle) {
    clearTimeout(feedbackHandle)
  }
  feedbackHandle = setTimeout(() => {
    feedback.value = null
  }, 220)
}

function clearTimers(): void {
  if (frameHandle !== null) {
    window.cancelAnimationFrame(frameHandle)
    frameHandle = null
  }
  if (shiftHandle) {
    clearTimeout(shiftHandle)
    shiftHandle = null
  }
  if (feedbackHandle) {
    clearTimeout(feedbackHandle)
    feedbackHandle = null
  }
}

function scheduleShift(): void {
  if (phase.value !== 'playing') {
    return
  }

  const dynamicDelay = Math.max(360, INITIAL_SHIFT_MS - score.value * 12)
  shiftHandle = setTimeout(() => {
    reshuffleBoard()
    scheduleShift()
  }, dynamicDelay)
}

function tick(): void {
  if (phase.value !== 'playing') {
    return
  }

  const elapsed = Date.now() - roundStartTs
  const remaining = Math.max(0, ROUND_DURATION_MS - elapsed)
  timeLeftMs.value = remaining

  if (remaining <= 0) {
    endRound()
    return
  }

  frameHandle = window.requestAnimationFrame(tick)
}

function startRound(): void {
  const normalizedName = playerName.value.trim()
  if (!normalizedName) {
    return
  }

  playerName.value = normalizedName
  savePlayerName(normalizedName)
  submitError.value = null
  score.value = 0
  correctTaps.value = 0
  wrongTaps.value = 0
  timeLeftMs.value = ROUND_DURATION_MS
  lastRank.value = null
  personalBest.value = false
  phase.value = 'playing'
  roundStartTs = Date.now()
  reshuffleBoard()
  clearTimers()
  scheduleShift()
  tick()
}

async function endRound(): Promise<void> {
  clearTimers()
  phase.value = 'finished'
  timeLeftMs.value = 0

  const normalizedName = playerName.value.trim()
  if (!normalizedName) {
    return
  }

  try {
    isSaving.value = true
    submitError.value = null
    const response = await apiClient.saveTapP40Score({
      player_name: normalizedName,
      score: score.value,
      correct_taps: correctTaps.value,
      wrong_taps: wrongTaps.value,
      duration_ms: ROUND_DURATION_MS,
      game_version: GAME_VERSION,
    })
    lastRank.value = response.rank
    personalBest.value = response.personal_best
    await fetchLeaderboard(leaderboardPeriod.value)
  } catch (err) {
    submitError.value = getErrorMessage(err, 'Не удалось сохранить результат.')
  } finally {
    isSaving.value = false
  }
}

function handleTilePress(tile: GameTile): void {
  if (phase.value !== 'playing') {
    return
  }

  if (tile.kind === 'target') {
    score.value += 1
    correctTaps.value += 1
    showFeedback('good')
    reshuffleBoard()
    if (shiftHandle) {
      clearTimeout(shiftHandle)
    }
    scheduleShift()
    return
  }

  if (tile.kind === 'distractor') {
    score.value = Math.max(0, score.value - 1)
    wrongTaps.value += 1
    showFeedback('miss')
  }
}

function restartRound(): void {
  clearTimers()
  phase.value = 'idle'
  score.value = 0
  correctTaps.value = 0
  wrongTaps.value = 0
  timeLeftMs.value = ROUND_DURATION_MS
  feedback.value = null
  reshuffleBoard()
}

function formatTime(ms: number): string {
  return (ms / 1000).toFixed(1)
}

function formatDuration(ms: number): string {
  return `${(ms / 1000).toFixed(1)} c`
}

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}

async function fetchLeaderboard(period: 'all' | 'day'): Promise<void> {
  leaderboardPeriod.value = period
  try {
    leaderboardLoading.value = true
    leaderboardError.value = null
    const response = await apiClient.fetchTapP40Leaderboard(period, 10)
    leaderboard.value = response.entries
  } catch (err) {
    leaderboardError.value = getErrorMessage(err, 'Не удалось загрузить рейтинг.')
  } finally {
    leaderboardLoading.value = false
  }
}

onMounted(() => {
  reshuffleBoard()
  if (hasIdentity.value) {
    void fetchLeaderboard(leaderboardPeriod.value)
  }
})

onUnmounted(() => {
  clearTimers()
})

watch(playerName, (value) => {
  savePlayerName(value)
})
</script>

<template>
  <section v-if="hasIdentity" class="tap-page">
    <header class="tap-header">
      <div class="tap-header__copy">
        <p class="app-kicker">P4.0 Mini Game</p>
        <h1 class="app-display">Tap the P4.0</h1>
        <p class="app-subtle">
          Ловите аватарку, не жмите на приманки и попробуйте влететь в топ за 25 секунд.
        </p>
      </div>

      <div class="tap-header__actions">
        <RouterLink to="/" class="app-button-ghost">
          <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
          К генератору
        </RouterLink>
      </div>
    </header>

    <div class="tap-layout">
      <article class="app-panel app-panel--strong tap-arena">
        <div class="tap-arena__topline">
          <div class="tap-metric">
            <span class="tap-metric__label">Счёт</span>
            <strong>{{ score }}</strong>
          </div>
          <div class="tap-metric">
            <span class="tap-metric__label">Таймер</span>
            <strong>{{ formatTime(timeLeftMs) }}</strong>
          </div>
          <div class="tap-metric">
            <span class="tap-metric__label">Точность</span>
            <strong>{{ accuracy }}%</strong>
          </div>
        </div>

        <div class="tap-setup">
          <label class="app-field tap-setup__field">
            <span class="app-label">Имя для рейтинга</span>
            <input
              v-model="playerName"
              type="text"
              maxlength="80"
              class="app-input"
              placeholder="Например: Катя"
              :disabled="phase === 'playing'"
            >
          </label>

          <div class="tap-setup__cta">
            <button
              type="button"
              class="app-button"
              :disabled="!canStart"
              @click="startRound"
            >
              <span class="material-symbols-outlined" aria-hidden="true">
                {{ phase === 'finished' ? 'replay' : 'play_arrow' }}
              </span>
              {{ phase === 'finished' ? 'Ещё раунд' : 'Старт' }}
            </button>
            <p class="tap-setup__hint">
              Тапайте только по боту P4.0. Лишние нажатия тоже считаются.
            </p>
          </div>
        </div>

        <div
          class="tap-board"
          :class="feedback ? `tap-board--${feedback}` : ''"
          @contextmenu.prevent
        >
          <button
            v-for="tile in board"
            :key="tile.id"
            type="button"
            class="tap-tile"
            :class="[
              `tap-tile--${tile.kind}`,
              tile.distractorKind ? `tap-tile--${tile.distractorKind}` : '',
            ]"
            :disabled="phase !== 'playing' || tile.kind === 'empty'"
            :aria-label="tile.kind === 'target' ? 'Цель P4.0' : 'Ложная плитка'"
            @click="handleTilePress(tile)"
            @contextmenu.prevent
          >
            <template v-if="tile.kind === 'target'">
              <img src="/favicon.svg" alt="" class="tap-tile__target-mark" draggable="false">
              <span class="tap-tile__target-pulse"></span>
            </template>

            <template v-else-if="tile.kind === 'distractor'">
              <span v-if="tile.distractorKind === 'spark'" class="tap-tile__spark"></span>
              <span v-else-if="tile.distractorKind === 'frame'" class="tap-tile__frame"></span>
              <span v-else-if="tile.distractorKind === 'swirl'" class="tap-tile__swirl"></span>
              <span v-else class="tap-tile__flash"></span>
            </template>
          </button>
        </div>

        <div class="tap-bottomline">
          <div class="tap-bottomline__stats">
            <span>Попаданий: {{ correctTaps }}</span>
            <span>Промахов: {{ wrongTaps }}</span>
            <span v-if="bestScore !== null">{{ bestScoreLabel }}: {{ bestScore }}</span>
          </div>

          <button type="button" class="app-button-ghost" @click="restartRound">
            <span class="material-symbols-outlined" aria-hidden="true">refresh</span>
            Сбросить раунд
          </button>
        </div>

        <div v-if="phase === 'finished'" class="tap-result">
          <div class="tap-result__copy">
            <p class="app-kicker">Раунд завершён</p>
            <h2 class="app-heading">{{ playerNameHint }}, у вас {{ score }} очков</h2>
            <p class="app-subtle">
              <template v-if="isSaving">Сохраняем результат в рейтинг...</template>
              <template v-else-if="lastRank !== null">
                Место в рейтинге: #{{ lastRank }}. {{ personalBest ? 'Это ваш лучший результат.' : 'Можно выбить лучше.' }}
              </template>
              <template v-else>
                Раунд засчитан локально. Можно сыграть ещё раз.
              </template>
            </p>
          </div>

          <div v-if="submitError" class="app-error">
            {{ submitError }}
          </div>
        </div>
      </article>

      <aside class="app-panel tap-leaderboard">
        <div class="tap-leaderboard__header">
          <div>
            <p class="app-kicker">Leaderboard</p>
            <h2 class="app-heading">Кто быстрее всех ловит P4.0</h2>
          </div>

          <div class="tap-leaderboard__tabs" role="tablist" aria-label="Период рейтинга">
            <button
              type="button"
              class="app-chip"
              :class="{ 'app-chip--blue': leaderboardPeriod === 'day' }"
              @click="fetchLeaderboard('day')"
            >
              Сегодня
            </button>
            <button
              type="button"
              class="app-chip"
              :class="{ 'app-chip--blue': leaderboardPeriod === 'all' }"
              @click="fetchLeaderboard('all')"
            >
              Всё время
            </button>
          </div>
        </div>

        <div v-if="leaderboardError" class="app-error">
          {{ leaderboardError }}
        </div>

        <div v-else-if="leaderboardLoading" class="tap-leaderboard__loading">
          Загружаем топ игроков...
        </div>

        <div v-else-if="leaderboard.length === 0" class="tap-leaderboard__loading">
          Пока пусто. Первый быстрый палец попадёт в топ.
        </div>

        <ol v-else class="tap-leaderboard__list">
          <li v-for="entry in leaderboard" :key="`${leaderboardPeriod}-${entry.rank}-${entry.player_name}`" class="tap-leaderboard__item">
            <div class="tap-leaderboard__rank">#{{ entry.rank }}</div>
            <div class="tap-leaderboard__identity">
              <strong>{{ entry.player_name }}</strong>
              <span>{{ entry.correct_taps }} попаданий · {{ entry.wrong_taps }} промаха</span>
            </div>
            <div class="tap-leaderboard__score">
              <strong>{{ entry.score }}</strong>
              <span>{{ formatDuration(entry.duration_ms) }}</span>
            </div>
          </li>
        </ol>
      </aside>
    </div>
  </section>

  <section v-else class="tap-page tap-page--gate">
    <article class="app-panel app-panel--strong tap-gate">
      <p class="app-kicker">Tap the P4.0</p>
      <h1 class="app-display">Сначала имя</h1>
      <p class="app-subtle">
        Игра открывается только после того, как вы введёте имя на главной. Рейтинг должен знать, кого хвалить.
      </p>

      <RouterLink to="/" class="app-button">
        <span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
        Вернуться на главную
      </RouterLink>
    </article>
  </section>
</template>

<style scoped>
.tap-page {
  display: grid;
  gap: 1rem;
}

.tap-page--gate {
  min-height: 60vh;
  place-items: center;
}

.tap-gate {
  display: grid;
  gap: 0.9rem;
  width: min(100%, 28rem);
  padding: 1.2rem;
}

.tap-header {
  display: grid;
  gap: 1rem;
  align-items: start;
}

.tap-header__copy {
  display: grid;
  gap: 0.5rem;
}

.tap-header__actions {
  display: flex;
  justify-content: flex-start;
}

.tap-layout {
  display: grid;
  gap: 1rem;
}

.tap-arena,
.tap-leaderboard {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}

.tap-arena__topline {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.tap-metric {
  display: grid;
  gap: 0.15rem;
  padding: 0.75rem;
  border: 2px solid var(--black);
  background: var(--white);
}

.tap-metric__label {
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
}

.tap-metric strong {
  font-size: 1.4rem;
  line-height: 1;
}

.tap-setup {
  display: grid;
  gap: 0.75rem;
}

.tap-setup__field {
  margin: 0;
}

.tap-setup__cta {
  display: grid;
  gap: 0.65rem;
}

.tap-setup__hint {
  margin: 0;
  font-size: 0.76rem;
  line-height: 1.5;
  color: var(--text-soft);
}

.tap-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  padding: 0.65rem;
  border: 2px solid var(--black);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(185, 205, 255, 0.78));
  transition: transform 120ms ease, background 120ms ease;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}

.tap-board--good {
  transform: scale(1.01);
}

.tap-board--miss {
  background: linear-gradient(180deg, rgba(255, 137, 49, 0.3), rgba(255, 255, 255, 0.94));
}

.tap-tile {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 5.6rem;
  border: 2px solid var(--black);
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.82);
  transition: transform 100ms ease, background 100ms ease, box-shadow 100ms ease;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
}

.tap-tile:disabled {
  opacity: 1;
}

.tap-tile--target {
  background: var(--accent-yellow);
  box-shadow: 4px 4px 0 var(--black);
}

.tap-tile--target:active,
.tap-tile--distractor:active {
  transform: scale(0.96);
}

.tap-tile--empty {
  background: rgba(255, 255, 255, 0.45);
  border-style: dashed;
}

.tap-tile--spark {
  background: var(--soft-lavender);
}

.tap-tile--frame {
  background: var(--digital-mint);
}

.tap-tile--swirl {
  background: var(--light-blue);
}

.tap-tile--flash {
  background: #fff4bf;
}

.tap-tile__target-mark {
  width: 64%;
  max-width: 3rem;
  aspect-ratio: 1;
  pointer-events: none;
  -webkit-user-drag: none;
  -webkit-touch-callout: none;
  user-select: none;
}

.tap-tile__target-pulse {
  position: absolute;
  inset: 0.35rem;
  border: 2px dashed var(--black);
  border-radius: 0.85rem;
}

.tap-tile__spark,
.tap-tile__frame,
.tap-tile__swirl,
.tap-tile__flash {
  display: block;
  position: relative;
  pointer-events: none;
  -webkit-touch-callout: none;
  user-select: none;
}

.tap-tile__spark {
  width: 2.2rem;
  height: 2.2rem;
  background: var(--white);
  clip-path: polygon(50% 0%, 62% 36%, 100% 50%, 62% 64%, 50% 100%, 38% 64%, 0% 50%, 38% 36%);
}

.tap-tile__frame {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid var(--black);
  border-radius: 0.75rem;
  background: transparent;
}

.tap-tile__swirl {
  width: 2.6rem;
  height: 2.6rem;
  border: 3px solid var(--black);
  border-radius: 50%;
}

.tap-tile__swirl::after {
  content: '';
  position: absolute;
  inset: 0.45rem;
  border-top: 3px solid var(--black);
  border-right: 3px solid transparent;
  border-bottom: 3px solid transparent;
  border-left: 3px solid transparent;
  border-radius: 50%;
  transform: rotate(32deg);
}

.tap-tile__flash {
  width: 2.1rem;
  height: 2.8rem;
  background: var(--white);
  clip-path: polygon(48% 0%, 100% 0%, 62% 42%, 100% 42%, 26% 100%, 40% 56%, 0% 56%);
}

.tap-bottomline {
  display: grid;
  gap: 0.75rem;
}

.tap-bottomline__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.85rem;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-soft);
}

.tap-result {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border: 2px solid var(--black);
  background: var(--white);
}

.tap-result__copy {
  display: grid;
  gap: 0.5rem;
}

.tap-leaderboard__header {
  display: grid;
  gap: 0.9rem;
}

.tap-leaderboard__tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tap-leaderboard__loading {
  font-size: 0.82rem;
  color: var(--text-soft);
}

.tap-leaderboard__list {
  display: grid;
  gap: 0.65rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.tap-leaderboard__item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.85rem;
  border: 2px solid var(--black);
  background: var(--white);
}

.tap-leaderboard__rank,
.tap-leaderboard__score {
  display: grid;
  gap: 0.15rem;
}

.tap-leaderboard__rank {
  min-width: 3rem;
  font-weight: 800;
}

.tap-leaderboard__identity {
  display: grid;
  gap: 0.2rem;
}

.tap-leaderboard__identity strong,
.tap-leaderboard__score strong {
  font-size: 0.95rem;
}

.tap-leaderboard__identity span,
.tap-leaderboard__score span {
  font-size: 0.72rem;
  line-height: 1.45;
  color: var(--text-soft);
}

@media (min-width: 980px) {
  .tap-header {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }

  .tap-layout {
    grid-template-columns: minmax(0, 1.2fr) minmax(18rem, 24rem);
    align-items: start;
  }
}

@media (max-width: 767px) {
  .tap-arena,
  .tap-leaderboard {
    padding: 0.9rem;
  }

  .tap-arena__topline {
    gap: 0.5rem;
  }

  .tap-metric {
    padding: 0.65rem;
  }

  .tap-metric strong {
    font-size: 1.15rem;
  }

  .tap-tile {
    min-height: 4.9rem;
  }
}
</style>
