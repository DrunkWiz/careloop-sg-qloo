// In-browser mock of the AAC endpoints, in the contract's shapes. Synthetic people only.
// Supports both "aac-siti" (Bedok North AAC) and "aac-farid" (Ang Mo Kio AAC) from the demo seed.
import type {
  BriefData,
  Caseload,
  CaseloadRow,
  Contact,
  GroupTastePlan,
  Handover,
  LogDay,
  Programme,
  ProgrammeIn,
  Rung,
  SeniorRef,
} from '../shared/contract';
import { applyClaims, delay, registerMock } from './mock';

const WORKER = 'aac-siti';
const FARID = 'aac-farid';
const AAC = { id: 'aac-105', name: 'Sample AAC (Bedok North)' };
const AAC_FARID = { id: 'aac-100', name: 'Ang Mo Kio AAC (demo)' };
const TODAY = '2026-10-24';

const S: Record<string, SeniorRef> = {
  ong: { id: 'ong', name: 'Mr Ong', language: 'zh' },
  aminah: { id: 'aminah', name: 'Mdm Aminah', language: 'en' },
  lee: { id: 'lee', name: 'Mdm Lee', language: 'en' },
  goh: { id: 'goh', name: 'Mr Goh', language: 'zh' },
  ng: { id: 'ng', name: 'Mr Ng', language: 'en-SG' },
  lim: { id: 'lim', name: 'Mr Lim', language: 'en-SG' },
  chandran: { id: 'chandran', name: 'Mr Chandran', language: 'en' },
  yeo: { id: 'yeo', name: 'Mdm Yeo', language: 'zh' },
  osman: { id: 'osman', name: 'Mr Osman', language: 'en-SG' },
};

const sitiIds = ['lee', 'goh', 'ng', 'lim', 'chandran', 'ong', 'aminah'];
const faridIds = ['yeo', 'osman'];

const contacts: Contact[] = [
  ...sitiIds.map((id) => ({
    id: `${WORKER}:${id}`,
    caregiver_id: 'cg-siti',
    senior_id: id,
    role: 'aac' as const,
    primary: true,
    name: 'Siti (AAC)',
    language: 'en' as const,
    worker_id: WORKER,
  })),
  ...faridIds.map((id) => ({
    id: `${FARID}:${id}`,
    caregiver_id: 'cg-farid',
    senior_id: id,
    role: 'aac' as const,
    primary: true,
    name: 'Farid (AAC)',
    language: 'en' as const,
    worker_id: FARID,
  })),
];

const day = (offset: number) => new Date(Date.UTC(2026, 9, 24 - offset)).toISOString().slice(0, 10);

const ongSeries = [
  [128, 79], [131, 80], [127, 78], [null, null], [129, 79], [132, 81], [130, 80],
  [141, 86], [143, 87], [141, 86], [145, 89], [147, 90], [144, 88], [146, 89],
].map(([systolic, diastolic], i) => ({ date: day(13 - i), systolic, diastolic }));

