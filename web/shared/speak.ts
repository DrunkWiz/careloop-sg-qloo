// Read text aloud with the most natural voice the browser has for the language.
// Left to itself, the browser picks its default voice, which on Windows is a robotic
// SAPI voice (Microsoft David or Zira). Edge's "Natural" voices, Chrome's Google voices
// and Apple's enhanced voices sound far better, so we look for those first.
import type { AppLang } from './i18n';

// Accents to try, best first. Singlish and English both prefer a Singapore voice.
const LOCALES: Record<string, string[]> = {
  en: ['en-SG', 'en-GB', 'en-AU', 'en-IN', 'en-US'],
  zh: ['zh-SG', 'zh-CN', 'zh-TW', 'zh-HK'],
  ms: ['ms-MY', 'ms-SG', 'id-ID'],
  ta: ['ta-SG', 'ta-IN', 'ta-MY'],
};
const NATURAL = /natural|neural|online|premium|enhanced|google|siri/i;
const ROBOTIC = /\b(david|mark|zira|hazel|george|susan|huihui|kangkang|yaoyao)\b|espeak/i;

let voices: SpeechSynthesisVoice[] = [];
function loadVoices() {
  voices = window.speechSynthesis.getVoices();
}
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  loadVoices();
  // Chrome fills the list in later.
  window.speechSynthesis.addEventListener?.('voiceschanged', loadVoices);
}

function score(v: SpeechSynthesisVoice, locales: string[]): number {
  const lang = v.lang.replace('_', '-');
  const i = locales.findIndex((l) => lang.toLowerCase() === l.toLowerCase());
  const base = locales[0].split('-')[0];
  if (i < 0 && !lang.toLowerCase().startsWith(base)) return -Infinity;
  let s = i < 0 ? 0 : (locales.length - i) * 2;  // closer accent first
  if (NATURAL.test(v.name)) s += 20;               // a natural voice beats a closer accent
  if (ROBOTIC.test(v.name)) s -= 5;
  if (!v.localService) s += 2;                     // online voices are usually neural
  return s;
}

/** The best voice for `lang`, or null to let the browser choose. */
export function pickVoice(lang: AppLang): SpeechSynthesisVoice | null {
  const locales = LOCALES[lang === 'en-SG' ? 'en' : lang] ?? LOCALES.en;
  let best: SpeechSynthesisVoice | null = null;
  let bestScore = -Infinity;
  for (const v of voices) {
    const s = score(v, locales);
    if (s > bestScore) { best = v; bestScore = s; }
  }
  return best;
}

export function speak(text: string, lang: AppLang): void {
  try {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const voice = pickVoice(lang);
    if (voice) { u.voice = voice; u.lang = voice.lang; }
    else u.lang = (LOCALES[lang === 'en-SG' ? 'en' : lang] ?? LOCALES.en)[0];
    // Natural voices already speak at an easy pace; slow the robotic ones a little more.
    u.rate = voice && NATURAL.test(voice.name) ? 0.95 : 0.88;
    window.speechSynthesis.speak(u);
  } catch {
    /* ignore TTS errors on unsupported browsers */
  }
}
