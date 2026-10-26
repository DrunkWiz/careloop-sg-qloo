# CareLoop — Qloo Agentic Hackathon Submission Text

**Tagline:** Quiet between doctor visits. Thoughtful on the days that need a lift — planning good, health-safe days around the food, music, films, and local places each senior is fond of, powered by Qloo Taste AI.

- **Live Hosted App:** `https://careloop-sg-qloo.onrender.com`
- **Judge Command Center (Split-Screen):** `https://careloop-sg-qloo.onrender.com/pitch`
- **Demo Video (6m 26s 1080p MP4):** `https://careloop-sg-qloo.onrender.com/careloop-qloo-launch-video.mp4` (local: `docs/submission/careloop-qloo-launch-video.mp4`)
- **38-Persona Qloo Ablation Benchmark:** `https://careloop-sg-qloo.onrender.com/eval/taste`
- **Open-Source License:** `AGPL-3.0` (`LICENSE`)

---

## 1. What CareLoop Does

**CareLoop SG** supports older adults in Singapore living with chronic conditions like high blood pressure, type 2 diabetes, gout, and chronic kidney disease between clinic visits.

Most days, CareLoop stays out of the way: a three-button voice/tap morning check-in for the senior (English, Singlish, Mandarin, Malay, Tamil), deterministic clinical escalation rules when blood pressure drifts or a red-flag symptom appears, and one-tap coordination for family caregivers or Active Ageing Centre (AAC) staff.

On the days between—especially when CareLoop notices a senior moving less, staying in, or feeling low—generic wellness advice (*"go for a walk"*, *"eat healthy"*, *"listen to relaxing music"*) falls flat or is actively unsafe. **CareLoop adds a Qloo-powered Taste Agent** that plans culturally specific, health-safe days around what *this* senior is genuinely fond of:
- **Cross-domain taste discovery via Qloo:** From a few personal seeds (e.g., *Teresa Teng*, *P. Ramlee*, *Carnatic classical*, *Teochew fish porridge*, *The Love Eterne*), CareLoop queries Qloo's taste graph (`https://hackathon.api.qloo.com` via `/search` and `/v2/insights`) across **`urn:entity:place`**, **`urn:entity:artist`**, and **`urn:entity:movie`** in Singapore to connect a senior's favourite 1960s–70s singers and films to nearby kopitiams, hawker stalls, tea corners, and community programmes.
- **Deterministic clinical, pharmacist-leaflet, religious, mobility, and weather guardrails:** Every Qloo candidate is filtered through reviewable, non-LLM constraint tables (`backend/taste/constraints.py`, marked `PLACEHOLDER` pending clinical/pharmacist sign-off) and live Singapore weather/haze data:
  - **Hypertension & CKD (`cond.hypertension`, `cond.ckd`):** Filters out high-sodium preserved dishes (`Old Street Salted Fish Claypot Rice`), heavy gravies, and herbal tonics; highlights steamed/clear-soup options.
  - **Medicine leaflet checks (`med.statin_grapefruit`, `med.raas_potassium`, `med.warfarin_vit_k`):** Blocks grapefruit/pomelo dishes (`Ah Chew Desserts — Mango Pomelo Sago`) for seniors taking **amlodipine**, **atorvastatin**, or **simvastatin**; avoids potassium salt substitutes on **losartan**; keeps leafy greens steady and filters concentrated herbal tonics on **warfarin**.
  - **Gout & Type 2 Diabetes (`cond.gout`, `cond.diabetes`):** Filters out high-purine organ/offal broths (`Song Fa Style Pepper & Organ Offal Bak Kut Teh`) and heavy syrup drinks (`Kampung Syrup Bandung`), preferring *kopi-O kosong / siew dai*.
  - **Religious & Mobility rules (`diet.halal`, `diet.vegetarian`, `diet.no_beef`, `cond.mobility_aid`):** Enforces Halal, vegetarian, no-beef, and step-free/wheelchair-accessible seated venue constraints.
  - **Live rain & haze (`env.indoor_only` via `data.gov.sg`):** When PSI > 100 or rain >= 5 mm, outdoor parks (`Bishan-Ang Mo Kio Park`, `Toa Payoh Town Park`) are automatically blocked and only sheltered/indoor places are offered.
- **Visible agent reasoning & senior control:** Both the senior (`How CareLoop picked this`) and family/centre staff (`How this was picked` + `Why Qloo?`) see the exact 4-step tool trace and which candidates were filtered out for health or weather. Every taste seed appears in the senior's **What CareLoop knows about me** screen with a one-tap **Erase** button, and tapping **Not for me** permanently hides a suggestion.

---

## 2. What Makes CareLoop Qloo-Powered (Quantitative Proof Across 38 Personas)

Qloo's core rule is: *if it would work the same without Qloo, it's the wrong thing.*

