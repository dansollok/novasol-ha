# Novasol Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integrates the [Novasol](https://www.novasol.dk) owner portal into Home Assistant.  
Syncs your rental bookings as a calendar and exposes sensors for upcoming guests, occupancy, income, annual performance, and guest reviews — with no cloud dependency beyond the Novasol API itself.

> **No browser or Playwright required.** Authentication uses plain HTTP calls to the Novasol API, so the integration runs on every device including Raspberry Pi Zero.

---

## Features

- **Calendar entity** — all bookings visible in the HA calendar card, with guest name, nationality flag, party size, and owner income in the description
- **Sensors** — 24 entities across two update cycles:
  - *Every 6 hours:* next guest details, current stay, party composition, booking financials, occupancy, and integration health
  - *Every 24 hours:* annual income, guest days, electricity cost, occupancy rate, and Feefo review score
- **Binary sensor** — Occupancy (on when a guest is currently checked in, with guest details as attributes)
- **Automatic token refresh** — access tokens are refreshed silently every hour; if the refresh token expires the integration re-logs in automatically using your stored credentials
- **Multi-property support** — if your account has multiple properties, the config flow lets you pick which one to track

---

## Requirements

- Home Assistant 2024.1 or newer
- A Novasol owner portal account ([login.novasol.dk](https://login.novasol.dk))
- No extra Python packages — only `aiohttp`, which is already part of HA core

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/dansollok/novasol-ha` with category **Integration**
4. Search for **Novasol** and click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/novasol/` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Novasol**
3. Enter your Novasol owner portal email and password
4. If you have multiple properties, select the one to track
5. Done — entities will appear under a new **Novasol** device

---

## Entities

### Calendar

| Entity | Description |
|--------|-------------|
| `calendar.novasol_XXXXX_bookings` | All bookings — customer stays and owner blocks. Guest name, nationality flag, party size and income shown in the event description. |

### Sensors

#### Updated every 6 hours

| Entity | Description |
|--------|-------------|
| `sensor.novasol_XXXXX_next_checkin` | Date of next guest arrival |
| `sensor.novasol_XXXXX_next_checkout` | Date of next guest departure |
| `sensor.novasol_XXXXX_days_until_checkin` | Days until next arrival |
| `sensor.novasol_XXXXX_next_guest` | Full name of next guest |
| `sensor.novasol_XXXXX_next_guest_nationality` | Raw nationality code (e.g. `D`) |
| `sensor.novasol_XXXXX_next_guest_country` | Full country name (e.g. `Germany`) |
| `sensor.novasol_XXXXX_next_booking_nights` | Length of next stay in nights |
| `sensor.novasol_XXXXX_next_booking_adults` | Number of adults in next booking |
| `sensor.novasol_XXXXX_next_booking_children` | Number of children in next booking |
| `sensor.novasol_XXXXX_next_booking_pets` | Number of pets in next booking |
| `sensor.novasol_XXXXX_next_booking_income` | Owner income for the next booking (DKK) |
| `sensor.novasol_XXXXX_next_booking_booked_on` | Date the next booking was made |
| `sensor.novasol_XXXXX_current_guest` | Full name of the guest currently staying (None when vacant) |
| `sensor.novasol_XXXXX_current_checkout` | Checkout date of the current stay |
| `sensor.novasol_XXXXX_current_booking_nights` | Length of the current stay in nights |
| `sensor.novasol_XXXXX_upcoming_bookings` | Total number of future customer bookings |
| `sensor.novasol_XXXXX_ytd_income` | Owner income booked so far this year (DKK) |
| `sensor.novasol_XXXXX_last_successful_poll` | Timestamp of last successful data fetch — stops updating if the integration breaks |

#### Updated every 24 hours

| Entity | Description |
|--------|-------------|
| `sensor.novasol_XXXXX_annual_income` | Total owner hire income for the current calendar year (DKK) |
| `sensor.novasol_XXXXX_annual_guest_days` | Total guest nights for the current calendar year |
| `sensor.novasol_XXXXX_annual_electricity` | Electricity cost charged to owner for the current year (DKK) |
| `sensor.novasol_XXXXX_annual_occupancy` | Occupancy rate for the current year — guest days as a percentage of available days (%) |
| `sensor.novasol_XXXXX_review_score` | Overall Feefo guest review score (0–5) |
| `sensor.novasol_XXXXX_review_count` | Total number of guest reviews |

### Binary sensor

| Entity | Description |
|--------|-------------|
| `binary_sensor.novasol_XXXXX_occupied` | On when a guest is currently checked in. Attributes include guest name, check-in/out dates, and party size. |

---

## Troubleshooting

**Integration shows as unavailable after setup**  
Check that your Novasol credentials are correct. Try logging in at [login.novasol.dk](https://login.novasol.dk) to verify.

**Bookings not updating**  
The integration polls every 6 hours. To force a refresh go to Settings → Devices & Services → Novasol → three-dot menu → **Reload**.

**Income shows 0**  
Year-to-date income counts bookings made (booked-on date) in the current calendar year. Bookings placed last year for stays this year are not included.

**Annual / review sensors show as unavailable**  
These sensors update every 24 hours from a separate API namespace (`/novasol/api/`). If they stay unavailable after 24 hours, the portal's cookie-based authentication for that namespace may not be working yet. The booking sensors and calendar are not affected — they use the standard bearer-token API. Check the HA logs for `Failed to fetch key figures` or `Failed to fetch reviews` warnings.

**How do I verify the integration is running?**  
Check `sensor.novasol_XXXXX_last_successful_poll` — it updates every time data is fetched successfully. If it stops advancing, something is wrong. For detailed logs add this to `configuration.yaml` and restart:
```yaml
logger:
  default: warning
  logs:
    custom_components.novasol: debug
```

---

## License

MIT

---
---

# Novasol Home Assistant Integration *(Dansk)*

Integrerer [Novasol](https://www.novasol.dk) ejerportalen i Home Assistant.  
Synkroniserer dine udlejningsbookinger som en kalender og viser sensorer for kommende gæster, belægning, indtægt, årsstatistik og gæsteanmeldelser — uden ekstra cloudafhængigheder ud over Novasol API'et selv.

> **Ingen browser eller Playwright kræves.** Godkendelse sker via almindelige HTTP-kald til Novasol API'et, så integrationen kører på alle enheder inkl. Raspberry Pi Zero.

---

## Funktioner

- **Kalender-enhed** — alle bookinger synlige i HA kalender-kortet, med gæstenavn, nationalitetsflag, antal personer og ejerindtægt i beskrivelsen
- **Sensorer** — 24 entiteter fordelt på to opdateringscyklusser:
  - *Hvert 6. time:* næste gæsts detaljer, igangværende ophold, selskabsstørrelse, økonomi, belægning og integrationsstatus
  - *Hvert 24. time:* årsindtægt, gæstedage, elforbrug, belægningsprocent og Feefo-anmeldelsesscore
- **Binær sensor** — Belægning (tændt når en gæst er tjekket ind, med gæstedetaljer som attributter)
- **Automatisk token-fornyelse** — adgangstokens fornyes lydløst hver time; udløber refresh-token, logger integrationen automatisk ind igen med de gemte credentials
- **Understøttelse af flere ejendomme** — har din konto flere ejendomme, kan du vælge hvilken der skal synkroniseres under opsætningen

---

## Krav

- Home Assistant 2024.1 eller nyere
- En Novasol ejerkonto ([login.novasol.dk](https://login.novasol.dk))
- Ingen ekstra Python-pakker — bruger kun `aiohttp`, som allerede er en del af HA core

---

## Installation

### Via HACS (anbefalet)

1. Åbn HACS i Home Assistant
2. Gå til **Integrationer** → tre-prikker-menu → **Brugerdefinerede repositories**
3. Tilføj `https://github.com/dansollok/novasol-ha` med kategorien **Integration**
4. Søg efter **Novasol** og klik **Download**
5. Genstart Home Assistant

### Manuel

1. Kopiér mappen `custom_components/novasol/` til din HA `config/custom_components/`-mappe
2. Genstart Home Assistant

---

## Konfiguration

1. Gå til **Indstillinger → Enheder og tjenester → Tilføj integration**
2. Søg efter **Novasol**
3. Indtast din Novasol ejerportal-email og adgangskode
4. Har du flere ejendomme, vælg den der skal synkroniseres
5. Færdig — enheder vises under en ny **Novasol**-enhed

---

## Entiteter

### Kalender

| Entitet | Beskrivelse |
|---------|-------------|
| `calendar.novasol_XXXXX_bookings` | Alle bookinger — gæsteophold og ejerblokke. Gæstenavn, nationalitetsflag, antal personer og indtægt vises i begivenhedsbeskrivelsen. |

### Sensorer

#### Opdateres hvert 6. time

| Entitet | Beskrivelse |
|---------|-------------|
| `sensor.novasol_XXXXX_next_checkin` | Næste gæsts ankomstdato |
| `sensor.novasol_XXXXX_next_checkout` | Næste gæsts afrejsedato |
| `sensor.novasol_XXXXX_days_until_checkin` | Dage til næste ankomst |
| `sensor.novasol_XXXXX_next_guest` | Næste gæsts fulde navn |
| `sensor.novasol_XXXXX_next_guest_nationality` | Nationalitetskode (fx `D`) |
| `sensor.novasol_XXXXX_next_guest_country` | Fuldt landsnavn (fx `Germany`) |
| `sensor.novasol_XXXXX_next_booking_nights` | Antal nætter i næste booking |
| `sensor.novasol_XXXXX_next_booking_adults` | Antal voksne i næste booking |
| `sensor.novasol_XXXXX_next_booking_children` | Antal børn i næste booking |
| `sensor.novasol_XXXXX_next_booking_pets` | Antal kæledyr i næste booking |
| `sensor.novasol_XXXXX_next_booking_income` | Ejerindtægt for næste booking (DKK) |
| `sensor.novasol_XXXXX_next_booking_booked_on` | Dato for da næste booking blev foretaget |
| `sensor.novasol_XXXXX_current_guest` | Fuldt navn på gæst der opholder sig nu (None ved ledigt) |
| `sensor.novasol_XXXXX_current_checkout` | Afrejsedato for igangværende ophold |
| `sensor.novasol_XXXXX_current_booking_nights` | Antal nætter i igangværende ophold |
| `sensor.novasol_XXXXX_upcoming_bookings` | Antal kommende gæstebookinger |
| `sensor.novasol_XXXXX_ytd_income` | Årets ejerindtægt til dato (DKK) |
| `sensor.novasol_XXXXX_last_successful_poll` | Tidspunkt for seneste vellykkede datahentning |

#### Opdateres hvert 24. time

| Entitet | Beskrivelse |
|---------|-------------|
| `sensor.novasol_XXXXX_annual_income` | Samlet ejerindtægt for indeværende kalenderår (DKK) |
| `sensor.novasol_XXXXX_annual_guest_days` | Samlet antal gæstenætter for indeværende kalenderår |
| `sensor.novasol_XXXXX_annual_electricity` | Elforbrug debiteret ejer for indeværende år (DKK) |
| `sensor.novasol_XXXXX_annual_occupancy` | Belægningsprocent for indeværende år — gæstedage som andel af disponible dage (%) |
| `sensor.novasol_XXXXX_review_score` | Samlet Feefo-gæsteanmeldelsesscore (0–5) |
| `sensor.novasol_XXXXX_review_count` | Samlet antal gæsteanmeldelser |

### Binær sensor

| Entitet | Beskrivelse |
|---------|-------------|
| `binary_sensor.novasol_XXXXX_occupied` | Tændt når en gæst er tjekket ind. Attributter inkluderer gæstenavn, check-in/ud datoer og selskabsstørrelse. |

---

## Fejlfinding

**Integrationen vises som utilgængelig efter opsætning**  
Kontrollér at dine Novasol-credentials er korrekte. Prøv at logge ind på [login.novasol.dk](https://login.novasol.dk) for at bekræfte.

**Bookinger opdateres ikke**  
Integrationen henter data hvert 6. time. For at tvinge en opdatering: Indstillinger → Enheder og tjenester → Novasol → tre-prikker-menu → **Genindlæs**.

**Indtægt viser 0**  
Årets indtægt til dato tæller bookinger der er foretaget (bestillingsdato) i det aktuelle kalenderår. Bookinger foretaget sidste år med ophold i år tælles ikke med.

**Årsstatistik- og anmeldelsessensorer vises som utilgængelige**  
Disse sensorer opdateres hvert 24. time fra et separat API-navnerum (`/novasol/api/`). Forbliver de utilgængelige efter 24 timer, fungerer portalens cookie-baserede autentificering for dette navnerum muligvis ikke endnu. Booking-sensorerne og kalenderen er ikke berørt — de bruger det normale bearer-token API. Tjek HA-logs for advarslerne `Failed to fetch key figures` eller `Failed to fetch reviews`.

**Hvordan ved jeg om integrationen kører?**  
Tjek `sensor.novasol_XXXXX_last_successful_poll` — den opdateres hver gang data hentes. Hvis den holder op med at skifte, er der et problem. For detaljerede logs tilføj dette til `configuration.yaml` og genstart:
```yaml
logger:
  default: warning
  logs:
    custom_components.novasol: debug
```

---

## Licens

MIT
