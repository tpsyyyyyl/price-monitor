# HANDOFF — Фаза 2 / Price Monitor (де саме зупинились)

> Стан на **2026-06-12**, кінець сесії.
> Це точка відновлення: відкрий цей файл у новій сесії — і продовжуй рівно звідси.
> Вікно безкоштовного Fable 5 діє **до 22.06.2026**.

## Статус: ✅ все зроблено, закомічено, запушено, задеплоєно
Робоче дерево чисте, нічого незакоміченого немає. 4 коміти на master, CI зелений.

## Проєкт
- **Smart Price Monitor** — Проєкт 2 Фази 2 (Portfolio Sprint): трекер цін з AI-інсайтами.
- Стек: FastAPI + SQLAlchemy 2 + Alembic (SQLite, Postgres-ready) · httpx + BeautifulSoup (адаптери: books.toscrape.com, scrapeme.live) · APScheduler (daily cron 06:00) · Telegram-алерти >5% (вимкнені без токена) · Groq `gpt-oss-120b` + евристичний fallback · React 19 + Vite + Tailwind 4 + Recharts · demo-login JWT · CSV-експорт.
- Директорія: `/home/bohdan/study/price-monitor/`
- venv: `.venv/` усередині репо (не спільний з landing-studio!)
- GitHub: `tpsyyyyyl/price-monitor` (публічний)
- **Live:** https://price-monitor-bohdan.fly.dev (Fly.io, регіон fra, app `price-monitor-bohdan`)
- Мова відповідей: **тільки українська**.

## Ключові команди
```bash
cd /home/bohdan/study/price-monitor
.venv/bin/python -m pytest tests/ -q        # 19 passed
cd frontend && npm run build                 # ✓ built
~/.fly/bin/fly deploy --ha=false             # деплой (fly НЕ в PATH — лежить у ~/.fly/bin/)
~/.fly/bin/fly logs -a price-monitor-bohdan  # логи проду
```
Секрети на Fly вже виставлені: `GROQ_API_KEY` (той самий ключ, що в landing-studio), `JWT_SECRET` (згенерований). `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` — НЕ виставлені, алерти йдуть у лог (це задокументовано в README).

## Що зробили в цій сесії
1. **Полір landing-studio:** перевірили live demo (ok), GitHub-репо отримало description + homepage + 8 topics (було порожньо).
2. **Збудували price-monitor з нуля** (4 субагенти на Opus, Fable — оркестратор):
   - каркас + моделі (products, price_points, users) + alembic + скрапер з адаптерами + 9 тестів;
   - API (products CRUD, history, CSV, scrape з jitter, insight) + demo-auth + scheduler + notify + seed (5 товарів × 21 день) + 10 тестів;
   - фронтенд: Dashboard (таблиця, badges, Scrape now / Simulate change), ProductDetail (графік + AI insight), стиль успадковано з landing-studio;
   - README зі скрінами (puppeteer-core проти live-сайту), CI, GitHub repo + topics.
3. **Деплой:** app + volume + секрети + `fly deploy`, верифіковано наживо (insight приходить із `source:"ai"`).
4. **Оновили `~/.claude/CLAUDE.md` розділ 5:** делегування на дешевші моделі тепер обовʼязковий дефолт (скарга з /usage від 2026-06-12).

## Відомі межі (свідомі рішення, є в README)
- Fly auto-stop (`min_machines_running=0`) → daily cron спить разом з машиною. Для демо ок («Scrape now» покриває). Якщо треба справжній щоденний скрейп — `min_machines_running = 1` у fly.toml.
- Дані — один спільний demo-workspace (без реєстрації). Auth-скіли вже показані в landing-studio.
- Кнопка «Simulate change» = jitter ±2-8% — демо-фіча, щоб графіки і алерти було видно одразу.

## Наступні кроки Фази 2 (план: «Фаза 2 - Portfolio Sprint» в Obsidian)
1. **Проєкт 3: AI Content Assistant Bot** — Telegram-бот (генерація контенту / переклад / summary), ~10-12 год. Рішення: Groq замість Claude/DALL-E (узгоджено 2026-06-12). Нове репо `/home/bohdan/study/content-bot` (або схожа назва).
2. **Portfolio website** (~4-6 год) — після проєктів; уже є 2 живих проєкти для нього.
3. **GitHub profile README** + 3 pinned repos; чернетки Upwork/Fiverr (шаблони в Obsidian: «Шаблон портфоліо», «Шаблони proposals»).
4. Опційно: GIF-демо генерації для README landing-studio.

## Контекст для нової сесії
- Повна нотатка сесії: `/home/bohdan/Im clown/2026-06-12 - Старт Фази 2, Smart Price Monitor.md`
- Постійна память Claude: фази/рішення збережені (phase-2-portfolio-sprint), MCP Memory-сервер не підключений — не шукай його.
- MCP filesystem дозволяє писати лише в `/home/bohdan/study/landing-studio` — для інших шляхів звичайний Write.
