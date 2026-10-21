// Things to do near the senior, pulled in automatically: their own AAC's programmes this week, the nearest
// AACs and community clubs (data.gov.sg), Qloo Taste AI cross-domain recommendations filtered by health/weather
// constraints, what CareLoop suggested today and how the senior has answered.
// Nothing here is booked: the senior picks, and a "not for me" is remembered.
import { useEffect, useState } from 'react';
import type { Activities, TasteVisitKit } from '../shared/contract';
import { addSeniorTaste, getActivities, searchTaste, type TasteSearchResult } from '../shared/api';
import { REFRESH_EVENT, useRefreshTick } from './live';

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;
const DAY_LABEL: Record<string, string> = { mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun' };
const fmt = (d: string) => new Date(d).toLocaleDateString('en-SG', { weekday: 'short', day: 'numeric', month: 'short' });
// Programme times come as "2pm", "8:30am" or "14:00". Minutes after midnight, for sorting.
export function timeKey(t: string): number {
  const m = t.trim().toLowerCase().match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);
  if (!m) return 24 * 60;
  let h = +m[1] % 12;
  if (m[3] === 'pm') h += 12;
  if (!m[3] && +m[1] >= 12) h = +m[1];
  return h * 60 + (m[2] ? +m[2] : 0);
}