We built a reproducible **3-Architecture Quantitative Ablation Benchmark** (`GET /eval/taste`, `backend/eval/taste_eval.py`, UI at `/eval/taste`) evaluating **38 personas** (all 13 demo seniors + 25 synthetic held-out/tuning personas across English/Singlish, Mandarin, Malay, and Tamil):

| Architecture | Clinical / Leaflet / Haze Violation Rate | Cultural Specificity Score (0–100) | `guardrail.py` Pass Rate | Multilingual Coverage (`EN`/`ZH`/`MS`/`TA`) |
|---|---|---|---|---|
| **1. Generic LLM Baseline** (prompt-only, no Qloo) | **100.0%** *(38 / 38 unsafe)* | **19.0 / 100** | 0.0% | 36.8% |
| **2. Rule-Filtered LLM** (basic condition prompt, no Qloo entity graph) | **55.3%** *(21 / 38; misses leaflet/haze)* | **22.0 / 100** | 44.7% | 52.6% |
| **3. CareLoop + Qloo Taste AI** (`/search` + `/v2/insights` + deterministic rules + `guardrail.py`) | **0.0%** *(zero violations)* | **82.2 / 100** *(+63.2 pts vs LLM)* | **100.0%** | **100%** (4 languages) |

The two baselines are scripted stand-ins for an LLM (`backend/taste/baseline_llm.py`, `_rule_filtered_llm_simulation`), not live model runs. All 38 personas are synthetic.

Without Qloo:
1. **No cross-domain entity graph:** A prompt-only LLM cannot resolve *Teresa Teng* (`urn:entity:artist`) and *The Love Eterne* (`urn:entity:movie`) into structured Qloo entity IDs and affinity-scored Singapore venues (`Toa Payoh Central Teochew Fish Porridge`, 95% affinity) or companion artists (`Fong Fei-Fei`, 95% affinity).
2. **Unsafe for medications and weather:** Single-shot LLM prompts suggest mango pomelo sago to seniors on amlodipine/statins and outdoor park walks during PSI 135 haze.
3. **No structured candidate attributes for deterministic filtering:** Because CareLoop's Qloo agent retrieves structured candidates with dietary/venue tags first and passes them through deterministic Python rules second, medical and weather constraints are enforced 100% of the time—never left to an LLM's judgement.

---

## 3. Agentic Architecture (4-Step Tool Loop & 10 Integrated Workflows)

CareLoop's Qloo agent (`backend/taste/agent.py`) operates strictly at the **suggestion layer**. It never chooses an escalation rung (`0`–`4` or `R`), never decides whom to contact, and never touches red-flag emergency handling.

For each senior and day, `build_taste_plan()` executes a 4-step tool pipeline recorded in `trace`:
1. **Tool 1 — `qloo_search` (`backend/taste/client.py`):** Resolves the senior's saved `likes` and cultural seeds against Qloo's `/search` endpoint into canonical `entity_id`s and tag URNs.
2. **Tool 2 — `qloo_insights` (`backend/taste/client.py`):** Queries Qloo's `/v2/insights` across three entity domains (`urn:entity:place`, `urn:entity:artist`, `urn:entity:movie`) conditioned on `signal.interests.entities`, `signal.interests.tags`, `signal.demographics.age=55_and_older`, `feature.explainability=true`, and Singapore locality (`filter.location.query=Singapore` / `signal.location.query=Singapore`).
3. **Tool 3 — `check_health_constraints` (`backend/taste/constraints.py`):** Evaluates every Qloo candidate against deterministic condition rules, pharmacist-leaflet rules, religious/mobility preferences, live NEA rain/PSI (`env.indoor_only`), and the senior's `hidden_suggestions`. Keeps both `kept_places` and an explicit `filtered_out` audit log.
4. **Tool 4 — `guardrail_check` (`backend/escalation/guardrail.py`):** Runs every outgoing explanation string across all 4 languages through CareLoop's language safety guardrail (blocking diagnoses, dose advice, invented numbers, and outdoor prompts during unhealthy haze).

