# Novasol Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integrates the [Novasol](https://www.novasol.dk) owner portal into Home Assistant.  
Syncs your rental bookings as a calendar and exposes sensors for upcoming guests, occupancy, and income — with no cloud dependency beyond the Novasol API itself.

> **No browser or Playwright required.** Authentication uses plain HTTP calls to the Novasol API, so the integration runs on every device including Raspberry Pi Zero.

---

## Features

- **Calendar entity** — all bookings visible in the HA calendar card, with guest name, nationality flag, party size, and owner income in the description
- **Sensors**
  - Next check-in date
  - Next check-out date
  - Days until next check-in
  - Next guest name
  - Upcoming bookings count
  - Year-to-date income (DKK)
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

| Entity | Type | Description |
|--------|------|-------------|
| `calendar.novasol_XXXXX_bookings` | Calendar | All bookings (customer + owner blocks) |
| `sensor.novasol_XXXXX_next_checkin` | Sensor | Date of next guest arrival |
| `sensor.novasol_XXXXX_next_checkout` | Sensor | Date of next guest departure |
| `sensor.novasol_XXXXX_days_until_checkin` | Sensor | Days until next arrival |
| `sensor.novasol_XXXXX_next_guest` | Sensor | Name of next guest |
| `sensor.novasol_XXXXX_upcoming_bookings` | Sensor | Number of future bookings |
| `sensor.novasol_XXXXX_ytd_income` | Sensor | Owner income this year (DKK) |
| `binary_sensor.novasol_XXXXX_occupied` | Binary sensor | On when a guest is checked in |

---

## Troubleshooting

**Integration shows as unavailable after setup**  
Check that your Novasol credentials are correct. Try logging in at [login.novasol.dk](https://login.novasol.dk) to verify.

**Bookings not updating**  
The integration polls every 6 hours. To force a refresh, go to Settings → Devices & Services → Novasol → three-dot menu → **Reload**.

**Income shows 0**  
Year-to-date income counts bookings made (booked-on date) in the current calendar year. Bookings made last year but staying this year are not included.

---

## License

MIT

---
---

# Novasol Home Assistant Integration *(Dansk)*

Integrerer [Novasol](https://www.novasol.dk) ejerportalen i Home Assistant.  
Synkroniserer dine udlejningsbookinger som en kalender og viser sensorer for kommende gæster, belægning og indtægt — uden ekstra cloudafhængigheder ud over Novasol API'et selv.

> **Ingen browser eller Playwright kræves.** Godkendelse sker via almindelige HTTP-kald til Novasol API'et, så integrationen kører på alle enheder inkl. Raspberry Pi Zero.

---

## Funktioner

- **Kalender-enhed** — alle bookinger synlige i HA kalender-kortet, med gæstenavn, nationalitetsflag, antal personer og ejerindtægt i beskrivelsen
- **Sensorer**
  - Næste check-in dato
  - Næste check-out dato
  - Dage til næste check-in
  - Næste gæsts navn
  - Antal kommende bookinger
  - Årets indtægt til dato (DKK)
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

## Fejlfinding

**Integrationen vises som utilgængelig efter opsætning**  
Kontrollér at dine Novasol-credentials er korrekte. Prøv at logge ind på [login.novasol.dk](https://login.novasol.dk) for at bekræfte.

**Bookinger opdateres ikke**  
Integrationen henter data hvert 6. time. For at tvinge en opdatering: Indstillinger → Enheder og tjenester → Novasol → tre-prikker-menu → **Genindlæs**.

**Indtægt viser 0**  
Årets indtægt til dato tæller bookinger der er foretaget (bestillingsdato) i det aktuelle kalenderår. Bookinger foretaget sidste år med ophold i år tælles ikke med.

---

## Licens

MIT
