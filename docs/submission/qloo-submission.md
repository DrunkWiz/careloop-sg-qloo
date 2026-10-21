# CareLoop — Qloo Agentic Hackathon Submission Text

**Tagline:** Quiet between doctor visits. Thoughtful on the days that need a lift — planning good, health-safe days around the food, music, films, and local places each senior is fond of, powered by Qloo Taste AI.

---

## 1. What CareLoop Does

**CareLoop SG** supports older adults in Singapore living with chronic conditions like high blood pressure and type 2 diabetes between clinic visits.

Most days, CareLoop stays out of the way: a three-button voice/tap morning check-in for the senior (English, Singlish, Mandarin, Malay, Tamil), deterministic clinical escalation rules when blood pressure drifts or a red-flag symptom appears, and one-tap coordination for family caregivers or Active Ageing Centre (AAC) staff.

On the days between—especially when CareLoop notices a senior moving less, staying in, or feeling low—generic wellness advice (*"go for a walk"*, *"eat healthy"*, *"listen to relaxing music"*) falls flat or is actively unsafe. **CareLoop adds a Qloo-powered Taste Agent** that plans culturally specific, health-safe days around what *this* senior is genuinely fond of:
- **Cross-domain taste discovery via Qloo:** From a few personal seeds (e.g., *Teresa Teng*, *P. Ramlee*, *Teochew fish porridge*, *The Love Eterne*), CareLoop queries Qloo's taste graph (`/search` and `/v2/insights`) across **`urn:entity:place`**, **`urn:entity:artist`**, and **`urn:entity:movie`** in Singapore to connect a senior's favourite 1960s–70s singers and films to nearby kopitiams, hawker stalls, tea corners, and community programmes.
- **Deterministic health, medicine-leaflet, and weather guardrails:** Every Qloo candidate is filtered through reviewable, non-LLM constraint tables (`backend/taste/constraints.py`, marked `PLACEHOLDER` pending clinical sign-off) and live Singapore weather/haze data:
  - **Hypertension:** Filters out high-sodium preserved dishes (`Old Street Salted Fish Claypot Rice`) and highlights lower-salt steamed/clear-soup options.
  - **Medicine leaflet checks:** Blocks grapefruit/pomelo dishes (`Ah Chew Desserts — Mango Pomelo Sago`) for seniors taking **amlodipine** (`med_amlodipine`).
  - **Type 2 diabetes:** Filters out heavy syrup drinks (`Kampung Syrup Bandung`) and prefers unsweetened or *siew dai* options.
  - **Live rain & haze (data.gov.sg):** When PSI > 100 or rain >= 5 mm, outdoor parks (`Bishan-Ang Mo Kio Park`, `East Coast Park`) are automatically filtered out and only sheltered/indoor places are offered.
- **Visible agent reasoning & senior control:** Both the senior (`How CareLoop picked this`) and family/centre staff (`How this was picked` + `Why Qloo?`) see the exact 4-step tool trace and which candidates were filtered out for health or weather. Every taste seed appears in the senior's **What CareLoop knows about me** screen with a one-tap **Erase** button, and tapping **Not for me** permanently hides a suggestion.

---

## 2. What Makes CareLoop Qloo-Powered (Why an LLM Alone Isn't Enough)

Qloo's core rule is: *if it would work the same without Qloo, it's the wrong thing.*

Without Qloo, a prompt-only LLM asked to plan a day for a 74-year-old in Toa Payoh with hypertension produces generic, ungrounded text (*"Take a walk in Bishan Park, eat a light hawker meal or mango pomelo sago, and listen to relaxing Chinese music"*). As shown in our side-by-side comparison (`docs/qloo-comparison.md` and the in-app **Why Qloo?** panel), that baseline fails in three ways:
1. **No cross-domain entity graph:** An LLM prompt does not resolve *Teresa Teng* (`urn:entity:artist:teresa-teng`) and *The Love Eterne* (`urn:entity:movie:love-eterne`) into structured Qloo entity IDs and affinity-scored Singapore venues (`qloo-tp-teochew-porridge`, 95% affinity) or companion artists (`Fong Fei-Fei`, 95% affinity).
2. **Unsafe for medications and weather:** A single-shot LLM prompt suggests mango pomelo sago to a senior on amlodipine and outdoor park walks during PSI 112 haze.
3. **No structured candidate attributes for deterministic filtering:** Because CareLoop's Qloo agent retrieves structured candidates with dietary/venue tags first and passes them through deterministic Python rules second, medical and weather constraints are enforced 100% of the time—never left to an LLM's judgement.

---

