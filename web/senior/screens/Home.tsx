// Home: the three daily buttons, the hold-to-talk mic, the morning check-in, haze line and suggestions.
import { useContext, useEffect, useState } from 'react';
import { getSeniorMemories, postSeniorMemory } from '../../shared/api';
import type { MemoryLaneResponse } from '../../shared/contract';
import { LangContext, dateLocale, speechLang, useT } from '../../shared/i18n';
import type { Today } from '../types';
import { BigButton, Icon, TalkButton } from '../ui';

export function Home({ today, busy, talkSupported, listening, interim, onPills, onBP, onFeel, onTalkStart, onTalkStop, onGoing, onNotForMe, onKnows, onMeds }: {
  today: Today;
  busy: boolean;
  talkSupported: boolean;
  listening: boolean;
  interim: string;
  onPills: () => void;
  onBP: () => void;
  onFeel: () => void;
  onTalkStart: () => void;
  onTalkStop: () => void;
  onGoing: (id: string) => void;
  onNotForMe: (id: string) => void;
  onKnows: () => void;
  onMeds: () => void;
}) {
  const t = useT();
  const comma = useContext(LangContext) === 'zh' ? '，' : ', ';
  const hour = new Date().getHours();
  const greeting = t(hour < 12 ? 'home.greeting.morning' : hour < 18 ? 'home.greeting.afternoon' : 'home.greeting.evening');
  const lang = useContext(LangContext);
  const complete = [today.pills_taken, today.bp_logged, today.feel_logged].filter(Boolean).length;
  const date = new Date(today.date ? `${today.date}T12:00:00` : Date.now()).toLocaleDateString(dateLocale(lang), { weekday: 'long', day: 'numeric', month: 'long' });

  const speakText = (text: string) => {
    try {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = speechLang(lang);
        u.rate = 0.92;
        window.speechSynthesis.speak(u);
      }
    } catch {
      /* ignore TTS errors on unsupported browsers */
    }
  };

  return (
    <div className="sa-home">
      <div className="sa-welcome"><p className="sa-date">{date}</p><h1 className="sa-greeting">{greeting}{today.senior.name ? comma + today.senior.name : ''}</h1><p className="sa-welcome-note">{t('home.subtitle')}</p><span className="sa-sun" aria-hidden="true">☀</span></div>
      <div className="sa-home-grid"><section className="sa-daily">
      <div className="sa-daily-head"><h2>{t('home.today')}</h2><span>{t('home.progress', { count: complete })}</span></div>
      <div className="sa-progress" aria-hidden="true">{[0,1,2].map((i) => <span key={i} className={i < complete ? 'is-complete' : ''} />)}</div>

      {today.checkin_due && (
        <div className="sa-card sa-checkin">
          <p className="sa-card-label">{t('checkin.title')}</p>
          {/* The engine's question, never a number. */}
          <p className="sa-prompt">{today.prompt?.text || t('checkin.default')}</p>
        </div>
      )}

      <div className="sa-buttons">
        <BigButton icon={Icon.pill} label={t(today.pills_taken ? 'home.pills.done' : 'home.pills')} done={today.pills_taken} onClick={onPills} disabled={busy} />
        <BigButton icon={Icon.heart} label={t(today.bp_logged ? 'home.bp.done' : 'home.bp')} done={today.bp_logged} onClick={onBP} disabled={busy} />
        <BigButton icon={Icon.smile} label={t('home.feel')} done={today.feel_logged} onClick={onFeel} disabled={busy} />
      </div>

      {talkSupported ? <TalkButton disabled={busy} listening={listening} onStart={onTalkStart} onStop={onTalkStop}
        label={listening ? t('checkin.release') : t('home.talk')} /> : <BigButton tone="primary" icon={Icon.list} label={t('home.type')} onClick={onFeel} disabled={busy} />}
      {talkSupported && <button type="button" className="sa-type-link" onClick={onFeel} disabled={busy}>{t('home.type')}</button>}
      {listening && <p className="sa-interim" aria-live="polite">{interim || t('checkin.listening')}</p>}
      {busy && <p className="sa-note" role="status">{t('common.saving')}</p>}
      </section><aside className="sa-beside">

      {today.haze && (
        <div className="sa-card sa-haze">
          <p className="sa-card-label"><span aria-hidden>{Icon.cloud}</span> {t('haze.title')}</p>
          <p>{today.haze.text}</p>
        </div>
      )}

      {today.suggestions.length > 0 && (
        <div className="sa-card">
          <p className="sa-card-label">{t('suggest.title')}</p>
          <ul className="sa-suggestions">
            {today.suggestions.slice(0, 3).map((s) => (
              <li key={s.id} style={{ flexDirection: 'column', alignItems: 'stretch', gap: 8 }}>
                <div>
                  <p className="sa-place">{s.place}</p>
                  <p className="sa-why">
                    {s.why_it_fits}
                    {s.indoor && <span className="sa-tag">{t('suggest.indoor')}</span>}
                    {s.free && <span className="sa-tag">{t('suggest.free')}</span>}
                  </p>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  <button
                    type="button"
                    className="sa-notforme"
                    style={s.response === 'going' ? { background: '#0b6e4f', color: '#fff', borderColor: '#0b6e4f' } : { borderColor: '#0b6e4f', color: '#0b6e4f' }}
                    onClick={() => onGoing(s.id)}
                  >
                    {s.response === 'going' ? `✓ ${t('suggest.going')}` : t('suggest.going')}
                  </button>
                  <button type="button" className="sa-notforme" onClick={() => onNotForMe(s.id)}>{t('suggest.notForMe')}</button>
                  <button
                    type="button"
                    className="sa-notforme"
                    onClick={() => speakText(`${s.place}. ${s.why_it_fits}`)}
                  >
                    {t('suggest.readAloud')}
                  </button>
                  <a
                    className="sa-notforme"
                    style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.place + ' Singapore')}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {t('suggest.map')} ↗
                  </a>
                </div>
              </li>
            ))}
          </ul>
          {today.taste_plan && (
            <details className="sa-taste-trace" style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(0,0,0,0.08)', fontSize: '0.92rem' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600 }}>{t('suggest.howPicked')}</summary>
              <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
                {today.taste_plan.recommendations.music.map((m) => (
                  <p key={m.entity_id} className="sa-why" style={{ margin: 0 }}>
                    <strong>{t('suggest.music')}</strong> {m.name} — {m.why}
                    {m.bridge ? ` (${m.bridge.path_label})` : ''}{' '}
                    <a
                      href={`https://www.youtube.com/results?search_query=${encodeURIComponent(m.name)}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: '#0b6e4f', fontWeight: 600, marginLeft: 4 }}
                    >
                      {t('suggest.listen')} ↗
                    </a>
                  </p>
                ))}
                {today.taste_plan.recommendations.movies.map((mv) => (
                  <p key={mv.entity_id} className="sa-why" style={{ margin: 0 }}>
                    <strong>{t('suggest.film')}</strong> {mv.name} — {mv.why}
                    {mv.bridge ? ` (${mv.bridge.path_label})` : ''}{' '}
                    <a
                      href={`https://www.youtube.com/results?search_query=${encodeURIComponent(mv.name)}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: '#0b6e4f', fontWeight: 600, marginLeft: 4 }}
                    >
                      {t('suggest.watch')} ↗
                    </a>
                  </p>
                ))}
                {today.taste_plan.filtered_out.length > 0 && (
                  <p className="sa-why" style={{ margin: 0 }}>
                    <strong>{t('suggest.filtered')}</strong> {today.taste_plan.filtered_out.map((f) => `${f.name} (${f.reason})`).join('; ')}
                  </p>
                )}
              </div>
            </details>
          )}
        </div>
      )}

      <SeniorReminiscenceCard seniorId={today.senior.id} lang={lang} onSpeak={speakText} />

      <button className="sa-link" onClick={onMeds}><span aria-hidden>{Icon.pill}</span> {t('home.meds')}</button>
      <button className="sa-link" onClick={onKnows}><span aria-hidden>{Icon.list}</span> {t('home.knows')}</button>
      </aside></div>
    </div>
  );
}

