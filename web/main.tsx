import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './shared/tokens.css';
import SeniorApp from './senior/SeniorApp';
import CareApp from './care/CareApp';
import JudgeCommandCenter from './care/JudgeCommandCenter';
import EvalView from './care/EvalView';
import Welcome from './Welcome';
import { useRoute } from './care/live';
import { doorFor, setUpApp } from './shared/pwa';

setUpApp(doorFor(window.location.pathname, window.location.search));

function parseLocation() {
  return window.location.pathname + window.location.search;
}

function RootApp() {
  useRoute(parseLocation);
  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);

  const isJudge =
    path === '/pitch' ||
    path.startsWith('/pitch/') ||
    path === '/care/pitch' ||
    params.get('judge') === '1' ||
    params.get('pitch') === '1';

  const isEval =
    path === '/eval' ||
    path.startsWith('/eval/') ||
    path === '/care/eval' ||
    path.startsWith('/care/eval/');

  if (isJudge) return <JudgeCommandCenter />;
  if (isEval) return <EvalView />;
  if (path.startsWith('/care')) return <CareApp />;
  if (path.startsWith('/senior')) return <SeniorApp />;
  return <Welcome />;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RootApp />
  </StrictMode>,
);
