# Santa Frontend

AI-generated Christmas greeting cards with Vue.js 3 and festive UI.

## Tech Stack

- **Framework**: Vue.js 3 (Composition API with `<script setup>`)
- **Build Tool**: Vite 5
- **UI Library**: PrimeVue (Aura theme)
- **CSS Framework**: Tailwind CSS + daisyUI (winter/night themes)
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **Effects**:
  - tsParticles (snow animation)
  - @vueuse/motion (animations)
  - vue3-carousel (carousels)
  - Glassmorphism effects
- **HTTP Client**: Axios
- **TypeScript**: Full type safety

## Project Structure

```
frontend/
├── src/
│   ├── api/                  # API client
│   │   └── client.ts         # Axios HTTP client with endpoints
│   ├── assets/
│   │   └── styles/
│   │       └── main.css      # Global styles + Christmas theme
│   ├── components/           # Vue components
│   │   ├── CardForm.vue      # Card generation form
│   │   ├── GenerationPreview.vue  # Preview with carousels
│   │   ├── GlassCard.vue     # Glassmorphism card wrapper
│   │   ├── ImageCarousel.vue # Image variants carousel
│   │   ├── SnowBackground.vue # tsParticles snow effect
│   │   └── TextCarousel.vue  # Text variants carousel
│   ├── composables/          # Composable functions
│   │   └── useParticles.ts   # Snow particle configuration
│   ├── router/               # Vue Router
│   │   └── index.ts          # Route definitions
│   ├── stores/               # Pinia stores
│   │   └── card.ts           # Card generation state
│   ├── types/                # TypeScript types
│   │   └── index.ts          # All type definitions
│   ├── views/                # Page views
│   │   ├── HomeView.vue      # Main page (form + preview)
│   │   └── SuccessView.vue   # Success screen
│   ├── App.vue               # Root component
│   └── main.ts               # App entry point
├── Dockerfile                # Multi-stage Docker build
├── nginx.conf                # Nginx configuration
├── index.html                # HTML entry point
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind + daisyUI config
└── package.json              # Dependencies

```

## Features

### 1. Christmas Theme
- **Colors**: Red (#DC2626), Green (#16A34A), Gold (#F59E0B)
- **Background**: Dark gradient (winter night)
- **Effects**: Falling snow particles, glassmorphism cards
- **Animations**: Twinkle, snow-fall

### 2. Card Generation Flow
1. **Form** (CardForm.vue):
   - Recipient selection (autocomplete from employees)
   - Optional sender, reason, message fields
   - Text enhancement toggle with 5 style options
   - Image style selection (4 options)

2. **Preview** (GenerationPreview.vue):
   - Text carousel with selection
   - Image carousel with selection
   - Regenerate buttons (3 regenerations max)
   - Send to Telegram button

3. **Success** (SuccessView.vue):
   - Animated success screen
   - Auto-redirect to home after 5 seconds

### 3. State Management (Pinia)
Store: `useCardStore()`
- **State**: generation ID, variants, selections, counters
- **Actions**: generate, regenerateText, regenerateImage, send, reset
- **Computed**: hasGeneration, canRegenerate, canSend

### 4. API Integration
Base URL: `/api/v1` (proxied to backend in dev mode)

Endpoints:
- `POST /cards/generate` - Generate card
- `POST /cards/regenerate` - Regenerate variant
- `POST /cards/send` - Send to Telegram
- `GET /employees` - Get employee list

## Development

### Prerequisites
- Node.js 20+
- npm or yarn

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

Access: http://localhost:3000

### Build for Production
```bash
npm run build
```

### Type Check
```bash
npm run type-check
```

## Docker

### Build Image
```bash
docker build -t santa-frontend .
```

### Run Container
```bash
docker run -p 3000:80 santa-frontend
```

## Environment Variables

Create `.env` file from `.env.example`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

In production (Docker), API requests are proxied through nginx to backend service.

## Styling

### Tailwind Classes
- `christmas-red`, `christmas-green`, `christmas-gold` - Theme colors
- `winter-bg-primary`, `winter-bg-secondary` - Background colors
- `winter-snow` - Snow white text color
- `glass-card` - Glassmorphism effect

### daisyUI Themes
- `winter` - Light theme (default)
- `night` - Dark theme

### Custom Animations
- `animate-snow-fall` - Falling snow animation
- `animate-twinkle` - Twinkling effect

## Components

### SnowBackground.vue
tsParticles configuration:
- 100 white particles
- Falling downward with wobble
- Transparent background

### GlassCard.vue
Reusable glassmorphism card:
- `background: rgba(255, 255, 255, 0.1)`
- `backdrop-filter: blur(10px)`
- `border: 1px solid rgba(255, 255, 255, 0.2)`

### CardForm.vue
Form with validation:
- PrimeVue AutoComplete for recipient
- Text inputs with character limits
- Radio buttons for style selection
- Loading state during generation

### TextCarousel.vue / ImageCarousel.vue
vue3-carousel implementation:
- Navigate between variants
- Selection radio buttons
- Regenerate with style selector
- Remaining regenerations counter

## Type Safety

All components use TypeScript with strict mode:
- Proper type definitions in `types/index.ts`
- No `any` types
- Full IntelliSense support

## Performance

- **Lazy Loading**: SuccessView loaded on demand
- **Code Splitting**: Vite automatic code splitting
- **Image Optimization**: Lazy loading images
- **Caching**: nginx caches static assets (1 year)
- **Gzip**: Enabled for text assets

## Browser Support

- Modern browsers (ES2020+)
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## Russian UI

All UI text is in Russian:
- Form labels and placeholders
- Button text
- Error messages
- Success messages

## License

Private project for internal use.
