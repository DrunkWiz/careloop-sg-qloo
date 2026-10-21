// In-browser mock of the family endpoints, in the exact shapes of the API contract.
// Covers all 13 demo seniors, 12 caregivers, and 18 contacts from backend/api/demo.py.
// ?scenario=handover (default), ?scenario=quiet, ?scenario=redflag.
import type {
  BriefData,
  CareNotes,
  CaregiverView,
  Contact,
  Digest,
  FamilySees,
  FamilyView,
  Handover,
  HealthSyncResult,
  HealthSyncView,
  LogDay,
  Medicine,
  MedicinesView,
  Message,
  PairCodeIn,
  PairCodeOut,
  PairIn,
  PairOut,
  PreventionView,
  RotaView,
  Rung,
  VentPost,
} from '../shared/contract';

interface SeniorMockProfile {
  id: string;
  name: string;
  language: 'en' | 'en-SG' | 'zh';
  region: 'north' | 'south' | 'east' | 'west' | 'central';
  aac_id: string;
  aac_name: string;
  base_bp: [number, number];
  steps: number;
  conditions: string[];
  medicines: Medicine[];
  consent: { family_sees: FamilySees; share_words: boolean; share_activity: boolean };
  checkins: { time: string; raw_text: string; language: 'en' | 'en-SG' | 'zh' }[];
  device?: { platform: 'health_connect' | 'healthkit'; platform_name: string; apps: string[]; hr: number };
}

