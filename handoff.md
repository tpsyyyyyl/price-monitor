# HANDOFF — Фаза 2 / Price Monitor (де саме зупинились)

> Стан на **2026-06-13**, кінець сесії.
> Це точка відновлення: відкрий цей файл у новій сесії — і продовжуй рівно звідси.
> Вікно безкоштовного Fable 5 діє **до 22.06.2026**.

## Статус: ✅ все зроблено, закомічено, запушено, задеплоєно
Робоче дерево чисте. На master 10 комітів, CI зелений, прод оновлений (6 деплоїв за сесію 13.06).
Останній live-тест: `jabko.ua iPhone 17 Pro Max → 66699 UAH, HTTP 201`.

## Проєкт
- **Smart Price Monitor** — Проєкт 2 Фази 2. Тепер це **два режими в одному**:
  1. **Extract (головна, `/`)** — універсальний AI-екстрактор: встав БУДЬ-ЯКИЙ URL + опиши що знайти → список структурованих результатів. На картках із ціною є кнопка **«Track»** → одразу в трекер.
  2. **Tracker (`/tracker`)** — трекер цін, що працює з **будь-яким** URL (не лише 2 demo-сайти): знайомі сайти через адаптери, решта — AI читає назву+ціну.
- Стек: FastAPI + SQLAlchemy 2 + Alembic · httpx + BeautifulSoup · Groq `gpt-oss-120b` · APScheduler · Telegram-алерти · **React 19 + Vite + Tailwind 4 + three.js/react-three-fiber (3D particle wave) + Recharts** · demo-login JWT · CSV-експорт.
- Дизайн: повністю переробили з landing-studio → **futuristic dark + neon glass**, шрифти Exo + Roboto Mono, 3D particle-wave фон (рухається при скролі, інтенсивніше що більше результатів). Орби прибрані.
- Директорія: `/home/bohdan/study/price-monitor/` · venv: `.venv/` усередині репо.
- GitHub: `tpsyyyyyl/price-monitor` (публічний) · **Live:** https://price-monitor-bohdan.fly.dev (Fly.io, fra, app `price-monitor-bohdan`).
- Мова відповідей: **тільки українська**.

## Ключові команди
```bash
cd /home/bohdan/study/price-monitor
.venv/bin/python -m pytest tests/ -q          # 25 passed
cd frontend && npm run build                   # ✓ built
~/.fly/bin/fly deploy --ha=false               # деплой (fly у ~/.fly/bin/)
~/.fly/bin/fly logs -a price-monitor-bohdan --no-tail   # логи проду (для дебагу 422 тощо)
```
Секрети на Fly: `GROQ_API_KEY`, `JWT_SECRET` виставлені. `TELEGRAM_*` — ні (алерти в лог).
**Локально GROQ_API_KEY НЕМАЄ** (`.env` відсутній) → AI-фічі локально віддають `source:error`/422;
реальна перевірка AI — тільки на Fly. Не шукай ключ у landing-studio (це заблоковано класифікатором).

## Що зробили в цій сесії (13.06)
1. **Universal AI extractor** — `backend/extract.py` (`extract_from_url`, `_html_to_text`, `ai_scrape`, `_coerce_price`), `ai.extract_items` + `ai.extract_product_price`, роут `POST /api/extract`, сторінка `Extract.jsx`, `ResultCard.jsx`.
2. **Tracker для будь-якого URL** — `POST /api/products` має AI-fallback (UnsupportedSite → `ai_scrape`) + приймає `{name, price, currency}` для «Track this result»; `runner.run_all` оновлює AI-товари через AI.
3. **Редизайн + 3D** — `ParticleField.jsx` (three.js), нова тема в `index.css`, рестайл усіх сторінок, `.glass`/`.glass-strong`.
4. **Дебаг prod-only 422 на реальних магазинах** (jabko.ua) — три причини поспіль (див. память `groq-extraction-gotchas`): обрізка тексту їла нав-сміття → витяг **JSON-LD/meta ціни до strip-у** + ліміт 18k→40k; `parse_price` давився UAH/пробілами → `_coerce_price`; `max_tokens=256` < reasoning gpt-oss → 1024; валюта тепер реальна зі сторінки.
5. **Непрозорі панелі** (`.glass-strong`) над хвилею — таблиця трекера, форми, картки графіка/insight.
6. Оновили глобальний `~/.claude/CLAUDE.md` розділ 5: оркестратор = Fable 5 АБО Opus.

## Наступні кроки
- **Дрібниці (не зроблено, на твій розсуд):** прибрати no-op перемикач кольорових схем (3 крапки) у навбарі — орбів уже немає; оновити скріни в README під новий дизайн.
- **Проєкт 3 Фази 2: AI Content Assistant Bot** — Telegram-бот (генерація/переклад/summary) на Groq, ~10-12 год. Нове репо `/home/bohdan/study/content-bot`.
- Portfolio website (~4-6 год) · GitHub profile README + 3 pinned repos · чернетки Upwork/Fiverr.

## Контекст
- Нотатки сесій: `/home/bohdan/Im clown/2026-06-13 - Допил Price Monitor.md` (та 2026-06-12 — старт).
- Постійна память Claude: `/home/bohdan/.claude/projects/-home-bohdan-study-price-monitor/memory/`.
- MCP Memory-сервер НЕ підключений — не шукай.
