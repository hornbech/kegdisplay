const CLIENT_ID_KEY = 'keg_client_id';
const VISIT_FLAG_KEY = 'keg_visit_counted';
const HEARTBEAT_MS = 20_000;

function randomId() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function getClientId() {
  let id = sessionStorage.getItem(CLIENT_ID_KEY);
  if (!id) {
    id = randomId();
    sessionStorage.setItem(CLIENT_ID_KEY, id);
  }
  return id;
}

export async function fetchStats() {
  const res = await fetch('/api/stats');
  if (!res.ok) throw new Error('stats');
  return res.json();
}

export async function recordVisitOnce() {
  if (sessionStorage.getItem(VISIT_FLAG_KEY) === '1') return null;
  try {
    const res = await fetch('/api/stats/visit', { method: 'POST' });
    if (!res.ok) return null;
    sessionStorage.setItem(VISIT_FLAG_KEY, '1');
    return res.json();
  } catch {
    return null;
  }
}

async function sendHeartbeat() {
  try {
    const res = await fetch('/api/stats/heartbeat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: getClientId() }),
    });
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

// Starts a heartbeat loop. `onTick(stats)` is called after each successful ping.
// Returns a cleanup function.
export function startHeartbeat(onTick) {
  let alive = true;
  const tick = async () => {
    if (!alive) return;
    const stats = await sendHeartbeat();
    if (stats && onTick) onTick(stats);
  };
  tick();
  const id = setInterval(tick, HEARTBEAT_MS);
  return () => { alive = false; clearInterval(id); };
}