## 3. Agentic Architecture (4-Step Tool Loop & Strict Safety Boundary)

CareLoop's Qloo agent (`backend/taste/agent.py`) operates strictly at the **suggestion layer**. It never chooses an escalation rung (`0`–`4` or `R`), never decides whom to contact, and never touches red-flag emergency handling.

For each senior and day, `build_taste_plan()` executes a 4-step tool pipeline recorded in `trace`:
1. **Tool 1 — `qloo_search` (`backend/taste/client.py`):** Resolves the senior's saved `likes` and cultural seeds (plus any favourites added by family or AAC staff via `GET /taste/search` and `POST /senior/{id}/taste`) against Qloo's `/search` endpoint into canonical `entity_id`s.
2. **Tool 2 — `qloo_insights` (`backend/taste/client.py`):** Queries Qloo's `/v2/insights` across three entity domains (`urn:entity:place`, `urn:entity:artist`, `urn:entity:movie`) conditioned on `signal.interests.entities`, `signal.interests.tags`, and `filter.location.query="Singapore"` (plus the senior's Singapore region: `central`, `west`, `east`).
3. **Tool 3 — `check_health_constraints` (`backend/taste/constraints.py`):** Evaluates every Qloo candidate against deterministic condition rules (`cond_hypertension`, `cond_diabetes`), medicine-leaflet rules (`med_amlodipine`, `med_losartan`, `med_metformin`), live NEA rain/PSI (`weather_indoor_only`), and the senior's `hidden_suggestions`. Keeps both `kept_places` and an explicit `filtered_out` audit log.
4. **Tool 4 — `guardrail_check` (`backend/language/guardrail.py`):** Runs every outgoing "why it fits" explanation string (English and Chinese) through CareLoop's language safety guardrail (blocking diagnoses, dose advice, invented numbers, and outdoor prompts during unhealthy haze).

**Graceful fallback:** When `QLOO_API_KEY` is set in the environment, `QlooClient` calls `https://hackathon.api.qloo.com` (`/search` and `/v2/insights`) with `X-Api-Key` and in-memory caching. When `QLOO_API_KEY` is unset (such as in CI/unit tests) or if Qloo is unreachable/rate-limited, `QlooClient` automatically falls back to `FixtureQlooClient` (`backend/taste/fixtures/qloo_fixtures.json`) so the app and all 237 offline unit tests never crash.

---

## 4. How Judges Can Try CareLoop End-to-End

1. **Open the Family Caregiver App (`/care/family?demo=1`):**
   - Tap the **Activities** tab for **Mr Tan**.
   - View **Suggested to Mr Tan today** (combining his AAC timetable, top health-safe Qloo place pick, and nearest Community Club).
   - Inspect the **CareLoop + Qloo taste graph for Mr Tan** card showing cross-domain picks across **Food & Place**, **Music**, and **Classic Film** with Qloo affinity scores and health badges (`Low-sodium options`, `No grapefruit/pomelo (amlodipine)`).
   - Expand **"How this was picked (Qloo agent steps & health guardrails)"** to inspect all 4 tool steps (`qloo_search`, `qloo_insights`, `check_health_constraints`, `guardrail_check`) and see why *Ah Chew Desserts — Mango Pomelo Sago* and *Old Street Salted Fish Claypot Rice* were filtered out.
   - Expand **"Add a favourite for Mr Tan (via Qloo search)"** to search Qloo entities (e.g. `Frances Yip` or `P. Ramlee`) and add a seed live.
   - Expand **"Why Qloo? (LLM-only baseline vs CareLoop + Qloo)"** to compare prompt-only LLM output against CareLoop + Qloo.
2. **Open the Senior App (`/senior`):**
   - See the big-text daily check-in and **Something you might enjoy** card (available in English, Singlish, 中文, Melayu, and தமிழ்).
   - Expand **How CareLoop picked this** to see the Qloo music & classic film picks and what was filtered out for health/weather.
   - Tap **What CareLoop knows about me** to see the Qloo taste seeds (`Enjoys music by Teresa Teng (CareLoop taste profile)`) and tap **Erase** on any seed to remove it immediately.
3. **Open CareLoop for Centres (`/care/aac?demo=1`):**
   - Click **Programmes** in the top bar to see the weekly AAC timetable (`Suits Mr Goh (walking)`, `Suits Mdm Lee (crafts)`) and the **CareLoop + Qloo taste matches across your seniors** summary card.
   - Click any senior in the caseload (e.g. **Mr Chandran** or **Mr Ng**) to inspect their Qloo taste plan in the right-hand sidebar.
