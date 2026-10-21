# Synthetic User Research: 25-Persona Simulation & Pain-Point Audit

> **Honesty & Data Labeling Note (`CLAUDE.md` Rule):** All 25 user personas and journeys below are **synthetic simulations** created to stress-test CareLoop + Qloo Taste AI across diverse Singapore eldercare, clinical, cultural, religious, and linguistic contexts.

---

## 1. The 25 Synthetic Personas Tested

### Cohort A — Seniors Living Alone or Semi-Independently (9 Personas)
| # | Synthetic Persona | Age & Language | Clinical & Medicine Profile | Cultural / Taste Seeds | Simulated Pain Point Uncovered |
|---|---|---|---|---|---|
| 1 | **Mdm梁 (Mdm Liang)** | 78, Mandarin / Cantonese (`zh`) | Hypertension, Diabetes, Amlodipine 5mg, Metformin 500mg | Cantonese opera, Frances Yip, Teochew porridge | Wanted to tap **"I'm going"** on a suggestion, hear it read aloud, and immediately listen to her recommended Frances Yip song without typing. |
| 2 | **Mr陳 (Uncle Tan)** | 74, English / Hokkien (`en`) | Hypertension, Atorvastatin 20mg | Teresa Teng, kopitiam, tai chi, 70s Mandarin classics | Mentioned *"missed hearing Teresa Teng"* in his morning check-in, but had no confirmation that CareLoop remembered it on his *Knows* screen. |
| 3 | **Cik Siti Rahmah** | 71, Malay (`ms`) | Hypertension, Diabetes, Losartan | P. Ramlee, Saloma, Malay keroncong, nasi padang | Needed strict **Halal** filtering on Qloo food recommendations and native Bahasa Melayu (`ms`) explanations for why a place or song was picked. |
| 4 | **Mr Govindasamy** | 76, Tamil (`ta`) | Hypertension, Vegetarian (Hindu), Amlodipine | Carnatic classical, M.S. Subbulakshmi, thosai | Needed **Vegetarian / No-Beef** guardrails and native Tamil (`ta`) explanations on Qloo recommendations and medicine-food badges. |
| 5 | **Uncle Lim Ah Huat** | 80, Mandarin (`zh`) | **Gout**, Hypertension, Allopurinol 100mg, Losartan | Bak kut teh, Hokkien opera, morning walks | Qloo's raw taste graph matched him to organ-meat soup and rich broths from his love of bak kut teh — unsafe for gout / uric acid flares. |
| 6 | **Mdm Wong Mei Ling** | 82, Cantonese / Mandarin (`zh`) | **Atrial Fibrillation (on Warfarin)**, Hypertension | Herbal soups, green vegetable dishes, Cantonese opera | Needed a **Warfarin (consistent Vitamin K)** guardrail so sudden large leafy-green / concentrated herbal broth spikes are flagged. |
| 7 | **Uncle Salleh** | 77, Malay (`ms`) | **Stage 3 CKD (Renal)**, Hypertension, Diabetes |Soto, keroncong, Malay classic films | Needed **Renal / CKD (low potassium & low phosphate)** filtering and a medicine-food badge on his MyHealth screen. |
| 8 | **Mdm Koh Swee Neo** | 84, English / Peranakan (`en`) | **Wheelchair / Walker user (`mobility_aid`)**, Hypertension | Nyonya kuih, gentle gardening, Teresa Teng | Needed Qloo to filter out steep-walk or non-step-free venues and prioritise **wheelchair-accessible, seated** options. |
| 9 | **Mr Raju** | 73, English / Tamil (`en`) | Mild low-vision, Hypertension | 1960s Tamil cinema, kopi o kosong, chess | Struggled to type his favourites on a phone keyboard; needed **one-tap cultural seed chips** on the *What CareLoop Knows* screen and **Read-Aloud (TTS)** on suggestions. |

---

