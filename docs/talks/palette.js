/* Palette at view time.
   Start from the viewer's own system setting — a phone in light mode gets the
   light deck — and let "t" override it for a projector that flatters neither.
   Marp scopes theme CSS under `section`, so the class goes on the slides
   themselves; nothing on <html> or <body> would reach those rules. */
(() => {
  const KEY = 'loop-deck-palette'
  const system = matchMedia('(prefers-color-scheme: light)')
  const stored = (() => { try { return localStorage.getItem(KEY) } catch (e) { return null } })()

  let mode = stored || (system.matches ? 'light' : 'dark')

  const paint = () => document.querySelectorAll('section').forEach(
    s => s.classList.toggle('lightmode', mode === 'light'))

  const set = (m) => {
    mode = m
    try { localStorage.setItem(KEY, m) } catch (e) { /* private window */ }
    paint()
  }

  // Bespoke builds the slides after this runs, so paint at every plausible
  // moment and keep painting whatever it adds later.
  paint()
  addEventListener('DOMContentLoaded', paint)
  addEventListener('load', paint)
  new MutationObserver(paint).observe(document.documentElement,
    { childList: true, subtree: true })

  // Until someone presses "t", the deck keeps following the system.
  system.addEventListener('change', e => { if (!stored) { mode = e.matches ? 'light' : 'dark'; paint() } })

  addEventListener('keydown', e => {
    if ((e.key === 't' || e.key === 'T') && !e.metaKey && !e.ctrlKey && !e.altKey)
      set(mode === 'light' ? 'dark' : 'light')
  })
})()
