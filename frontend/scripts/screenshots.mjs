// One-off helper: takes README screenshots against the live deployment.
// Usage: node scripts/screenshots.mjs
import puppeteer from 'puppeteer-core'

const BASE = 'https://price-monitor-bohdan.fly.dev'
const OUT = new URL('../../docs/', import.meta.url).pathname

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  args: ['--no-sandbox', '--hide-scrollbars'],
})
const page = await browser.newPage()
await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 })

async function shot(path, name, wait = 1200) {
  await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, wait))
  await page.screenshot({ path: `${OUT}${name}.png` })
  console.log(`saved ${name}.png`)
}

// login screen (dark theme is the default)
await shot('/login', 'login')

// log into the shared demo workspace, then authenticated pages
const session = await page.evaluate(async () => {
  const res = await fetch('/api/auth/demo', { method: 'POST' })
  return res.json()
})
await page.evaluate((s) => {
  localStorage.setItem('pm_token', s.token)
}, session)

await shot('/', 'dashboard')

// open the first product for the detail view (chart + AI insight)
const products = await page.evaluate(async () => {
  const res = await fetch('/api/products', {
    headers: { Authorization: `Bearer ${localStorage.getItem('pm_token')}` },
  })
  return res.json()
})
if (products.length) {
  // give the AI insight call extra time to resolve
  await shot(`/product/${products[0].id}`, 'product-detail', 4000)
}

await browser.close()