### Cohort B — Family Caregivers & Domestic Helpers (7 Personas)
| # | Synthetic Persona | Role | Scenario Simulated | Simulated Pain Point Uncovered |
|---|---|---|---|---|
| 10 | **grace (Daughter of Mdm Liang)** | Primary working daughter | Coordinating Sunday visit while checking 14-day timeline | Wanted the **Family Visit Kit** to know who is **On Duty** in the Family Rota today, and a one-click **`+ Add to Family To-Dos`** button so the visit kit doesn't get lost in WhatsApp. |
| 11 | **ben (Son of Mdm Liang)** | Secondary sibling | Checking why a Rung-2 `2.low_day` dot appeared on the timeline | Could see that CareLoop sent a gentle nudge on a low day, but couldn't see *which Qloo cultural nudge* was actually sent to his mum. |
| 12 | **marcus (Son of Mr Tan)** | Busy son stopping by a hawker centre | Buying dinner on the way to visit his dad | Knew his dad's Qloo food match (*Maxwell Teochew Fish Porridge*), but didn't know **how to order it safely** at the stall (*"less salt, clear soup, no gravy, kopi o kosong"*). |
| 13 | **Nurul (Daughter of Cik Siti)** | Daughter managing dietary tags | Updating her mother's religious and mobility requirements | Needed a one-click way in the Care view to toggle **Halal**, **Wheelchair / Step-Free**, or **Gout / Renal** tags and immediately see Qloo re-filter. |
| 14 | **Siti (Domestic Helper for Mdm Wong)** | Live-in helper cooking daily meals | Preparing lunch and buying groceries | Needed a copyable **Hawker & Home Kitchen Order Card** listing exact cooking tips and ingredients to avoid for Mdm Wong's medicines. |
| 15 | **Priya (Niece in Overseas Timezone)** | Remote family member | Reviewing a Rung-4 handover before calling her uncle | Wanted a **Doorstep / Call Cultural Icebreaker** on the Handover screen so she could open the call warmly with her uncle's favourite song or kopi order instead of sounding like an interrogation. |
| 16 | **David (Sandwich-Generation Caregiver)** | Caring for both parents | Testing rainy/hazy days for upcoming weekend | Wanted a **What-If Weather & Haze Simulator** (`Sunny`, `Downpour`, `Haze`) to see indoor backups ahead of time. |

---

### Cohort C — Active Ageing Centre (AAC) Staff & Befrienders (5 Personas)
| # | Synthetic Persona | Role | Scenario Simulated | Simulated Pain Point Uncovered |
|---|---|---|---|---|
| 17 | **mei (AAC Programme Coordinator)** | Runs weekly timetable at Peacehaven AAC | Reviewing the Qloo Group Taste Intersection Planner | Loved the cohort recommendations (*Group Refreshment*, *Sing-Along*, *Matinee Film*), but had to manually re-type them into the weekly timetable — wanted **`+ Add to Timetable`** in one click. |
| 18 | **Uncle Rahim (AAC Befriender Volunteer)** | Doing doorstep knocks for Rung-4 `no_contact` / `activity` handovers | Visiting a reluctant senior who hasn't replied | Needed the **Qloo Doorstep Icebreaker** right inside `HandoverView` so volunteers know what cultural touchpoint (e.g., Cantonese opera or Teresa Teng) opens the door. |
| 19 | **Sister Catherine (AAC Kitchen & Catering Lead)** | Ordering refreshments for 30 seniors | Planning Friday tea break | Needed a **Caterer & Kitchen Dietary Headcount Matrix** (`low_sodium: 2 pax`, `diabetic_friendly: 1 pax`, `grapefruit_free: 1 pax`, etc.) with a one-click copy sheet for the caterer. |
| 20 | **Kelvin (New Social Work Intern)** | Auditing why certain places were excluded | Inspecting cohort safety union | Needed transparent `filtered_out` reasons for gout, renal, wheelchair, and weather rules. |
| 21 | **Mdm Farah (Malay-Speaking Befriender)** | Supporting multi-ethnic seniors | Checking senior-facing app in `ms` and `ta` | Found that Qloo explanations previously fell back to English when switched to Malay (`ms`) or Tamil (`ta`). |

---