const map = (lat: number, lon: number) => `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;

export function useActivities(seniorId: string, contactId?: string) {
  const [data, setData] = useState<Activities | null | undefined>(undefined);
  const tick = useRefreshTick();
  useEffect(() => {
    getActivities(seniorId, contactId).then(setData, () => setData(null));
  }, [seniorId, contactId, tick]);
  return data;
}

export default function ActivitiesView({ seniorId, contactId, name, compact }: { seniorId: string; contactId?: string; name: string; compact?: boolean }) {
  const a = useActivities(seniorId, contactId);
  if (a === undefined) return <p className="care-muted">Finding things to do nearby…</p>;
  if (!a) return <p className="care-muted">Couldn't load activities.</p>;
  const going = a.suggestions.filter((s) => s.response === 'going').length;
  const notForMe = a.suggestions.filter((s) => s.response === 'not_for_me').length;
  const tp = a.taste_plan;

  return (
    <>
      {a.indoor_only && (
        <p className="care-notice">
          {a.why_indoor === 'rain' ? `Rain today (${a.rain_mm} mm nearby)` : `Haze today (PSI ${a.psi})`}: CareLoop is only suggesting indoor options.
        </p>
      )}

      <section className="care-card">
        <h2>Suggested to {name} today</h2>
        <p className="care-muted">
          Picked by CareLoop's taste agent and safety rules from what {name} likes{a.likes.length ? ` (${a.likes.join(', ')})` : ''}: their own centre first, Qloo cross-domain taste matches, then the nearest community club.
        </p>
        <ul className="act-list">
          {a.suggested_today.map((s, i) => (
            <li key={i} className="act-item">
              <span className={`act-kind is-${s.kind}`}>{s.kind === 'cc' ? 'CC' : s.kind === 'aac' ? 'AAC' : 'Programme'}</span>
              <span className="act-body">
                <strong>{s.place}</strong>
                <span className="care-muted">
                  {s.why_it_fits} · {s.indoor ? 'Indoor' : 'Outdoor'}
                  {s.sample && ' · sample timetable'}
                </span>
              </span>
            </li>
          ))}
        </ul>
        {(going > 0 || notForMe > 0) && (
          <p className="care-muted">Last two weeks: said "going" {going} time{going === 1 ? '' : 's'}, "not for me" {notForMe}. A "not for me" isn't suggested again.</p>
        )}
      </section>

      {tp && (
        <section className="care-card">
          <h2>CareLoop + Qloo taste graph for {name}</h2>
          <p className="care-muted">{tp.profile.summary}</p>
          {tp.constraints.badges.length > 0 && (
            <p className="care-muted">
              <strong>Active health & weather filters:</strong> {tp.constraints.badges.join(' · ')}
            </p>
          )}
          <ul className="act-list">
            {tp.recommendations.places.map((p) => (
              <li key={p.entity_id} className="act-item">
                <span className="act-kind is-programme">Food & Place</span>
                <span className="act-body">
                  <strong>{p.name}</strong>
                  <span className="care-muted">
                    {p.why} · {Math.round(p.affinity * 100)}% Qloo match
                    {p.fit_badges.length > 0 ? ` · ${p.fit_badges.join(', ')}` : ''}
                  </span>
                  {p.bridge && (
                    <span className="care-muted" style={{ display: 'block', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                      <code>Bridge:</code> {p.bridge.path_label}
                    </span>
                  )}
                </span>
              </li>
            ))}
            {tp.recommendations.music.map((m) => (
              <li key={m.entity_id} className="act-item">
                <span className="act-kind is-aac">Music</span>
                <span className="act-body">
                  <strong>{m.name}</strong>
                  <span className="care-muted">
                    {m.why} · {Math.round(m.affinity * 100)}% Qloo match
                  </span>
                  {m.bridge && (
                    <span className="care-muted" style={{ display: 'block', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                      <code>Bridge:</code> {m.bridge.path_label}
                    </span>
                  )}
                </span>
              </li>
            ))}
            {tp.recommendations.movies.map((mv) => (
              <li key={mv.entity_id} className="act-item">
                <span className="act-kind is-cc">Classic Film</span>
                <span className="act-body">
                  <strong>{mv.name}</strong>
                  <span className="care-muted">
                    {mv.why} · {Math.round(mv.affinity * 100)}% Qloo match
                  </span>
                  {mv.bridge && (
                    <span className="care-muted" style={{ display: 'block', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                      <code>Bridge:</code> {mv.bridge.path_label}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>

          {tp.visit_kit && (
            <FamilyVisitKitCard name={name} kit={tp.visit_kit} />
          )}

          {tp.low_day_nudge && (
            <details className="care-card decision-info" style={{ marginTop: '0.5rem' }}>
              <summary>Rung-2 "Low Day" cultural nudge (when movement or contact dips for 1 day)</summary>
              <dl>
                <dt>Rule <code>{tp.low_day_nudge.rule_id ?? '2.low_day'}</code> (senior-only gentle suggestion, never alerts family)</dt>
                <dd>
                  <p style={{ margin: '0.25rem 0' }}>{tp.low_day_nudge.nudge_text ?? tp.low_day_nudge.text}</p>
                  <p className="care-muted" style={{ margin: '0.25rem 0 0' }}>
                    <strong>Place / Treat:</strong> {tp.low_day_nudge.place_pick ?? tp.low_day_nudge.place}
                    {(tp.low_day_nudge.music_companion ?? tp.low_day_nudge.music) ? ` · Companion song: ${tp.low_day_nudge.music_companion ?? tp.low_day_nudge.music}` : ''}
                    {tp.low_day_nudge.film_companion ? ` · Film: ${tp.low_day_nudge.film_companion}` : ''}
                  </p>
                </dd>
              </dl>
            </details>
          )}

          <details className="care-card decision-info" style={{ marginTop: '0.75rem' }}>
            <summary>How this was picked (Qloo agent steps & health guardrails)</summary>
            <dl>
              {tp.trace.map((st) => (
                <div key={st.step}>
                  <dt>
                    Step {st.step}: <code>{st.tool}</code> — {st.title}
                  </dt>
                  <dd>
                    {st.output_summary}
                    {st.details.length > 0 && (
                      <ul className="care-muted" style={{ margin: '0.25rem 0 0.5rem 1.1rem', padding: 0 }}>
                        {st.details.map((d, idx) => (
                          <li key={idx}>{d}</li>
                        ))}
                      </ul>
                    )}
                  </dd>
                </div>
              ))}
              <dt>Safety boundary</dt>
              <dd>
                CareLoop's Qloo agent works only at the suggestion level. Escalation rungs (0–4 and R) and who gets contacted are always decided by deterministic rules, and every explanation string passes <code>guardrail.py</code>.
              </dd>
            </dl>
          </details>

          <details className="care-card decision-info" style={{ marginTop: '0.5rem' }}>
            <summary>Add a favourite for {name} (via Qloo search)</summary>
            <QlooFavouriteBox seniorId={seniorId} name={name} />
          </details>
          <details className="care-card decision-info" style={{ marginTop: '0.5rem' }}>
            <summary>Why Qloo? (LLM-only baseline vs CareLoop + Qloo)</summary>
            <dl>
              <dt>Prompt-only LLM baseline (without Qloo or health filter tools)</dt>
              <dd>
                <ul className="care-muted" style={{ margin: '0.25rem 0 0.5rem 1.1rem', padding: 0 }}>
                  {tp.comparison.llm_only.generic_picks.map((g, i) => (
                    <li key={i}>{g}</li>
                  ))}
                </ul>
                <strong>Where LLM-only falls short:</strong>
                <ul className="care-muted" style={{ margin: '0.25rem 0 0.5rem 1.1rem', padding: 0 }}>
                  {tp.comparison.llm_only.limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </dd>
              <dt>CareLoop + Qloo Taste AI + deterministic health rules</dt>
              <dd>
                <ul className="care-muted" style={{ margin: '0.25rem 0 0.5rem 1.1rem', padding: 0 }}>
                  {tp.comparison.careloop_with_qloo.picks.map((pk, i) => (
                    <li key={i}>{pk}</li>
                  ))}
                </ul>
                {tp.comparison.careloop_with_qloo.filtered_examples.length > 0 && (
                  <span>
                    <strong>Filtered out for safety:</strong> {tp.comparison.careloop_with_qloo.filtered_examples.join('; ')}.
                  </span>
                )}
              </dd>
            </dl>
          </details>
        </section>
      )}

      {a.own_aac && (
        <section className="care-card">
          <h2>This week at {a.own_aac.name}</h2>
          <p className="care-muted">{a.own_aac.address}</p>
          <div className="week">
            {DAYS.map((d) => {
              const items = a.own_aac!.programmes.filter((p) => p.weekdays.includes(d) && !p.hidden).sort((x, y) => timeKey(x.time) - timeKey(y.time));
              return (
                <div key={d} className={`week-day ${d === a.weekday ? 'is-today' : ''}`}>
                  <span className="week-label">{DAY_LABEL[d]}{d === a.weekday ? ' · today' : ''}</span>
                  {items.length ? (
                    items.map((p) => (
                      <span key={p.id} className={`week-prog ${p.fits ? 'is-fit' : ''} ${a.indoor_only && !p.indoor ? 'is-out' : ''}`}>
                        <span className="week-time">{p.time}</span> {p.title}
                        {p.fits && <span className="week-fit">likes {p.fits}</span>}
                      </span>
                    ))
                  ) : (
                    <span className="care-muted week-none">–</span>
                  )}
                </div>
              );
            })}
          </div>
          {a.own_aac.programmes.some((p) => p.sample) && <p className="care-muted">Sample timetable: the centre hasn't entered its own yet.</p>}
        </section>
      )}

      {!compact && (
        <section className="care-card">
          <h2>Nearby</h2>
          <p className="care-muted">Distances from {a.distance_from}, as the crow flies.</p>
          <ul className="act-list">
            {[...a.nearby_ccs, ...a.nearby_aacs]
              .sort((x, y) => x.km - y.km)
              .map((p) => (
                <li key={p.id} className="act-item">
                  <span className={`act-kind is-${p.kind}`}>{p.kind === 'cc' ? 'CC' : 'AAC'}</span>
                  <span className="act-body">
                    <strong>{p.name}</strong>
                    <span className="care-muted">
                      {p.km} km · {p.address}
                    </span>
                  </span>
                  <a className="care-link act-map" href={map(p.lat, p.lon)} target="_blank" rel="noreferrer">
                    Map
                  </a>
                </li>
              ))}
          </ul>
        </section>
      )}

      {!compact && a.suggestions.length > 0 && (
        <section className="care-card">
          <h2>Recent suggestions</h2>
          <ul className="act-list">
            {a.suggestions.slice(0, 8).map((s) => (
              <li key={s.id} className="act-item">
                <span className="act-date">{fmt(s.date)}</span>
                <span className="act-body">
                  <strong>{s.place}</strong>
                  <span className="care-muted">{s.why_it_fits}</span>
                </span>
                <span className={`act-resp is-${s.response ?? 'none'}`}>
                  {s.response === 'going' ? 'Going' : s.response === 'not_for_me' ? 'Not for me' : 'No answer'}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {!compact && <p className="care-muted care-source">{a.source}</p>}
    </>
  );
}

function QlooFavouriteBox({ seniorId, name }: { seniorId: string; name: string }) {
  const [q, setQ] = useState('');
  const [results, setResults] = useState<TasteSearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [addedMsg, setAddedMsg] = useState<string | null>(null);

  const onSearch = async () => {
    if (!q.trim()) return;
    setBusy(true);
    try {
      const r = await searchTaste(q.trim());
      setResults(r.results);
    } finally {
      setBusy(false);
    }
  };

  const onAdd = async (seed: string) => {
    setBusy(true);
    try {
      await addSeniorTaste(seniorId, seed);
      setAddedMsg(`Added "${seed}" to ${name}'s taste seeds.`);
      setQ('');
      setResults([]);
      window.dispatchEvent(new Event(REFRESH_EVENT));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ marginTop: '0.5rem', display: 'grid', gap: '0.5rem' }}>
      <p className="care-muted" style={{ margin: 0 }}>
        Search Qloo's taste graph for a singer, dish, classic film or hawker centre {name} is fond of.
      </p>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. Frances Yip, P. Ramlee, fish soup…"
          aria-label="Search Qloo entities"
          style={{ flex: 1, minWidth: '180px' }}
        />
        <button type="button" className="care-secondary" disabled={busy || !q.trim()} onClick={onSearch}>
          Search Qloo
        </button>
        <button type="button" className="care-primary" disabled={busy || !q.trim()} onClick={() => onAdd(q.trim())}>
          Add directly
        </button>
      </div>
      {results.length > 0 && (
        <ul className="act-list" style={{ margin: 0 }}>
          {results.map((r) => (
            <li key={r.entity_id} className="act-item">
              <span className="act-kind is-programme">{r.type.replace('urn:entity:', '')}</span>
              <span className="act-body">
                <strong>{r.name}</strong>
                <span className="care-muted">{r.entity_id}</span>
              </span>
              <button type="button" className="care-link" disabled={busy} onClick={() => onAdd(r.name)}>
                + Add
              </button>
            </li>
          ))}
        </ul>
      )}
      {addedMsg && <p className="care-muted" style={{ margin: 0 }}>{addedMsg}</p>}
    </div>
  );
}

