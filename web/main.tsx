import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './shared/tokens.css';
import SeniorApp from './senior/SeniorApp';
import CareApp from './care/CareApp';
import JudgeCommandCenter from './care/JudgeCommandCenter';
import EvalView from './care/EvalView';
import Welcome from './Welcome';
import { doorFor, setUpApp } from './shared/pwa';

const path = window.location.pathname;
const params = new URLSearchParams(window.location.search);
setUpApp(doorFor(path, window.location.search));

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

const App = isJudge
  ? JudgeCommandCenter
  : isEval
    ? EvalView
    : path.startsWith('/care')
      ? CareApp
      : path.startsWith('/senior')
        ? SeniorApp
        : Welcome;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