### Cohort D — Primary Care Clinicians & Hackathon Judges (4 Personas)
| # | Synthetic Persona | Role | Scenario Simulated | Simulated Pain Point Uncovered |
|---|---|---|---|---|
| 22 | **Dr Lim (Polyclinic GP)** | Reviewing the 1-page GP Brief PDF (`GET /senior/{sid}/brief.pdf`) | 8-minute polyclinic consult | Wanted the 1-page GP Brief to include **active dietary/medicine-food guardrails** and **14-day social engagement metrics** (`going` vs `not_for_me`) alongside BP and adherence. |
| 23 | **Community Pharmacist (NHG)** | Reviewing medicine cards with senior | Explaining Amlodipine, Atorvastatin, Warfarin, Allopurinol | Wanted the senior's **MyHealth** medicine screen to display a clear **Food & Drink Safety Badge** right on each interacting medication card. |
| 24 | **Hackathon Judge (Technical / AI Architecture)** | Evaluating Qloo API integration live | Testing dynamic context changes on the deployed app | Wanted an interactive **What-If Weather & Haze Simulator** (`Live NEA`, `Sunny`, `Downpour`, `Haze`) and live dietary guardrail toggles in the UI to verify Qloo re-ranking without running `curl`. |
| 25 | **AIC / MOH Eldercare Evaluator** | Reviewing safety boundaries | Auditing escalation vs suggestion separation | Verified that Qloo never alters Rung 0–4 / R escalation rules, and that every outgoing explanation string passes `guardrail.py`. |

---

## 2. How the 6 Feature Upgrades Resolve Every Pain Point

1. **Interactive "What-If Weather & Haze Simulator" + Live Dietary Guardrail Toggles (`ActivitiesView.tsx`, `/senior/{sid}/taste`, `/senior/{sid}/activities`)**
   - Caregivers and judges can toggle between **Live NEA**, **Sunny (PSI 45, 0mm)**, **Downpour (14mm)**, and **Haze (PSI 138)**, plus toggle **Halal**, **Vegetarian**, **No Beef**, **Gout**, **Renal / CKD**, and **Wheelchair / Step-Free** guardrails in real time.
2. **Expanded Clinical, Religious & Mobility Guardrails + Hawker/Home Kitchen Order Card + Medicine Leaflet Badges (`constraints.py`, `agent.py`, `medicines.py`, `MyHealth.tsx`)**
   - Added deterministic rules for `gout`, `chronic kidney disease`, `warfarin`, `mobility_aid`, `halal`, `vegetarian`, and `no_beef`.
   - Added `kitchen_card` to every senior's taste plan with copyable hawker ordering instructions (*"less salt, clear soup, kopi o kosong"*) and home-cooking tips.
   - Added `food_badge` and `food_note` to `MyHealth.tsx` medicine cards.
3. **Closed-Loop Senior Experience (`Home.tsx`, `Knows.tsx`, `SeniorApp.tsx`)**
   - Seniors can tap **"I'm going"** or **"Not for me"**, tap **"Read aloud"** (`speechSynthesis`), open **Listen / Watch / Map** links directly on Qloo picks, tap one-click favourite chips on **Knows**, and see a confirmation toast when a check-in extracts new cultural taste seeds.
4. **AAC One-Click Timetable Scheduling + Caterer Dietary Headcount Matrix + Doorstep Icebreaker (`AacProgrammes.tsx`, `HandoverView.tsx`)**
   - AAC staff can click **`+ Add to Timetable`** on any Qloo Group Taste recommendation and copy the **Caterer Dietary Headcount Matrix** (`catering_matrix`).
   - Family and AAC workers viewing a handover get a **Qloo Doorstep / Call Icebreaker** (`doorstep_icebreaker`) tailored to the senior's cultural seeds.
5. **Rota-Aware Family Visit Kit + One-Click "Add to Family To-Dos" + GP Brief Upgrade + 14-Day Log Rung-2 Nudge (`ActivitiesView.tsx`, `gp_brief.py`, `Timeline.tsx`)**
   - `FamilyVisitKitCard` highlights who is **On Duty** today from the Family Rota and lets caregivers append the Visit Kit directly to **Family To-Dos**.
   - The 1-page GP Brief (`brief_data` & `gp_brief.py`) now includes active dietary/medicine-food guardrails and social engagement stats.
   - Selecting a `2.low_day` dot on the 14-day `Timeline` shows the exact Qloo cultural nudge sent to the senior.
6. **4-Language Qloo Explanations (`en`, `zh`, `ms`, `ta`)**
   - Every Qloo entity explanation, bridge rationale, and safety badge supports English (`en`), Chinese (`zh`), Malay (`ms`), and Tamil (`ta`), with all strings verified by `guardrail.py`.
