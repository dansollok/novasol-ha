# Changelog

## [1.1.1] — 2026-05-24

### Added

- **Key-box code sensor** — `sensor.novasol_XXXXX_keybox_code` exposes the property's key-box code, read from the `/v1/property/{id}` endpoint. Updated every 24 hours alongside the other annual stats sensors.

---

## [1.1.0] — 2026-05-24

### Fixed

- **Annual / review sensors now reliable** — resolved the long-standing `key_figures redirected` error that kept the 24-hour sensors unavailable.

  The root cause was a three-part authentication problem with the Drupal-based `/novasol/api/` namespace:

  1. **Shared session discarded cookies.** The integration was using HA's shared `aiohttp` session (`async_get_clientsession`), which uses a `DummyCookieJar` that silently discards `Set-Cookie` headers. Switching to a dedicated `aiohttp.ClientSession()` with a private cookie jar fixes this.
  2. **Stale token restore skipped cookie setup.** On startup, `load_tokens()` only restored the JWT strings — it never re-authenticated with the server, so the Drupal-required cookies (`idToken`, `expiresAt`, etc.) were never present. The fix is to always call `authenticate()` on startup so the server populates the full cookie jar.
  3. **SSO bridge redirect was being blocked.** The `POST /awaze-owner-login` bridge (which establishes the Drupal `SSESS` session cookie) was called with `allow_redirects=False`. This stopped `aiohttp` before the server-side redirect chain completed, so the `SSESS` cookie was never written into the session. Removing the flag lets the full handshake finish.

  No configuration change or re-setup is needed — existing installations will pick up the fix automatically after a HA restart.

---

## [1.0.1] — 2026-04-30 *(superseded by 1.1.0)*

### Fixed

- **Annual / review sensors unavailable** — partial fix: added the `POST /awaze-owner-login` SSO bridge call before every key-figures request. This was necessary but not sufficient on its own; the remaining issues (shared session, startup cookie loss, redirect blocking) were resolved in 1.1.0.

---

## [1.0.0] — 2026-04-30

### Added

#### New sensors — current stay
- `current_guest` — name of the guest currently checked in (None when vacant)
- `current_checkout` — checkout date of the active stay
- `current_booking_nights` — length of the current stay in nights

#### New sensor — booking history
- `next_booking_booked_on` — date the next booking was originally placed

#### Annual performance sensors (updated every 24 hours)
Six new sensors sourced from the Novasol key-figures and reviews APIs:
- `annual_income` — total owner hire income for the current calendar year (DKK)
- `annual_guest_days` — total guest nights for the current calendar year
- `annual_electricity` — electricity cost charged to the owner this year (DKK)
- `annual_occupancy` — occupancy rate: guest days as a percentage of available days (%)
- `review_score` — overall Feefo guest review score (0–5)
- `review_count` — total number of guest reviews

#### Dual update cycle
A second `NovaSolStatsCoordinator` runs every 24 hours alongside the existing 6-hour booking coordinator. Booking sensors, the calendar, and the binary sensor are unaffected. Stats sensors degrade gracefully — if either the key-figures or reviews endpoint is unreachable, the affected sensors return `None` rather than making the whole integration unavailable.

### Changed
- Sensor entity list grows from 14 to 24 (plus the existing binary sensor).

---

## [0.99.4] — 2026-04-27

- Next booking detail sensors: nationality, country, party size, income.

## [0.99.0] — prior

- Initial release: calendar, occupancy binary sensor, next check-in/out dates, days until check-in, upcoming bookings count, YTD income, last-poll timestamp.