function FamilyVisitKitCard({ name, kit }: { name: string; kit: TasteVisitKit }) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(kit.whatsapp_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      /* ignore if clipboard unavailable */
    }
  };

  const waUrl = `https://wa.me/?text=${encodeURIComponent(kit.whatsapp_text)}`;

  return (
    <div className="care-card" style={{ marginTop: '0.75rem', background: 'var(--bg-soft, #faf8f5)' }}>
      <h3 style={{ margin: '0 0 0.25rem', fontSize: '0.98rem' }}>Bringing something over? Family Visit Kit for {name}</h3>
      <p className="care-muted" style={{ margin: '0 0 0.5rem' }}>{kit.summary}</p>
      <ul className="care-muted" style={{ margin: '0 0 0.6rem 1.1rem', padding: 0 }}>
        {kit.treat && (
          <li>
            <strong>Safe treat to tapao:</strong> {kit.treat}
          </li>
        )}
        {kit.music && (
          <li>
            <strong>Put on during visit:</strong> {kit.music}
          </li>
        )}
        {kit.film && (
          <li>
            <strong>Watch together:</strong> {kit.film}
          </li>
        )}
        <li>
          <strong>Safety check:</strong> {kit.safety_note}
        </li>
      </ul>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button type="button" className="care-secondary" onClick={onCopy}>
          {copied ? 'Copied for WhatsApp!' : 'Copy for Family WhatsApp'}
        </button>
        <a className="care-link" href={waUrl} target="_blank" rel="noreferrer" style={{ alignSelf: 'center' }}>
          Share on WhatsApp ↗
        </a>
      </div>
    </div>
  );
}