const ongHandover: Handover = {
  id: 'ho-dec-ong-2026-10-24',
  senior_id: 'ong',
  decision_id: 'dec-ong-2026-10-24',
  opened_at: '2026-10-24T09:50:00+08:00',
  kind: 'bp_drift',
  evidence: {
    summary: '7-day average systolic 144, 14 above their own baseline of 130, and over 140 on 7 of 7 days',
    bp_series: ongSeries,
    baseline: { systolic: 130, diastolic: 80 },
    dates: ongSeries.slice(7).map((p) => p.date),
    tried: [
      { date: '2026-10-18', rung: '1', what: 'one odd reading 141/86 against a baseline of 130; offer to re-measure' },
      { date: '2026-10-21', rung: '3', what: '7-day average systolic 136 against a baseline of 130; over 140 on 4 days; not persistent yet' },
    ],
  },
  options: [
    { id: 'call', label: 'Call them today' },
    { id: 'home_visit', label: 'Home visit this week' },
    { id: 'gp_note', label: 'Draft a note to the GP' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const aminahHandover: Handover = {
  id: 'ho-dec-aminah-2026-10-24',
  senior_id: 'aminah',
  decision_id: 'dec-aminah-2026-10-24',
  opened_at: '2026-10-24T12:00:00+08:00',
  kind: 'no_contact',
  evidence: {
    summary: 'no reply to check-ins for 3 days and very low movement, not explained by rain or haze',
    bp_series: [],
    baseline: null,
    dates: [day(2), day(1), day(0)],
    tried: [{ date: day(1), rung: '3', what: 'no reply and no steps for 2 days' }],
  },
  options: [
    { id: 'call', label: 'Call them today' },
    { id: 'home_visit', label: 'Home visit today' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const osmanHandover: Handover = {
  id: 'ho-dec-osman-2026-10-24',
  senior_id: 'osman',
  decision_id: 'dec-osman-2026-10-24',
  opened_at: '2026-10-24T12:00:00+08:00',
  kind: 'no_contact',
  evidence: {
    summary: 'no reply to check-ins for 3 days and very low movement, not explained by rain or haze',
    bp_series: [],
    baseline: { systolic: 133, diastolic: 83 },
    dates: [day(2), day(1), day(0)],
    tried: [{ date: day(1), rung: '3', what: 'no reply and no steps for 2 days' }],
  },
  options: [
    { id: 'call', label: 'Call them today' },
    { id: 'home_visit', label: 'Home visit today' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const chandranHandover: Handover = {
  id: 'ho-dec-chandran-2026-10-24',
  senior_id: 'chandran',
  decision_id: 'dec-chandran-2026-10-24',
  opened_at: '2026-10-24T09:45:00+08:00',
  kind: 'bp_drift',
  evidence: {
    summary: '7-day average systolic 145, 16 above their own baseline of 129, seen through OMRON cuff',
    bp_series: ongSeries,
    baseline: { systolic: 129, diastolic: 80 },
    dates: ongSeries.slice(7).map((p) => p.date),
    tried: [{ date: '2026-10-20', rung: '3', what: '7-day average systolic 139 against a baseline of 129' }],
  },
  options: [
    { id: 'call', label: 'Call them today' },
    { id: 'home_visit', label: 'Home visit this week' },
    { id: 'gp_note', label: 'Draft a note to the GP' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const leeRedFlag: Handover = {
  id: 'ho-dec-lee-2026-10-24',
  senior_id: 'lee',
  decision_id: 'dec-lee-2026-10-24',
  opened_at: '2026-10-24T09:18:00+08:00',
  kind: 'red_flag',
  evidence: { summary: 'a danger symptom: chest pain', bp_series: [], baseline: null, dates: [TODAY], tried: [] },
  options: [
    { id: 'call_now', label: 'Call them now' },
    { id: '995', label: 'Call 995 for them' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

registerMock([ongHandover, aminahHandover, osmanHandover, chandranHandover, leeRedFlag], contacts);

function row(
  worker: string,
  s: SeniorRef,
  status: CaseloadRow['status'],
  rung: Rung,
  reason: string,
  last: string | null,
  h: Handover | null,
): CaseloadRow {
  return {
    senior: s,
    contact_id: `${worker}:${s.id}`,
    status,
    today: { rung, reason },
    handover: h ? applyClaims(h) : null,
    last_reply: last,
  };
}

export function getCaseload(workerId: string): Promise<Caseload> {
  const isFarid = workerId === FARID || workerId === 'cg-farid';
  const w = isFarid ? FARID : WORKER;
  const red = new URLSearchParams(window.location.search).get('scenario') === 'redflag';
  const rows = isFarid
    ? [
        row(w, S.osman, 'handover', '4', osmanHandover.evidence.summary, '2026-10-20T08:30:00+08:00', osmanHandover),
        row(w, S.yeo, 'quiet', '0', 'no action, because BP 127/79 within range for them (baseline 127); movement normal for them', '2026-10-24T08:30:00+08:00', null),
      ]
    : [
        red
          ? row(w, S.lee, 'red_flag', 'R', 'a danger symptom: chest pain', '2026-10-24T09:18:00+08:00', leeRedFlag)
          : row(w, S.lee, 'quiet', '0', 'no action, because BP 132/87 within range for them (baseline 134); movement normal for them', '2026-10-24T09:30:00+08:00', null),
        row(w, S.ong, 'handover', '4', ongHandover.evidence.summary, '2026-10-24T08:55:00+08:00', ongHandover),
        row(w, S.aminah, 'handover', '4', aminahHandover.evidence.summary, '2026-10-21T09:30:00+08:00', aminahHandover),
        row(w, S.chandran, 'handover', '4', chandranHandover.evidence.summary, '2026-10-24T08:45:00+08:00', chandranHandover),
        row(w, S.goh, 'quiet', '0', 'no action, because BP 126/82 within range for them (baseline 126); movement normal for them', '2026-10-24T09:30:00+08:00', null),
        row(w, S.lim, 'quiet', '0', 'no reply to check-ins, but Fitbit steps normal (5,620 steps) so not treated as no-contact', '2026-10-22T08:30:00+08:00', null),
        row(w, S.ng, 'quiet', '3', 'low movement and low contact on 4 days this week (AAC caseload row only, no alert)', '2026-10-24T09:30:00+08:00', null),
      ];
  const order = { red_flag: 0, handover: 1, quiet: 2 };
  rows.sort((a, b) => order[a.status] - order[b.status] || a.senior.name.localeCompare(b.senior.name));
  return delay({ worker_id: w, today: TODAY, seniors: rows });
}

export function getBrief(seniorId: string): Promise<BriefData> {
  const isFaridCentre = seniorId === 'yeo' || seniorId === 'osman' || seniorId === 'tan' || seniorId === 'teo' || seniorId === 'chua';
  return delay({
    senior: { id: seniorId, name: S[seniorId]?.name ?? seniorId, conditions: ['hypertension'], medicines: [] },
    period: { from: '2026-07-27', to: TODAY },
    aac: { ...(isFaridCentre ? AAC_FARID : AAC), going: [] },
  });
}

// --- befriending record (proposed endpoint) ------------------------------------------------

const quiet = (said: string, time = '09:15'): [Rung, string, string, string | null, string] =>
  ['0', '0.nothing', 'no action, because BP within range for them; movement normal for them', said, time];

const LOGS: Record<string, [Rung, string, string, string | null, string][]> = {
  aminah: [
    ['4', '4.no_contact', 'no reply to check-ins for 3 days and very low movement, not explained by rain or haze', null, ''],
    ['3', '3.no_data', 'no reply and no steps for 2 days', null, ''],
    ['0', '0.nothing', 'no action, because one day without a reply never escalates', null, ''],
    quiet('Morning! Took my medicine. Going to the market.', '09:30'),
    quiet('Ok, medicine taken.'),
    quiet('Good morning. Cooking for my neighbour today.'),
    quiet('Taken already.'),
  ],
  osman: [
    ['4', '4.no_contact', 'no reply to check-ins for 3 days and very low movement, not explained by rain or haze', null, ''],
    ['3', '3.no_data', 'no reply and no steps for 2 days', null, ''],
    ['0', '0.nothing', 'no action, because one day without a reply never escalates', null, ''],
    quiet('Ok lah, today fine.', '08:30'),
    quiet('Eat medicine already.'),
    quiet('Kopi with my kakis.'),
    quiet('Ok lah, today fine.'),
  ],
  ong: [
    ['4', '4.bp_drift', ongHandover.evidence.summary, '早上好，药吃了', '08:55'],
    quiet('吃了'),
    quiet('吃了，去咖啡店'),
    ['3', '3.mild_drift', '7-day average systolic 136 against a baseline of 130; over 140 on 4 days; not persistent yet', '吃了', '09:10'],
    quiet('好'),
    quiet('昨天吃了很多卤面'),
    ['1', '1.odd_reading', 'one odd reading 141/86 against a baseline of 130; offer to re-measure', '早', '09:01'],
  ],
  chandran: [
    ['4', '4.bp_drift', chandranHandover.evidence.summary, 'Took my pills.', '08:45'],
    quiet('Took my pills.'),
    ['3', '3.mild_drift', '7-day average systolic 139 against a baseline of 129; over 140 on 4 days; not persistent yet', 'Feeling ok today.', '09:00'],
    quiet('Went to the centre with friends.'),
    quiet('Took my pills.'),
    quiet('Feeling ok today.'),
    quiet('Took my pills.'),
  ],
  ng: [
    ['3', '3.activity_week', 'low movement and low contact on 4 days this week (AAC caseload row only, no alert)', 'Stay home today lor.', '09:30'],
    ['0', '0.nothing', 'no action, because low movement explained by rain (NEA rainfall, nearest station)', 'Raining, stay home.', '09:40'],
    quiet('Eat medicine already.'),
    ['0', '0.nothing', 'no action, because one low day never escalates', 'Stay home today lor.', '09:20'],
    quiet('Kopi with my kakis.'),
    ['0', '0.nothing', 'no action, because one low day never escalates', 'Stay home today lor.', '09:25'],
    quiet('Ok lah, today fine.'),
  ],
};

export function getLog(seniorId: string, n = 7): Promise<LogDay[] | null> {
  const base = LOGS[seniorId] ?? [];
  const filler = quiet(S[seniorId]?.language === 'zh' ? '我吃了药。' : 'Took my pills.');
  const days = Array.from({ length: n }, (_, i) => base[i] ?? filler);
  const red = seniorId === 'lee' && new URLSearchParams(window.location.search).get('scenario') === 'redflag';
  return delay(
    days.map(([rung, rule_id, reason, said, time], i): LogDay => {
      if (red && i === 0) {
        [rung, rule_id, reason, said, time] = ['R', 'R.symptom', 'a danger symptom: chest pain', 'chest pain since morning', '09:18'];
      }
      const bp = reason.match(/BP (\d+)\/(\d+)/);
      return {
        date: day(i),
        rung,
        rule_id,
        reason,
        decision_id: `dec-${seniorId}-${day(i)}`,
        checkins: said ? [{ time: `${day(i)}T${time}:00+08:00`, raw_text: said, language: S[seniorId]?.language ?? 'en' }] : [],
        replied: !!said,
        pills: said ? 'taken' : null,
        social: !!said && /kopi|friends|kakis|咖啡|market|neighbour/i.test(said),
        bp: bp ? { systolic: +bp[1], diastolic: +bp[2] } : null,
        psi: 45,
        rain_mm: /rain/i.test(reason) ? 8.4 : 0,
        festival: null,
      };
    }),
  );
}

// --- programmes ----------------------------------------------------------------------------

const PROG_KEY = 'careloop-mock-programmes';

const samples: Programme[] = ([
  { title: 'Morning exercise', weekdays: ['mon', 'wed', 'fri'], time: '09:00', tags: ['exercise'], indoor: false, free: true },
  { title: 'Communal lunch', weekdays: ['tue'], time: '11:30', tags: ['food', 'chatting'], indoor: true, free: false },
  { title: 'Karaoke afternoon', weekdays: ['wed'], time: '14:00', tags: ['singing'], indoor: true, free: true },
  { title: 'Health talk: knowing your blood pressure', weekdays: ['thu'], time: '10:00', tags: ['learning'], indoor: true, free: true },
  { title: 'Arts and crafts', weekdays: ['fri'], time: '15:00', tags: ['crafts'], indoor: true, free: true },
] as ProgrammeIn[]).map((p, i) => ({ ...p, id: `prog-${AAC.id}-${i}`, place_id: AAC.id, sample: true }));

export function getProgrammes(_aacId: string): Promise<Programme[]> {
  try {
    const saved = localStorage.getItem(PROG_KEY);
    if (saved) return delay(JSON.parse(saved));
  } catch {
    /* fall through to samples */
  }
  return delay(samples);
}

export function putProgrammes(aacId: string, list: ProgrammeIn[]): Promise<Programme[]> {
  const out = list.map((p, i) => ({ ...p, id: `prog-${aacId}-${i}`, place_id: aacId, sample: false }));
  try {
    localStorage.setItem(PROG_KEY, JSON.stringify(out));
  } catch {
    /* storage unavailable: kept for this page only */
  }
  return delay(out);
}

export function importTimetableMock(
  aacId: string,
  body: { text?: string; url?: string; save?: boolean },
): Promise<import('../shared/contract').TimetableImport> {
  const progs = samples.map(({ title, title_zh, weekdays, time, tags, indoor, free }) => ({
    title,
    title_zh,
    weekdays,
    time,
    tags,
    indoor,
    free,
  }));
  return delay({
    programmes: progs,
    warnings: [],
    saved: !!body.save,
    feed: body.url
      ? { url: body.url, pulled_at: new Date().toISOString(), error: null, count: progs.length, warnings: [] }
      : null,
  });
}

export function getAacTasteGroup(aacId: string): Promise<GroupTastePlan> {
  return delay({
    aac_id: aacId,
    aac_name: aacId === 'aac-100' || aacId === 'aac-ang-mo-kio' ? AAC_FARID.name : AAC.name,
    engine: 'qloo_taste_ai',
    mode: 'fixture',
    seniors: [
      { id: 'ong', name: 'Mr Ong', language: 'zh', conditions: ['hypertension', 'high_cholesterol'], medicines: ['amlodipine'] },
      { id: 'aminah', name: 'Mdm Aminah', language: 'en', conditions: ['hypertension', 'diabetes'], medicines: ['metformin'] },
      { id: 'lee', name: 'Mdm Lee', language: 'en', conditions: ['hypertension'], medicines: [] },
      { id: 'goh', name: 'Mr Goh', language: 'zh', conditions: ['hypertension'], medicines: [] },
      { id: 'ng', name: 'Mr Ng', language: 'en-SG', conditions: [], medicines: [] },
    ],
    shared_seeds: [
      { query: 'kopitiam', count: 4, seniors: ['Mr Ong', 'Mdm Lee', 'Mr Goh', 'Mr Ng'] },
      { query: 'Teresa Teng', count: 3, seniors: ['Mr Ong', 'Mdm Lee', 'Mr Goh'] },
      { query: 'tai chi', count: 3, seniors: ['Mr Ong', 'Mdm Aminah', 'Mr Goh'] },
      { query: 'P. Ramlee', count: 2, seniors: ['Mdm Aminah', 'Mr Ng'] },
    ],
    resolved_entities: [
      { seed: 'kopitiam', entity_id: 'urn:entity:place:kopitiam-heritage', name: 'Traditional Nanyang Kopitiam', type: 'urn:entity:place', tags: ['kopi', 'nostalgia', 'morning_routine'] },
      { seed: 'Teresa Teng', entity_id: 'urn:entity:artist:teresa-teng', name: 'Teresa Teng (邓丽君)', type: 'urn:entity:artist', tags: ['mandopop', '1970s', 'nostalgia'] },
      { seed: 'P. Ramlee', entity_id: 'urn:entity:artist:p-ramlee', name: 'P. Ramlee', type: 'urn:entity:artist', tags: ['malay_classics', 'jalan_ampas', '1960s'] },
    ],
    cohort_constraints: [
      { rule: 'no_high_sodium', label: 'Low-sodium options required (hypertension care)', triggered_by: ['Mr Ong', 'Mdm Aminah', 'Mdm Lee', 'Mr Goh'] },
      { rule: 'no_high_sugar', label: 'Unsweetened / low-GI options required (diabetes care)', triggered_by: ['Mdm Aminah'] },
      { rule: 'no_grapefruit', label: 'Avoid grapefruit (medicine interaction)', triggered_by: ['Mr Ong'] },
    ],
    catering_matrix: {
      total_seniors: 5,
      recommended_refreshment: 'Teochew Steamed Fish Porridge & Clear Soup Stall',
      counts: {
        halal: 1,
        vegetarian: 0,
        no_beef: 1,
        low_salt: 4,
        less_sugar: 1,
        low_purine_gout: 1,
        renal_friendly: 0,
        no_grapefruit_pomelo: 1,
        wheelchair_seated: 1,
      },
      rows: [
        { rule_id: 'diet.hypertension.low_sodium', badge: 'Low-salt / less gravy', count: 4, seniors: ['Mr Ong', 'Mdm Aminah', 'Mdm Lee', 'Mr Goh'] },
        { rule_id: 'diet.diabetes.low_sugar', badge: 'Siew dai / kosong', count: 1, seniors: ['Mdm Aminah'] },
        { rule_id: 'pref.halal', badge: 'Halal-friendly', count: 1, seniors: ['Mdm Aminah'] },
        { rule_id: 'diet.gout.low_purine', badge: 'Low-purine (gout-safe)', count: 1, seniors: ['Mr Goh'] },
        { rule_id: 'mobility.step_free_seated', badge: 'Step-free / seated', count: 1, seniors: ['Mdm Lee'] },
      ],
      caterer_sheet_text:
        'Sample AAC (Bedok North) — Caterer & Outing Headcount Matrix (5 seniors):\n' +
        '• Recommended Venue / Dish: Teochew Steamed Fish Porridge & Clear Soup Stall\n' +
        '• Low-Salt / Less Gravy: 4 pax\n' +
        '• Less Sugar / Kosong (Diabetic-Friendly): 1 pax\n' +
        '• Halal-Certified: 1 pax\n' +
        '• Low-Purine (No Organ Meat / Anchovy Broth): 1 pax\n' +
        '• No Grapefruit / Pomelo (Statin/BP Leaflet): 1 pax\n' +
        '• Wheelchair / Step-Free Seating: 1 pax',
    },
    weather: { psi: 45, rain_mm: 0, indoor_only: false },
    group_recommendations: {
      refreshment_or_outing: [
        {
          id: 'urn:entity:place:teochew-fish-soup',
          name: 'Teochew Steamed Fish Porridge & Clear Soup Stall',
          tags: ['teochew', 'low_sodium_available', 'easy_to_chew', 'hawker_heritage', 'indoor_seating'],
          why: 'Matches cohort taste for Traditional Nanyang Kopitiam & Teresa Teng; fits all 5 seniors (Low-sodium options required (hypertension care); Unsweetened / low-GI options required (diabetes care)).',
          bridge: 'kopitiam + Teresa Teng → [nostalgia, 1970s] → Teochew Steamed Fish Porridge & Clear Soup Stall (✓ cohort-safe)',
        },
        {
          id: 'urn:entity:place:soy-beancurd-less-sugar',
          name: 'Traditional Warm Tau Huay & Soy Milk (Siew Dai / Kosong)',
          tags: ['nostalgia', 'custom_sugar_level', 'low_gi_option', 'calcium_rich', 'indoor_seating'],
          why: 'Matches cohort taste for Traditional Nanyang Kopitiam & Teresa Teng; fits all 5 seniors (Low-sodium options required (hypertension care); Unsweetened / low-GI options required (diabetes care)).',
          bridge: 'kopitiam + Teresa Teng → [nostalgia, 1970s] → Traditional Warm Tau Huay & Soy Milk (Siew Dai / Kosong) (✓ cohort-safe)',
        },
      ],
      music_playlist: [
        {
          id: 'urn:entity:artist:teresa-teng',
          name: 'Teresa Teng — The Moon Represents My Heart (月亮代表我的心)',
          tags: ['mandopop', '1970s', 'singalong', 'nostalgia'],
          why: 'Shared nostalgic sing-along pick across the cohort (Traditional Nanyang Kopitiam, Teresa Teng (邓丽君)).',
          bridge: 'kopitiam + Teresa Teng → [nostalgia, singalong] → Teresa Teng — The Moon Represents My Heart (月亮代表我的心)',
        },
        {
          id: 'urn:entity:artist:saloma',
          name: 'Biduanita Saloma & P. Ramlee Duets',
          tags: ['malay_classics', '1960s', 'kampung_memories', 'singalong'],
          why: 'Shared nostalgic sing-along pick across the cohort (Traditional Nanyang Kopitiam, Teresa Teng (邓丽君)).',
          bridge: 'kopitiam + Teresa Teng → [nostalgia, singalong] → Biduanita Saloma & P. Ramlee Duets',
        },
      ],
      matinee_film: [
        {
          id: 'urn:entity:movie:ilo-ilo',
          name: 'Ilo Ilo (爸妈不在家) — Heartwarming Singapore Family Drama',
          tags: ['singapore_cinema', 'family', 'mandarin_hokkien'],
          why: 'Group matinee screening matched via Qloo cross-domain taste graph for 5 seniors at Sample AAC (Bedok North).',
          bridge: 'kopitiam + Teresa Teng → [nostalgia, singapore_heritage] → Ilo Ilo (爸妈不在家) — Heartwarming Singapore Family Drama',
        },
      ],
    },
    filtered_out: [
      { name: 'Old Airport Road Char Kway Teow & Laksa', reason: 'Filtered for cohort safety: Low-sodium options required (hypertension care) (Mr Ong, Mdm Aminah, Mdm Lee, Mr Goh)' },
      { name: 'Traditional Kopi Gu You & Kaya Toast Set (Full Sugar)', reason: 'Filtered for cohort safety: Unsweetened / low-GI options required (diabetes care) (Mdm Aminah)' },
    ],
  });
}
