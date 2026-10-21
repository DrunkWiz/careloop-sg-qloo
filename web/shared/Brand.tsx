// href=null renders the mark without a link: the senior app uses that, so a stray tap never takes a senior
// out of their app to the public home page.
export default function Brand({ light = false, href = '/' }: { light?: boolean; href?: string | null }) {
  const inner = <>
    <span className="cl-brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M16 9C9 0 0 10 9 19l7 7 7-7C32 10 23 0 16 9Z" stroke="currentColor" strokeWidth="2.5"/><path d="M7 15h6l2-4 3 8 2-4h5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg></span>
    <span>Fondly</span>
  </>;
  if (href === null) return <span className={`cl-brand${light ? ' cl-brand-light' : ''}`} aria-label="Fondly">{inner}</span>;
  return <a className={`cl-brand${light ? ' cl-brand-light' : ''}`} href={href} aria-label="Fondly home">{inner}</a>;
}
