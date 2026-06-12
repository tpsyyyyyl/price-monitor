import { pctChangeStyle } from '../format'

const SITE_LABEL = {
  books_toscrape: 'Books to Scrape',
  scrapeme: 'ScrapeMe',
}

export function PctBadge({ pct }) {
  const { className, arrow, label } = pctChangeStyle(pct)
  const title =
    pct === null || pct === undefined
      ? 'Not enough history yet'
      : pct < 0
        ? 'Price dropped since last check'
        : pct > 0
          ? 'Price rose since last check'
          : 'No change'
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${className}`}
    >
      <span aria-hidden>{arrow}</span>
      {pct === null || pct === undefined ? 'new' : label}
    </span>
  )
}

export function SiteBadge({ site }) {
  return (
    <span className="rounded-full bg-accent/15 px-2.5 py-0.5 text-xs font-medium text-accent-soft">
      {SITE_LABEL[site] ?? site}
    </span>
  )
}