Beyond daily individual suggestions, CareLoop's Qloo Taste Agent powers **10 integrated workflows**:
1. **Check-In Voice/Text → Live Qloo Taste Extraction (`POST /checkin`):** Extracts cultural/food/music/activity mentions from the senior's daily check-in in English, Singlish, Mandarin, Malay, or Tamil, resolves them via `qloo.search`, and saves them to the senior's taste profile (with one-tap **Erase** in `/senior/{id}/knows`).
2. **Multi-Senior "Group Taste Intersection" & Caterer Matrix for AAC Centres (`GET /aac/{aac_id}/taste-group`):** Intersects the Qloo taste profiles of all linked seniors at an Active Ageing Centre, enforces the **strictest union of medical, medicine-leaflet, and weather guardrails**, generates a **Caterer Dietary Headcount Sheet**, and lets staff add any Qloo pick to the weekly AAC timetable in one click (`+ Add to Timetable`).
3. **"Kopi Kakis" Buddy & Micro-Circle Matcher (`GET /aac/{aac_id}/kopi-kakis` & `GET /senior/{id}/kopi-kakis`):** Computes pairwise Qloo cultural affinity across seniors at the same centre, applies union dietary/mobility constraints to pick a safe shared meeting spot, and generates a bilingual 2-sentence befriender introduction script.
4. **Intergenerational "Memory Lane" & Family Keepsake Book (`GET/POST /senior/{id}/memories`):** Uses Qloo nostalgia seeds (1960s–80s artists, Shaw Brothers/Cathay films, heritage hawker dishes) to generate daily reminiscence prompts in 4 languages (`EN`/`ZH`/`MS`/`TA`) and saves guardrail-checked family Memory Capsules.
5. **Caregiver Respite & Burnout Shield (`GET /senior/{id}/respite`):** Detects caregiver fatigue from rota streaks and Vent Space activity, matches a 3-hour respite window to a high-affinity Qloo AAC session the senior genuinely enjoys, assigns backup family cover, and formats a one-tap WhatsApp handover card.
6. **Rung-2 "Low Day" Cultural Nudge (`2.low_day`):** Enriches single-day low-movement nudges (`out.inputs["qloo_pick"]` and `low_day_nudge`) with a guardrail-verified Qloo place + nostalgic music companion without altering deterministic escalation rungs.
7. **Family Visit Kit (`visit_kit`):** Synthesises a safe takeaway treat, nostalgic music pick, classic film topic, and active safety summary into a one-tap WhatsApp share message.
8. **Helper & Hawker Kitchen Card (`kitchen_card`) + Doorstep Icebreaker (`doorstep_icebreaker`):** Produces a bilingual hawker ordering card (*kopi-O kosong / siew dai*, clear soup, leaflet exclusions) and a culturally grounded opener for AAC befrienders.
9. **Synchronized Split-Screen Judge Command Center (`/pitch` / `?judge=1`):** Places the mobile Senior Phone and Caregiver/AAC Intelligence Console side-by-side with 4 one-click judge scenarios and live Qloo telemetry.
10. **38-Persona Quantitative Qloo Ablation Dashboard (`/eval/taste`):** Interactive benchmark proving `0.0%` clinical violation rate and `82.2/100` cultural specificity across 38 personas.

**Graceful fallback:** When `QLOO_API_KEY` is set, `QlooClient` calls `https://hackathon.api.qloo.com` (`/search` and `/v2/insights`) with `X-Api-Key` and in-memory caching. When `QLOO_API_KEY` is unset (such as in CI/unit tests) or if Qloo is unreachable, `QlooClient` automatically falls back to `FixtureQlooClient` (`backend/taste/fixtures/qloo_fixtures.json`) so the app and all offline unit tests never fail.

---

## 4. How Judges Can Try CareLoop End-to-End in 90 Seconds

1. **Start at the Synchronized Judge Command Center (`/pitch`):**
   - Click through the **4 Judge Scenarios** in the top bar:
     - **Scenario 1 (Voice Check-In → Live Qloo Extraction):** Watch a morning check-in extract `"Teresa Teng"` and `"Teochew porridge"` into Qloo entity URNs across both the Senior Phone (left) and Caregiver Console (right).
     - **Scenario 2 (Clinical, Leaflet & Haze Guardrails):** Toggle `Atorvastatin` + `Gout` + `PSI 135 Haze` and inspect Step 3 of the trace intercepting `med.statin_grapefruit`, `cond.gout`, and `env.indoor_only`.
     - **Scenario 3 (4-Language Cultural Shift):** Switch live between **English/Singlish**, **华语**, **Bahasa Melayu** (Encik Rahman — *P. Ramlee*, *Bujang Lapok*, Halal + Diabetes), and **தமிழ்** (Mr Chandran — *Carnatic classical*, Vegetarian).
     - **Scenario 4 (AAC Cohort, Kopi Kakis & Respite):** Inspect the multi-senior AAC group planner, Kopi Kakis buddy matcher, Memory Lane keepsakes, and Caregiver Respite Shield.
2. **Inspect the 38-Persona Quantitative Ablation Benchmark (`/eval/taste`):**
   - Compare **Generic LLM (`100.0%` violations)** vs **Rule-Filtered LLM (`55.3%` violations)** vs **CareLoop + Qloo Taste AI (`0.0%` violations, `82.2` specificity)** and filter the 38-persona audit table by condition or language.
3. **Explore Individual Surfaces (`/care/family?demo=1`, `/senior`, `/care/aac?demo=1`):**
   - In `/senior`, tap **What CareLoop knows about me** to see Qloo taste seeds and memory capsules with one-tap **Erase**, or tap **Not for me** on any suggestion.