function SeniorReminiscenceCard({
  seniorId,
  lang,
  onSpeak,
}: {
  seniorId: string;
  lang: string;
  onSpeak: (text: string) => void;
}) {
  const [lane, setLane] = useState<MemoryLaneResponse | null>(null);
  const [story, setStory] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedBanner, setSavedBanner] = useState(false);

  useEffect(() => {
    getSeniorMemories(seniorId, lang).then(setLane, () => setLane(null));
  }, [seniorId, lang]);

  if (!lane) return null;

  const titleLabel =
    lang === 'zh'
      ? '今日怀旧故事 (Qloo 记忆回廊)'
      : lang === 'ms'
        ? 'Kenangan Hari Ini (Qloo Memory Lane)'
        : lang === 'ta'
          ? 'இன்றைய நினைவுகள் (Qloo Memory Lane)'
          : 'Memory Lane — Today’s Story Prompt';

  const saveLabel =
    lang === 'zh'
      ? '保存到家庭纪念册'
      : lang === 'ms'
        ? 'Simpan Cerita Keluarga'
        : lang === 'ta'
          ? 'குடும்ப நினைவுகளில் சேமி'
          : 'Save Story for Family';

  const onSave = async () => {
    if (!story.trim()) return;
    setSaving(true);
    try {
      await postSeniorMemory(seniorId, {
        story_text: story.trim(),
        qloo_seed: lane.daily_prompt.qloo_seed,
        prompt: lane.daily_prompt.prompt,
        recorded_by: `${lane.senior_name} (Senior App)`,
        language: lang,
      });
      setStory('');
      setSavedBanner(true);
      setTimeout(() => setSavedBanner(false), 3000);
      const updated = await getSeniorMemories(seniorId, lang);
      setLane(updated);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="sa-card" style={{ marginTop: 12 }}>
      <p className="sa-card-label">{titleLabel}</p>
      <p className="sa-place" style={{ fontSize: '1.02rem', marginBottom: 6 }}>
        {lane.daily_prompt.prompt}
      </p>
      <p className="sa-why" style={{ marginBottom: 8 }}>
        {lane.daily_prompt.qloo_seed} · {lane.daily_prompt.film_companion}
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
        <button
          type="button"
          className="sa-notforme"
          onClick={() => onSpeak(lane.daily_prompt.prompt)}
        >
          {lang === 'zh' ? '朗读问题' : 'Read prompt aloud'}
        </button>
        {lane.daily_prompt.starter_chips.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            className="sa-notforme"
            onClick={() => setStory((prev) => (prev ? `${prev} ${chip}` : chip))}
          >
            + {chip}
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <input
          type="text"
          value={story}
          onChange={(e) => setStory(e.target.value)}
          placeholder={lang === 'zh' ? '写下或说出您的当年回忆…' : 'Share a favourite memory for your family…'}
          aria-label="Share a memory"
          style={{
            flex: 1,
            minWidth: 180,
            padding: '0.55rem 0.7rem',
            borderRadius: 10,
            border: '1px solid rgba(0,0,0,0.18)',
            fontSize: '0.96rem',
          }}
        />
        <button
          type="button"
          className="sa-notforme"
          disabled={saving || !story.trim()}
          onClick={() => void onSave()}
          style={{ background: '#0b6e4f', color: '#fff', borderColor: '#0b6e4f', fontWeight: 600 }}
        >
          {saving ? '…' : saveLabel}
        </button>
      </div>
      {savedBanner && (
        <p className="sa-why" style={{ color: '#0b6e4f', fontWeight: 600, marginTop: 6 }}>
          ✓ {lang === 'zh' ? '已存入家庭纪念册！' : 'Saved to your Family Memory Lane Keepsake Book!'}
        </p>
      )}
      {lane.capsules.length > 0 && (
        <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid rgba(0,0,0,0.08)' }}>
          <p className="sa-why" style={{ margin: 0 }}>
            <strong>{lang === 'zh' ? '最新保存的故事：' : 'Latest saved keepsake:'}</strong> “{lane.capsules[0].story_text}”{' '}
            <span style={{ opacity: 0.75 }}>({lane.capsules[0].date})</span>
          </p>
        </div>
      )}
    </div>
  );
}
