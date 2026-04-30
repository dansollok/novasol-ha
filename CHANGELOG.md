# Changelog

## [1.0.1] — 2026-04-30

### Fixed

- **Annual / review sensors unavailable** — `GET /novasol/api/key_figures` was redirecting to the login page because the Drupal session had never been established. The client now calls the `GET /awaze-owner-login` SSO bridge (with the existing Bearer token) before every key-figures request, which sets the required server-side session cookie automatically. No configuration change needed.

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
