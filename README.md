# 🏠 SIT Bolig-Varsler

En automatisert overvåker for SIT (Studentsamskipnaden i Trondheim) som varsler deg på telefonen med en gang drømmeboligen blir ledig. 

Scriptet snakker direkte med SIT sitt GraphQL-API i bakgrunnen, noe som gjør det både raskere og mer pålitelig enn vanlig web-scraping.

## ✨ Funksjoner
* **API-sniffing:** Overvåker sanntidsdata direkte fra SITs Azure-backend.
* **Smarte filtre:** Filtrer på boligtype (f.eks. 3-roms, dublett), maks dato og lokasjon via `config.toml`.
* **Push-varsling:** Sender umiddelbare varsler til mobilen via **Pushover**.
* **State-tracking:** Husker hvilken bolig som var sist sett for å unngå dupliserte varsler.
* **Headless-modus:** Kjører lydløst i bakgrunnen (bruker Chromium via Playwright).

---

## 🛠 Installasjon

1. **Klone/Last ned prosjektet:**
   ```bash
   git clone <din-url>
   cd sit-bolig-varsler
   ```

2. **Sett opp virtuelt miljø (anbefalt):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # eller: venv\Scripts\activate  # Windows
   ```

3. **Installer avhengigheter:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

---

## ⚙️ Konfigurasjon

### 1. `.env` (Hemmeligheter)
Opprett en fil kalt `.env` i rotmappen og legg til dine Pushover-nøkler:
```ini
PUSHOVER_USER_KEY=ditt_user_key_her
PUSHOVER_APP_TOKEN=ditt_app_token_her
```

### 2. `config.toml` (Innstillinger)
Rediger `config.toml` for å sette dine preferanser:
```toml
[scraping]
base_delay = 120           # Minimum sekunder mellom sjekk
random_delay_max = 60      # Maks tilfeldig tilleggstid (for å unngå bot-deteksjon)

[filters]
showAll = false
maxAvailableDate = "2026-08-01"
housingType = ["3-roms", "2-roms", "2rompar"]  # Tom liste [] betyr alle typer
```

---

## 🚀 Bruk

### Test varslingen
Sjekk at koblingen til Pushover fungerer:
```bash
sit-bolig-varsler --test-alert
```

### List ut tilgjengelige boliger
Se hva som matcher filtrene dine akkurat nå:
```bash
sit-bolig-varsler --list-all
```

### Start overvåking (Aktiv modus)
Kjør denne for å la scriptet stå og gå i bakgrunnen med varsling aktivert:
```bash
sit-bolig-varsler --activate-alert
```

### Debugging
Hvis noe ikke fungerer, kjør med debug-flagg for å se hva API-et svarer:
```bash
sit-bolig-varsler --list-all --debug
```

---

## ⚠️ Ansvarsfraskrivelse
Dette verktøyet er laget for personlig bruk. Pass på at du ikke setter `base_delay` for lavt, da dette kan føre til at IP-adressen din blir blokkert av SITs sikkerhetssystemer. Vær en snill robot! 🤖