const SENIOR_PROFILES: Record<string, SeniorMockProfile> = {
  tan: {
    id: 'tan',
    name: 'Mr Tan',
    language: 'en-SG',
    region: 'central',
    aac_id: 'aac-100',
    aac_name: 'Ang Mo Kio AAC (demo)',
    base_bp: [128, 80],
    steps: 5200,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [
      { time: '2026-10-24T08:30:00+08:00', raw_text: 'Ok lah, today fine.', language: 'en-SG' },
      { time: '2026-10-24T09:30:00+08:00', raw_text: 'Eat medicine already.', language: 'en-SG' },
      { time: '2026-10-23T08:30:00+08:00', raw_text: 'Kopi with my kakis.', language: 'en-SG' },
      { time: '2026-10-23T09:30:00+08:00', raw_text: 'Eat medicine already.', language: 'en-SG' },
    ],
    device: { platform: 'health_connect', platform_name: 'Health Connect', apps: ['Fitbit', 'OMRON connect'], hr: 68 },
  },
  wong: {
    id: 'wong',
    name: 'Mdm Wong',
    language: 'zh',
    region: 'west',
    aac_id: 'aac-002',
    aac_name: 'Jurong West AAC (demo)',
    base_bp: [132, 82],
    steps: 3800,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [
      { time: '2026-10-24T08:25:00+08:00', raw_text: '今天还好，和朋友去唱歌。', language: 'zh' },
      { time: '2026-10-24T09:15:00+08:00', raw_text: '我吃了药。', language: 'zh' },
    ],
  },
  teo: {
    id: 'teo',
    name: 'Mrs Teo',
    language: 'en',
    region: 'west',
    aac_id: 'aac-100',
    aac_name: 'Ang Mo Kio AAC (demo)',
    base_bp: [130, 81],
    steps: 4400,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [
      { time: '2026-10-24T08:15:00+08:00', raw_text: 'Feeling ok today. Watered the plants.', language: 'en' },
      { time: '2026-10-24T09:05:00+08:00', raw_text: 'Took my pills.', language: 'en' },
    ],
  },
  kaur: {
    id: 'kaur',
    name: 'Mdm Kaur',
    language: 'en',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [124, 76],
    steps: 6800,
    conditions: ['hypertension', 'high cholesterol'],
    medicines: [
      { name: 'telmisartan', dose_text: '40 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
      { name: 'atorvastatin', dose_text: '20 mg once a day', schedule: ['night'], started: '2024-03-01', for_bp: false },
    ],
    consent: { family_sees: 'readings', share_words: false, share_activity: true },
    checkins: [{ time: '2026-10-24T08:00:00+08:00', raw_text: 'Morning walk done. Took my pills.', language: 'en' }],
    device: { platform: 'healthkit', platform_name: 'Apple Health', apps: ['Fitbit', 'OMRON connect'], hr: 64 },
  },
  rahman: {
    id: 'rahman',
    name: 'Encik Rahman',
    language: 'en',
    region: 'west',
    aac_id: 'aac-002',
    aac_name: 'Jurong West AAC (demo)',
    base_bp: [134, 84],
    steps: 4200,
    conditions: ['hypertension', 'type 2 diabetes'],
    medicines: [
      { name: 'amlodipine', dose_text: '10 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
      { name: 'metformin', dose_text: '500 mg twice a day, with meals', schedule: ['morning', 'evening'], started: '2024-03-01', for_bp: false },
    ],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [
      { time: '2026-10-24T08:20:00+08:00', raw_text: 'Feeling ok today. Had kopi o kosong with friends.', language: 'en' },
      { time: '2026-10-24T09:10:00+08:00', raw_text: 'Took my pills.', language: 'en' },
    ],
    device: { platform: 'health_connect', platform_name: 'Health Connect', apps: ['Fitbit'], hr: 72 },
  },
  chua: {
    id: 'chua',
    name: 'Mdm Chua',
    language: 'zh',
    region: 'central',
    aac_id: 'aac-100',
    aac_name: 'Ang Mo Kio AAC (demo)',
    base_bp: [130, 80],
    steps: 3500,
    conditions: ['hypertension'],
    medicines: [
      { name: 'losartan', dose_text: '50 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
      { name: 'aspirin (low dose)', dose_text: '100 mg once a day, after food', schedule: ['morning'], started: '2024-03-01', for_bp: false },
    ],
    consent: { family_sees: 'digest', share_words: false, share_activity: true },
    checkins: [{ time: '2026-10-24T08:40:00+08:00', raw_text: '今天还好，我吃了药。', language: 'zh' }],
  },
  lee: {
    id: 'lee',
    name: 'Mdm Lee',
    language: 'en',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [135, 84],
    steps: 3000,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-24T09:30:00+08:00', raw_text: 'Feeling ok today.', language: 'en' }],
  },
  goh: {
    id: 'goh',
    name: 'Mr Goh',
    language: 'zh',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [126, 78],
    steps: 6100,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-24T09:15:00+08:00', raw_text: '我吃了药。', language: 'zh' }],
  },
  ng: {
    id: 'ng',
    name: 'Mr Ng',
    language: 'en-SG',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [138, 86],
    steps: 2600,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-24T09:30:00+08:00', raw_text: 'Stay home today lor.', language: 'en-SG' }],
  },
  lim: {
    id: 'lim',
    name: 'Mr Lim',
    language: 'en-SG',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [130, 82],
    steps: 5600,
    conditions: ['hypertension'],
    medicines: [
      { name: 'bisoprolol', dose_text: '2.5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
      { name: 'hydrochlorothiazide', dose_text: '12.5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
    ],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-22T08:30:00+08:00', raw_text: 'Ok lah, today fine.', language: 'en-SG' }],
    device: { platform: 'health_connect', platform_name: 'Health Connect', apps: ['Fitbit'], hr: 70 },
  },
  chandran: {
    id: 'chandran',
    name: 'Mr Chandran',
    language: 'en',
    region: 'east',
    aac_id: 'aac-105',
    aac_name: 'Bedok North AAC (demo)',
    base_bp: [129, 80],
    steps: 4800,
    conditions: ['hypertension'],
    medicines: [
      { name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
      { name: 'Zanidip', dose_text: '10 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true },
    ],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-24T08:45:00+08:00', raw_text: 'Took my pills.', language: 'en' }],
    device: { platform: 'health_connect', platform_name: 'Health Connect', apps: ['Fitbit', 'OMRON connect'], hr: 74 },
  },
  yeo: {
    id: 'yeo',
    name: 'Mdm Yeo',
    language: 'zh',
    region: 'central',
    aac_id: 'aac-100',
    aac_name: 'Ang Mo Kio AAC (demo)',
    base_bp: [127, 79],
    steps: 3300,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-24T08:30:00+08:00', raw_text: '今天还好，和朋友去了活动中心。', language: 'zh' }],
  },
  osman: {
    id: 'osman',
    name: 'Mr Osman',
    language: 'en-SG',
    region: 'central',
    aac_id: 'aac-100',
    aac_name: 'Ang Mo Kio AAC (demo)',
    base_bp: [133, 83],
    steps: 2900,
    conditions: ['hypertension'],
    medicines: [{ name: 'amlodipine', dose_text: '5 mg once a day', schedule: ['morning'], started: '2024-03-01', for_bp: true }],
    consent: { family_sees: 'readings', share_words: true, share_activity: true },
    checkins: [{ time: '2026-10-20T08:30:00+08:00', raw_text: 'Ok lah, today fine.', language: 'en-SG' }],
  },
};

const family: Contact[] = [
  { id: 'tan-weiling', caregiver_id: 'cg-weiling', senior_id: 'tan', role: 'family', primary: true, name: 'Wei Ling', language: 'en', worker_id: null },
  { id: 'tan-kelvin', caregiver_id: 'cg-kelvin', senior_id: 'tan', role: 'family', primary: false, name: 'Kelvin', language: 'en', worker_id: null },
  { id: 'teo-kelvin', caregiver_id: 'cg-kelvin', senior_id: 'teo', role: 'family', primary: true, name: 'Kelvin', language: 'en', worker_id: null },
  { id: 'teo-jane', caregiver_id: 'cg-jane', senior_id: 'teo', role: 'family', primary: false, name: 'Jane', language: 'en', worker_id: null },
  { id: 'wong-mei', caregiver_id: 'cg-mei', senior_id: 'wong', role: 'family', primary: true, name: 'Mei', language: 'zh', worker_id: null },
  { id: 'kaur-priya', caregiver_id: 'cg-priya', senior_id: 'kaur', role: 'family', primary: true, name: 'Priya', language: 'en', worker_id: null },
  { id: 'kaur-arjun', caregiver_id: 'cg-arjun', senior_id: 'kaur', role: 'family', primary: false, name: 'Arjun', language: 'en', worker_id: null },
  { id: 'rahman-nur', caregiver_id: 'cg-nur', senior_id: 'rahman', role: 'family', primary: true, name: 'Nur', language: 'en', worker_id: null },
  { id: 'rahman-maria', caregiver_id: 'cg-maria', senior_id: 'rahman', role: 'family', primary: false, name: 'Maria (helper)', language: 'en', worker_id: null },
  { id: 'chua-junjie', caregiver_id: 'cg-junjie', senior_id: 'chua', role: 'family', primary: true, name: 'Jun Jie', language: 'en', worker_id: null },
  { id: 'chua-huimin', caregiver_id: 'cg-huimin', senior_id: 'chua', role: 'family', primary: false, name: 'Hui Min', language: 'zh', worker_id: null },
];

const CAREGIVER_META: Record<string, { name: string; language: 'en' | 'en-SG' | 'zh'; role: 'family' | 'aac'; worker_id: string | null }> = {
  'cg-weiling': { name: 'Wei Ling', language: 'en', role: 'family', worker_id: null },
  'cg-kelvin': { name: 'Kelvin', language: 'en', role: 'family', worker_id: null },
  'cg-jane': { name: 'Jane', language: 'en', role: 'family', worker_id: null },
  'cg-mei': { name: 'Mei', language: 'zh', role: 'family', worker_id: null },
  'cg-priya': { name: 'Priya', language: 'en', role: 'family', worker_id: null },
  'cg-arjun': { name: 'Arjun', language: 'en', role: 'family', worker_id: null },
  'cg-nur': { name: 'Nur', language: 'en', role: 'family', worker_id: null },
  'cg-maria': { name: 'Maria (helper)', language: 'en', role: 'family', worker_id: null },
  'cg-junjie': { name: 'Jun Jie', language: 'en', role: 'family', worker_id: null },
  'cg-huimin': { name: 'Hui Min', language: 'zh', role: 'family', worker_id: null },
  'cg-siti': { name: 'Siti', language: 'en', role: 'aac', worker_id: 'aac-siti' },
  'cg-farid': { name: 'Farid', language: 'en', role: 'aac', worker_id: 'aac-farid' },
};

const day = (offset: number) => {
  const d = new Date(Date.UTC(2026, 9, 24 - offset));
  return d.toISOString().slice(0, 10);
};

// 7 quiet days around ~128/80, then a 7-day drift to ~145/88.
const series = [
  [126, 78], [130, 81], [127, 79], [129, 80], [null, null], [128, 79], [131, 82],
  [140, 85], [142, 87], [139, 84], [144, 88], [146, 89], [143, 87], [145, 88],
].map(([systolic, diastolic], i) => ({ date: day(13 - i), systolic, diastolic }));

function buildSeniorSeries(seniorId: string) {
  if (seniorId === 'tan') return series;
  const p = SENIOR_PROFILES[seniorId] ?? SENIOR_PROFILES.tan;
  const [bSys, bDia] = p.base_bp;
  const offsets = [
    [-2, -1], [1, 1], [-1, 0], [0, 1], [2, 1], [-1, -1], [1, 0],
    [0, 0], [-2, -1], [1, 1], [0, 0], [2, 1], [-1, 0], [0, 0],
  ];
  return offsets.map(([ds, dd], i) => ({
    date: day(13 - i),
    systolic: bSys + ds,
    diastolic: bDia + dd,
  }));
}

const driftHandover: Handover = {
  id: 'ho-dec-tan-2026-10-24',
  senior_id: 'tan',
  decision_id: 'dec-tan-2026-10-24',
  opened_at: '2026-10-24T09:50:00+08:00',
  kind: 'bp_drift',
  evidence: {
    summary: '7-day average systolic 143, 15 above their own baseline of 128, and over 140 on 6 of 7 days',
    bp_series: series,
    baseline: { systolic: 128, diastolic: 80 },
    dates: series.slice(7).map((p) => p.date),
    tried: [
      { date: '2026-10-15', rung: '1', what: 'one odd reading 155/91 against a baseline of 128; offer to re-measure' },
      { date: '2026-10-17', rung: '2', what: 'pills running low; suggest refill or delivery' },
      { date: '2026-10-21', rung: '3', what: '7-day average systolic 137 against a baseline of 128; over 140 on 4 days; not persistent yet' },
    ],
  },
  options: [
    { id: 'call', label: 'Call them today' },
    { id: 'visit', label: 'Visit this week' },
    { id: 'gp', label: 'Book a GP appointment' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const redFlagHandover: Handover = {
  id: 'ho-dec-tan-2026-10-25',
  senior_id: 'tan',
  decision_id: 'dec-tan-2026-10-25',
  opened_at: '2026-10-25T10:12:00+08:00',
  kind: 'red_flag',
  evidence: {
    summary: 'blood pressure 186/112 at crisis level (180/110 or above)',
    bp_series: [...series.slice(1), { date: '2026-10-25', systolic: 186, diastolic: 112 }],
    baseline: { systolic: 128, diastolic: 80 },
    dates: ['2026-10-25'],
    tried: [],
  },
  options: [
    { id: 'call_now', label: 'Call them now' },
    { id: '995', label: 'Call 995 for them' },
  ],
  status: 'open',
  claimed_by: null,
  claimed_at: null,
  choice: null,
};

const redFlagMessage: Message = {
  id: 'msg-dec-tan-2026-10-25-tan-weiling',
  senior_id: 'tan',
  decision_id: 'dec-tan-2026-10-25',
  to: 'family',
  contact_id: 'tan-weiling',
  rung: 'R',
  language: 'en',
  text: 'CareLoop urgent: Mr Tan logged blood pressure 186/112 at crisis level (180/110 or above). We have asked them to call 995 now. Please check on them immediately.',
  from_template: true,
  guardrail: { passed: true, reasons: [] },
  model: null,
  time: '2026-10-25T10:12:00+08:00',
};

const claims = new Map<string, { claimed_by: string; claimed_by_name: string; claimed_at: string; choice: string }>();
const allHandovers = new Map<string, Handover>([
  [driftHandover.id, driftHandover],
  [redFlagHandover.id, redFlagHandover],
]);
const allContacts = new Map<string, Contact>(family.map((c) => [c.id, c]));

let mockDayOffset = 11;

export function registerMock(handovers: Handover[], contacts: Contact[]) {
  handovers.forEach((h) => allHandovers.set(h.id, h));
  contacts.forEach((c) => allContacts.set(c.id, c));
}

export function applyClaims(h: Handover): Handover {
  const c = claims.get(h.id);
  return c ? { ...h, status: 'claimed', ...c } : { ...h };
}

function scenario(): 'quiet' | 'handover' | 'redflag' {
  const s = new URLSearchParams(window.location.search).get('scenario');
  if (s === 'quiet' || s === 'redflag' || s === 'handover') return s;
  return mockDayOffset >= 11 ? 'handover' : 'quiet';
}

export const delay = <T,>(v: T): Promise<T> => new Promise((r) => setTimeout(() => r(v), 60));

export function getCaregiverView(caregiverId: string): Promise<CaregiverView> {
  const byContact = allContacts.get(caregiverId);
  const resolvedCgId = byContact ? byContact.caregiver_id : caregiverId;
  const mine = [...allContacts.values()].filter((c) => c.caregiver_id === resolvedCgId);
  const meta = CAREGIVER_META[resolvedCgId];
  const me = mine[0];
  const s = scenario();
  return delay({
    caregiver: {
      id: resolvedCgId,
      name: meta?.name ?? me?.name ?? 'Caregiver',
      language: meta?.language ?? me?.language ?? 'en',
      role: meta?.role ?? me?.role ?? 'family',
      worker_id: meta?.worker_id ?? me?.worker_id ?? null,
    },
    seniors: mine.map((c) => {
      const prof = SENIOR_PROFILES[c.senior_id] ?? SENIOR_PROFILES.tan;
      const isTan = c.senior_id === 'tan';
      const status = isTan ? (s === 'redflag' ? 'red_flag' : s === 'handover' ? 'handover' : 'quiet') : 'quiet';
      const rv = mockRotas[c.senior_id];
      const onDuty = rv?.on_duty ? rv.on_duty.id === c.id : c.primary;
      return {
        contact_id: c.id,
        senior_id: prof.id,
        senior_name: prof.name,
        primary: c.primary,
        status,
        on_duty: onDuty,
      };
    }),
  });
}

export function getFamilyView(contactId: string): Promise<FamilyView> {
  const me =
    allContacts.get(contactId) ??
    family.find((c) => c.id === contactId || c.caregiver_id === contactId) ??
    family[0];
  const prof = SENIOR_PROFILES[me.senior_id] ?? SENIOR_PROFILES.tan;
  const seniorContacts = [...allContacts.values()].filter((c) => c.senior_id === prof.id);
  const isTan = prof.id === 'tan';
  const s = isTan ? scenario() : 'quiet';
  const handovers = isTan
    ? (s === 'quiet' ? [] : s === 'redflag' ? [redFlagHandover, driftHandover] : [driftHandover]).map(applyClaims)
    : [];
  const [bSys, bDia] = prof.base_bp;
  const rv = mockRotas[prof.id];
  const onDutyName = rv?.on_duty?.name ?? seniorContacts.find((c) => c.primary)?.name ?? me.name;
  const onDuty = rv?.on_duty ? rv.on_duty.id === me.id : me.primary;
  const todayStr = s === 'redflag' ? '2026-10-25' : '2026-10-24';

  const digest: Digest | null =
    prof.consent.family_sees === 'nothing'
      ? null
      : {
          week_start: '2026-10-18',
          week_end: todayStr,
          headline: s === 'redflag' || s === 'handover' ? 'needs you' : prof.id === 'chua' ? 'worth a look' : 'quiet',
          readings_days: 7,
          mean_systolic: prof.consent.family_sees === 'readings' ? (isTan && s !== 'quiet' ? 143 : bSys) : null,
          mean_diastolic: prof.consent.family_sees === 'readings' ? (isTan && s !== 'quiet' ? 87 : bDia) : null,
          baseline: prof.consent.family_sees === 'readings' ? { systolic: bSys, diastolic: bDia } : null,
          pills_taken_days: prof.id === 'rahman' ? 6 : 7,
          missed_days: prof.id === 'rahman' ? 1 : 0,
          checkin_days: 7,
          social_days: 4,
          worth_raising:
            isTan && s !== 'quiet'
              ? ['7-day average systolic 143 vs 128 baseline (over 140 on 6 of 7 days)', 'Mentioned pills running low on 17 Oct']
              : prof.id === 'rahman'
                ? ['Missed Sunday morning pill (recurring Sunday pattern)']
                : prof.id === 'chua'
                  ? ['Mild systolic rise (+6 mmHg over baseline this week)']
                  : [],
        };

  return delay({
    contact: { ...me, consent: prof.consent },
    senior: { id: prof.id, name: prof.name, language: prof.language },
    family_sees: prof.consent.family_sees,
    today: todayStr,
    status: s === 'redflag' ? 'red_flag' : s === 'handover' ? 'handover' : 'quiet',
    on_duty: onDuty,
    on_duty_name: onDutyName,
    digest,
    handovers,
    red_flags: isTan && s === 'redflag' ? [redFlagMessage] : [],
    other_contacts: seniorContacts.filter((c) => c.id !== me.id).map((c) => ({ id: c.id, name: c.name })),
  });
}

export function setPrimary(contactId: string): Promise<Contact> {
  const c = allContacts.get(contactId) ?? family[0];
  for (const item of allContacts.values()) {
    if (item.senior_id === c.senior_id) item.primary = item.id === c.id;
  }
  return delay({ ...c, primary: true });
}

export function createPairCode(body: PairCodeIn): Promise<PairCodeOut> {
  const code = String(Math.floor(100000 + Math.random() * 900000));
  const cgId = body.caregiver_id ?? `cg-${Date.now()}`;
  const seniorId = body.senior_id ?? `senior-${Date.now()}`;
  const contactId = `${seniorId}-${cgId}`;
  const contact: Contact = {
    id: contactId,
    caregiver_id: cgId,
    senior_id: seniorId,
    role: body.role,
    primary: true,
    name: body.contact_name,
    language: body.language ?? 'en',
    worker_id: body.worker_id ?? null,
  };
  allContacts.set(contactId, contact);
  return delay({ code, caregiver_id: cgId, senior_id: seniorId, contact_id: contactId });
}

export function pair(_body: PairIn): Promise<PairOut> {
  return delay({ senior_id: 'tan', contact_name: 'Wei Ling', contact_id: 'tan-weiling' });
}

export function claimHandover(handoverId: string, contactId: string, choice: string): Promise<Handover> {
  const c = allContacts.get(contactId) ?? family[0];
  claims.set(handoverId, {
    claimed_by: c.id,
    claimed_by_name: c.name,
    claimed_at: new Date().toISOString(),
    choice,
  });
  const base = allHandovers.get(handoverId) ?? driftHandover;
  return delay(applyClaims(base));
}

export function getBrief(seniorId: string): Promise<BriefData> {
  const prof = SENIOR_PROFILES[seniorId] ?? SENIOR_PROFILES.tan;
  const isTan = prof.id === 'tan';
  return delay({
    senior: {
      id: prof.id,
      name: prof.name,
      conditions: prof.conditions,
      medicines: prof.medicines,
    },
    period: { from: '2026-07-27', to: '2026-10-24' },
    aac: { id: prof.aac_id, name: prof.aac_name, going: isTan ? ['Morning exercise', 'Communal lunch'] : ['Morning exercise'] },
  });
}

// --- 14-day daily log (GET /senior/{id}/log) ------------------------------------------------

const TAN_DAYS: [string, Rung, string, string, string | null][] = [
  ['2026-10-25', 'R', 'R.bp_crisis', 'blood pressure 186/112 at crisis level (180/110 or above)', "I'm fine lah, BP 186 over 112"],
  ['2026-10-24', '4', '4.bp_drift', driftHandover.evidence.summary, 'Ok lah, today fine.'],
  ['2026-10-23', '3', '3.mild_drift', '7-day average systolic 142 against a baseline of 128; over 140 on 5 days; not persistent yet', 'Kopi with my kakis.'],
  ['2026-10-22', '3', '3.mild_drift', '7-day average systolic 140 against a baseline of 128; over 140 on 4 days; not persistent yet', 'Ok lah, today fine.'],
  ['2026-10-21', '3', '3.mild_drift', '7-day average systolic 137 against a baseline of 128; over 140 on 4 days; not persistent yet', 'Stay home today lor.'],
  ['2026-10-20', '0', '0.nothing', 'no action, because BP 139/84 within range for them; movement normal for them', 'Ok lah, today fine.'],
  ['2026-10-19', '0', '0.nothing', 'no action, because BP 142/87 slightly above baseline, watching quietly', 'Kopi with my kakis.'],
  ['2026-10-18', '0', '0.nothing', 'no action, because BP 140/85 slightly above baseline, watching quietly', 'Ok lah, today fine.'],
  ['2026-10-17', '2', '2.meds_low', 'pills running low; suggest refill or delivery', 'Ok lah. Medicine almost finish already.'],
  ['2026-10-16', '0', '0.nothing', 'no action, because BP 128/79 within range for them; movement normal for them', 'Ok lah, today fine.'],
  ['2026-10-15', '1', '1.odd_reading', 'one odd reading 155/91 against a baseline of 128; offer to re-measure', 'Ok lah, today fine.'],
  ['2026-10-14', '0', '0.nothing', 'no action, because low movement explained by rain (NEA rainfall, nearest station)', 'Raining, stay home lor.'],
  ['2026-10-13', '0', '0.nothing', 'no action, because BP 130/81 within range for them (baseline 128); movement normal for them', 'Kopi with my kakis.'],
  ['2026-10-12', '0', '0.nothing', 'no action, because BP 126/78 within range for them (baseline 128); movement normal for them', 'Ok lah, today fine.'],
  ['2026-10-11', '0', '0.nothing', 'no action, because BP 129/80 within range for them (baseline 128); movement normal for them', 'Ok lah, today fine.'],
];

export function getLog(days: number, seniorId = 'tan'): Promise<LogDay[]> {
  const prof = SENIOR_PROFILES[seniorId] ?? SENIOR_PROFILES.tan;
  if (prof.id !== 'tan') {
    const ser = buildSeniorSeries(prof.id);
    const defaultWords =
      prof.language === 'zh' ? '今天还好，我吃了药。' : prof.language === 'en-SG' ? 'Ok lah, today fine.' : 'Feeling ok today. Took my pills.';
    return delay(
      ser
        .slice(-days)
        .reverse()
        .map((pt, idx) => ({
          date: pt.date,
          rung: '0' as Rung,
          rule_id: '0.nothing',
          reason: `no action, because BP ${pt.systolic}/${pt.diastolic} within range for them (baseline ${prof.base_bp[0]}); movement normal for them`,
          decision_id: `dec-${prof.id}-${pt.date}`,
          checkins: prof.consent.share_words
            ? [{ time: `${pt.date}T08:30:00+08:00`, raw_text: defaultWords, language: prof.language }]
            : [],
          replied: true,
          pills: (prof.id === 'rahman' && idx === 3 ? 'missed' : 'taken') as 'taken' | 'missed',
          social: idx % 2 === 0,
          bp: pt.systolic != null && pt.diastolic != null ? { systolic: pt.systolic, diastolic: pt.diastolic } : null,
          psi: 45,
          rain_mm: 0,
          festival: null,
        })),
    );
  }
  const s = scenario();
  const end = s === 'redflag' ? '2026-10-25' : s === 'handover' ? '2026-10-24' : '2026-10-13';
  const bp = (date: string, reason: string | null) => {
    const p = series.find((x) => x.date === date);
    if (p) return p.systolic != null && p.diastolic != null ? { systolic: p.systolic, diastolic: p.diastolic } : null;
    const m = reason?.match(/BP (\d+)\/(\d+)/);
    return m ? { systolic: +m[1], diastolic: +m[2] } : null;
  };
  return delay(
    TAN_DAYS.filter(([d]) => d <= end)
      .slice(0, days)
      .map(([date, rung, rule_id, reason, words]) => ({
        date,
        rung,
        rule_id,
        reason,
        decision_id: `dec-tan-${date}`,
        checkins: words ? [{ time: `${date}T08:30:00+08:00`, raw_text: words, language: 'en-SG' as const }] : [],
        replied: !!words,
        pills: 'taken' as const,
        social: !!words && /kopi|kakis/i.test(words),
        bp: bp(date, reason),
        psi: 45,
        rain_mm: words && /rain/i.test(words) ? 6.2 : 0,
        festival: null,
      })),
  );
}

// --- care notes (GET/PUT /senior/{id}/care-notes), kept in this browser for the offline demo ------

const NOTES_KEY = (sid: string) => `careloop-mock-notes-${sid}`;
const SEEDED_TAN_NOTES: CareNotes = {
  appointments: [
    {
      id: 'ap-1',
      date: '2026-10-02',
      time: '10:00',
      place: 'Ang Mo Kio Family Clinic (demo)',
      purpose: 'BP review',
      who_goes: 'Wei Ling',
      notes_after: 'BP fine at the clinic. Same amlodipine dose. Keep measuring at home each morning.',
    },
    {
      id: 'ap-2',
      date: '2026-10-29',
      time: '09:30',
      place: 'Ang Mo Kio Family Clinic (demo)',
      purpose: 'BP review and medicine refill',
      who_goes: 'Kelvin',
      notes_after: '',
    },
  ],
  questions: [
    {
      id: 'q-1',
      text: 'His morning readings are higher than at the clinic. Which ones should we trust?',
      by: 'Wei Ling',
      added: '2026-10-10',
      asked: false,
      answer: '',
    },
    {
      id: 'q-2',
      text: 'Is it fine for him to take his pill after kopi instead of before breakfast?',
      by: 'Kelvin',
      added: '2026-10-11',
      asked: false,
      answer: '',
    },
  ],
  tasks: [
    { id: 't-1', title: 'Collect amlodipine refill from the clinic', due: '2026-10-27', owner: 'Kelvin', done: false, done_by: null },
    { id: 't-2', title: 'Buy new AA batteries for the BP monitor', due: '2026-10-25', owner: 'Wei Ling', done: false, done_by: null },
    { id: 't-3', title: 'Put the emergency card on the fridge', due: null, owner: null, done: true, done_by: 'Wei Ling' },
  ],
  prevention: { flu: '2025-10-04', pneumococcal: '2024-11-12', covid: '2025-11-20', kidney: '2026-04-02', healthier_sg: '2024-02-15' },
  emergency: {
    allergies: 'Penicillin (rash)',
    gp_name: 'Dr Lim, Ang Mo Kio Family Clinic (demo)',
    gp_phone: '6000 0000',
    home_address: 'Blk 999 Ang Mo Kio Ave 9, #05-123 (demo address)',
    notes: 'Lives alone on weekdays. Spare key with the neighbour at #05-125.',
  },
  updated_by: 'Wei Ling',
  updated_at: '2026-10-10T20:15:00+08:00',
};

const EMPTY_NOTES: CareNotes = {
  appointments: [],
  questions: [],
  tasks: [],
  prevention: {},
  emergency: { allergies: '', gp_name: '', gp_phone: '', home_address: '', notes: '' },
  updated_by: null,
  updated_at: null,
};

export function getCareNotes(seniorId: string): Promise<CareNotes> {
  try {
    const s = localStorage.getItem(NOTES_KEY(seniorId));
    if (s) return delay(JSON.parse(s));
  } catch {
    /* fall through */
  }
  return delay(structuredClone(seniorId === 'tan' ? SEEDED_TAN_NOTES : EMPTY_NOTES));
}

export function putCareNotes(seniorId: string, notes: CareNotes): Promise<CareNotes> {
  const out = { ...notes, updated_at: new Date().toISOString() };
  try {
    localStorage.setItem(NOTES_KEY(seniorId), JSON.stringify(out));
  } catch {
    /* storage unavailable: kept for this page only */
  }
  return delay(out);
}

// --- vent space (Nathan): anonymous caregiver rant room, kept in this browser ----------------

const VENT_KEY = 'careloop-mock-vent';

function ventSeed(): VentPost[] {
  const now = Date.now();
  const ago = (h: number) => new Date(now - h * 3600000).toISOString();
  return [
    { id: 'vp-demo-042', nickname: 'Caregiver 042', text: "Third time this week Pa refused to take his pill, I'm so tired", time: ago(2), hugs: 3, hidden: false },
    { id: 'vp-demo-128', nickname: 'Caregiver 128', text: 'Anyone else feel guilty for needing a break?', time: ago(5), hugs: 7, hidden: false },
    { id: 'vp-demo-077', nickname: 'Caregiver 077', text: "Mum said I don't care about her. I do everything for her. That hurt.", time: ago(27), hugs: 5, hidden: false },
    { id: 'vp-demo-214', nickname: 'Caregiver 214', text: 'Finally got 6 hours of sleep last night. Small wins.', time: ago(53), hugs: 12, hidden: false },
    { id: 'vp-demo-091', nickname: 'Caregiver 091', text: 'The doctor said her BP is improving. I was so relieved I cried.', time: ago(74), hugs: 8, hidden: false },
    { id: 'vp-demo-156', nickname: 'Caregiver 156', text: "Sometimes I wonder if I'm doing enough for him.", time: ago(126), hugs: 4, hidden: false },
  ];
}

function loadVent(): VentPost[] {
  try {
    const s = localStorage.getItem(VENT_KEY);
    if (s) return JSON.parse(s);
  } catch {
    /* fall through */
  }
  const seed = ventSeed();
  try {
    localStorage.setItem(VENT_KEY, JSON.stringify(seed));
  } catch {
    /* ignore */
  }
  return seed;
}

function saveVent(posts: VentPost[]) {
  try {
    localStorage.setItem(VENT_KEY, JSON.stringify(posts));
  } catch {
    /* ignore */
  }
}

export function getVentFeed(): Promise<VentPost[]> {
  const cutoff = new Date(Date.now() - 7 * 86400000).toISOString();
  return delay(
    loadVent()
      .filter((p) => !p.hidden && p.time >= cutoff)
      .sort((a, b) => b.time.localeCompare(a.time))
      .slice(0, 100),
  );
}

export function postVent(nickname: string, text: string): Promise<VentPost> {
  const posts = loadVent();
  const post: VentPost = {
    id: `vp-${Date.now()}`,
    nickname: nickname.trim(),
    text: text.trim(),
    time: new Date().toISOString(),
    hugs: 0,
    hidden: false,
  };
  posts.unshift(post);
  saveVent(posts);
  return delay(post);
}

export function hugVentPost(postId: string): Promise<VentPost> {
  const posts = loadVent();
  const p = posts.find((x) => x.id === postId);
  if (!p) return Promise.reject(new Error('post not found'));
  p.hugs++;
  saveVent(posts);
  return delay({ ...p });
}

export function reportVentPost(postId: string): Promise<{ id: string; hidden: boolean }> {
  const posts = loadVent();
  const p = posts.find((x) => x.id === postId);
  if (!p) return Promise.reject(new Error('post not found'));
  p.hidden = true;
  saveVent(posts);
  return delay({ id: postId, hidden: true });
}

// --- rota (GET/PUT/POST/DELETE /senior/{sid}/rota) -----------------------------------------

const mockRotas: Record<string, RotaView> = {
  tan: {
    rota: { id: 'rota-tan', senior_id: 'tan', mode: 'weekly', start_date: '2026-09-03', order: ['tan-weiling', 'tan-kelvin'], swaps: [] },
    on_duty: { id: 'tan-kelvin', name: 'Kelvin' },
  },
  teo: {
    rota: { id: 'rota-teo', senior_id: 'teo', mode: 'weekly', start_date: '2026-09-03', order: ['teo-kelvin', 'teo-jane'], swaps: [] },
    on_duty: { id: 'teo-kelvin', name: 'Kelvin' },
  },
  kaur: {
    rota: { id: 'rota-kaur', senior_id: 'kaur', mode: 'weekly', start_date: '2026-09-03', order: ['kaur-priya', 'kaur-arjun'], swaps: [] },
    on_duty: { id: 'kaur-priya', name: 'Priya' },
  },
  rahman: {
    rota: { id: 'rota-rahman', senior_id: 'rahman', mode: 'weekly', start_date: '2026-09-03', order: ['rahman-nur', 'rahman-maria'], swaps: [] },
    on_duty: { id: 'rahman-nur', name: 'Nur' },
  },
  chua: {
    rota: { id: 'rota-chua', senior_id: 'chua', mode: 'weekly', start_date: '2026-09-03', order: ['chua-junjie', 'chua-huimin'], swaps: [] },
    on_duty: { id: 'chua-junjie', name: 'Jun Jie' },
  },
};

export function getRota(seniorId: string): Promise<RotaView> {
  const rv = mockRotas[seniorId] ?? { rota: null, on_duty: null };
  return delay(structuredClone(rv));
}

export function putRota(seniorId: string, mode: 'weekly' | 'daily', startDate: string, order: string[]): Promise<RotaView> {
  const firstContact = allContacts.get(order[0]);
  const rv: RotaView = {
    rota: { id: `rota-${seniorId}`, senior_id: seniorId, mode, start_date: startDate, order, swaps: [] },
    on_duty: firstContact ? { id: firstContact.id, name: firstContact.name } : null,
  };
  mockRotas[seniorId] = rv;
  return delay(structuredClone(rv));
}

export function swapRota(seniorId: string, date: string, contactId: string): Promise<RotaView> {
  const rv = mockRotas[seniorId] ?? {
    rota: { id: `rota-${seniorId}`, senior_id: seniorId, mode: 'weekly', start_date: '2026-09-03', order: [contactId], swaps: [] },
    on_duty: null,
  };
  const swaps = (rv.rota?.swaps ?? []).filter((s) => s.date !== date);
  swaps.push({ date, contact_id: contactId });
  if (rv.rota) rv.rota.swaps = swaps;
  const c = allContacts.get(contactId);
  if (c) rv.on_duty = { id: c.id, name: c.name };
  mockRotas[seniorId] = rv;
  return delay(structuredClone(rv));
}

export function deleteRota(seniorId: string): Promise<RotaView> {
  mockRotas[seniorId] = { rota: null, on_duty: null };
  return delay({ rota: null, on_duty: null });
}

// Connected devices for seniors with Health Connect or Apple Health in demo.py
export function getHealthSync(seniorId: string, days = 7): Promise<HealthSyncView> {
  const prof = SENIOR_PROFILES[seniorId];
  if (!prof?.device) {
    return delay({ connected: false, status: null, days: [], shares_readings: true, shares_activity: true });
  }
  const today = new Date('2026-10-24T22:30:00+08:00');
  const [bSys, bDia] = prof.base_bp;
  const hasCuff = prof.device.apps.some((a) => /omron/i.test(a));
  const rows = Array.from({ length: days }, (_, i) => {
    const d = new Date(today.getTime() - (days - 1 - i) * 86400000).toISOString().slice(0, 10);
    const sys = seniorId === 'tan' ? 140 + i * 2 : bSys + ((i % 3) - 1);
    const dia = seniorId === 'tan' ? 85 + i : bDia + ((i % 2) - 1);
    return {
      date: d,
      steps: Math.max(1200, prof.steps + [-220, 190, 410, -150, 300, -80, 110][i % 7]),
      resting_hr: prof.device!.hr + [-1, 1, 0, 2, -2, 0, 1][i % 7],
      sleep_hours: [6.9, 6.2, 7.4, 6.6, 7.1, 5.9, 6.8][i % 7],
      bp: hasCuff && prof.consent.family_sees === 'readings' ? [{ time: `${d}T08:05:00+08:00`, systolic: sys, diastolic: dia }] : [],
    };
  });
  return delay({
    connected: true,
    status: {
      platform: prof.device.platform,
      platform_name: prof.device.platform_name,
      apps: prof.device.apps,
      kinds: hasCuff ? ['blood pressure', 'heart rate', 'sleep', 'steps'] : ['heart rate', 'sleep', 'steps'],
      last_sync: today.toISOString(),
      last_batch: { records: 19, readings: hasCuff ? 4 : 3, skipped: 0 },
    },
    days: rows,
    shares_readings: prof.consent.family_sees === 'readings',
    shares_activity: prof.consent.share_activity,
  });
}

export function demoHealthSyncMock(seniorId: string, bp?: [number, number]): Promise<HealthSyncResult> {
  const prof = SENIOR_PROFILES[seniorId] ?? SENIOR_PROFILES.tan;
  const dev = prof.device ?? { platform: 'health_connect' as const, platform_name: 'Health Connect', apps: ['Fitbit', 'OMRON connect'], hr: 68 };
  const crisis = bp && (bp[0] >= 180 || bp[1] >= 110);
  return delay({
    status: {
      platform: dev.platform,
      platform_name: dev.platform_name,
      apps: dev.apps,
      kinds: ['blood pressure', 'heart rate', 'sleep', 'steps'],
      last_sync: new Date().toISOString(),
      last_batch: { records: 12, readings: bp ? 4 : 3, skipped: 0 },
    },
    imported: { steps: 1, heart_rate: 1, sleep: 1, ...(bp ? { bp: 1 } : {}) },
    days: ['2026-10-24'],
    skipped: 0,
    rung: crisis ? 'R' : '0',
    message: crisis ? { text: 'Blood pressure at crisis level — please rest and check on them.' } : null,
  });
}

export function demoAdvanceMock(days: number): Promise<{ today: string }> {
  mockDayOffset = Math.min(14, mockDayOffset + days);
  const d = new Date(Date.UTC(2026, 9, 13 + mockDayOffset)).toISOString().slice(0, 10);
  return delay({ today: d });
}

export function demoResetMock(): Promise<{ today: string }> {
  mockDayOffset = 0;
  claims.clear();
  return delay({ today: '2026-10-13' });
}

const MED_NOTES: Record<string, { group: string; what_for: string; how_it_helps: string; look_out_for: string[] }> = {
  amlodipine: {
    group: 'BP',
    what_for: 'Lowers blood pressure.',
    how_it_helps: 'It relaxes the blood vessels so blood flows more easily.',
    look_out_for: ['Swollen ankles can happen. Tell your doctor if they bother you.', 'Some people feel flushed or get a headache at first.'],
  },
  telmisartan: {
    group: 'BP',
    what_for: 'Lowers blood pressure and protects the kidneys.',
    how_it_helps: 'It keeps blood vessels relaxed so the heart does not have to pump as hard.',
    look_out_for: ['Feeling dizzy when standing up quickly — get up slowly from bed or a chair.'],
  },
  losartan: {
    group: 'BP',
    what_for: 'Lowers blood pressure and protects the kidneys.',
    how_it_helps: 'It blocks a signal that tightens blood vessels.',
    look_out_for: ['Dizziness when standing up quickly — rise slowly.'],
  },
  atorvastatin: {
    group: 'Cholesterol',
    what_for: 'Lowers cholesterol to protect the heart and blood vessels.',
    how_it_helps: 'It reduces the amount of cholesterol the liver makes.',
    look_out_for: ['Avoid large amounts of grapefruit or pomelo juice.', 'Tell your doctor if you get unusual muscle aches.'],
  },
  metformin: {
    group: 'Blood sugar',
    what_for: 'Helps control blood sugar in type 2 diabetes.',
    how_it_helps: 'It helps the body use insulin better, especially after meals.',
    look_out_for: ['Take with or just after meals to reduce stomach upset.'],
  },
  bisoprolol: {
    group: 'BP / Heart',
    what_for: 'Lowers blood pressure and steadies the heartbeat.',
    how_it_helps: 'It slows the heart rate slightly so the heart works more gently.',
    look_out_for: ['Do not stop suddenly without checking with your doctor.'],
  },
  hydrochlorothiazide: {
    group: 'BP (water tablet)',
    what_for: 'Lowers blood pressure by helping the body pass extra salt and water.',
    how_it_helps: 'Taken in the morning so you do not have to wake up at night to pass urine.',
    look_out_for: ['Can make you pass urine more often in the morning.'],
  },
  'aspirin (low dose)': {
    group: 'Heart protection',
    what_for: 'Helps prevent blood clots.',
    how_it_helps: 'Makes platelets in the blood less sticky.',
    look_out_for: ['Take after food to protect the stomach.'],
  },
};

export function getMedicines(seniorId = 'tan', _lang = 'en'): Promise<MedicinesView> {
  const prof = SENIOR_PROFILES[seniorId] ?? SENIOR_PROFILES.tan;
  return delay({
    medicines: prof.medicines.map((m) => {
      const info = MED_NOTES[m.name.toLowerCase()];
      return {
        name: m.name,
        dose_text: m.dose_text,
        when: m.schedule.map((s) => `in the ${s}`),
        for_bp: m.for_bp,
        known: !!info,
        generic: info ? m.name.toLowerCase() : null,
        group: info?.group ?? null,
        what_for: info?.what_for ?? 'Prescribed medicine — check your pharmacy label or ask your pharmacist.',
        how_it_helps: info?.how_it_helps ?? null,
        look_out_for: info?.look_out_for ?? [],
      };
    }),
    always: 'Take it as on your label, even on days you feel well. If anything on this page worries you, ask your pharmacist or doctor.',
    note: 'Plain-language notes for the demo, from standard patient-leaflet wording. PLACEHOLDER until a pharmacist or the medical student checks them.',
  });
}

export function getPrevention(_seniorId = 'tan', _lang = 'en'): Promise<PreventionView> {
  const item = (
    id: string,
    title: string,
    why: string,
    where: string,
    status: 'due' | 'done' | 'not_recorded' | 'booked',
    status_text: string,
    last_done: string | null,
    next_due: string | null,
  ) => ({ id, title, why, where, every_days: 365, last_done, next_due, status, status_text, placeholder: false });
  return delay({
    items: [
      item('flu', 'Flu vaccine', "Flu is more serious for older adults. The vaccine changes each year, so it's once a year.", 'Polyclinic, a CHAS or Healthier SG clinic, or some pharmacies', 'due', 'Due', '2025-10-04', '2026-10-04'),
      item('fit', 'Bowel cancer screening (FIT kit)', 'A simple stool test done at home, once a year from 50.', 'Collect a kit at a Healthier SG clinic', 'not_recorded', 'Not recorded yet', null, null),
      item('pneumococcal', 'Pneumococcal vaccine', 'Protects against a common cause of pneumonia. Recommended once from 65.', 'Polyclinic or a CHAS or Healthier SG clinic', 'done', 'Done', '2024-11-12', null),
    ],
    note: "For adults 65 and over with high blood pressure. Vaccines from MOH's adult immunisation schedule; screenings from Screen for Life.",
  });
}
