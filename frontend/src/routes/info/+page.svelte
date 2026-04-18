<script>
  import { onMount, onDestroy } from 'svelte';
  import { startHeartbeat, fetchStats, recordVisitOnce } from '$lib/presence.js';

  let stats = { visits: 0, online: 0 };
  let stopHeartbeat = null;
  let pollId = null;

  async function refresh() {
    try { stats = await fetchStats(); } catch {}
  }

  onMount(async () => {
    await recordVisitOnce();
    refresh();
    stopHeartbeat = startHeartbeat((s) => stats = s);
    pollId = setInterval(refresh, 5_000);
  });

  onDestroy(() => {
    if (stopHeartbeat) stopHeartbeat();
    if (pollId) clearInterval(pollId);
  });
</script>

<svelte:head><title>Info — Bear Brew</title></svelte:head>

<main>
  <header>
    <div class="header-inner">
      <div class="logo">🍻</div>
      <div>
        <h1>Bear Brew</h1>
        <p class="tagline">About this display</p>
      </div>
      <a href="/" class="back-link">← Display</a>
    </div>
    <div class="wood-strip"></div>
  </header>

  <div class="container">
    <section>
      <h2>Links</h2>
      <ul class="links">
        <li><a href="/api/docs" target="_blank" rel="noopener">📖 API documentation (Swagger)</a></li>
        <li><a href="https://github.com/hornbech/kegdisplay" target="_blank" rel="noopener">💻 GitHub project</a></li>
      </ul>
    </section>

    <section>
      <h2>Stats</h2>
      <div class="stats">
        <div class="stat">
          <span class="stat-value">{stats.visits.toLocaleString()}</span>
          <span class="stat-label">👀 Total visits</span>
        </div>
        <div class="stat">
          <span class="stat-value">
            <span class="dot"></span>{stats.online}
          </span>
          <span class="stat-label">Online now</span>
        </div>
      </div>
      <p class="note">A visit is counted once per browser session. "Online now" reflects anyone who pinged the server in the last minute.</p>
    </section>
  </div>
</main>

<style>
  main { min-height: 100vh; background: var(--bg); }

  header { background: #111; border-bottom: 3px solid var(--accent); }
  .header-inner { max-width: 900px; margin: 0 auto; padding: 1.2rem 2rem; display: flex; align-items: center; gap: 1rem; }
  .logo { font-size: 2.5rem; }
  h1 { font-family: var(--font-heading); font-size: 2rem; color: var(--accent-light); }
  .tagline { color: var(--text-muted); font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; }
  .back-link { margin-left: auto; color: var(--text-muted); font-size: 0.8rem; text-decoration: none; border: 1px solid #444; padding: 4px 12px; border-radius: 6px; }
  .back-link:hover { color: var(--accent); border-color: var(--accent); }

  .wood-strip { height: 8px; background: repeating-linear-gradient(90deg, #5c3d1e 0px, #7a5230 40px, #5c3d1e 80px); opacity: 0.6; }

  .container { max-width: 900px; margin: 2rem auto; padding: 0 2rem; display: flex; flex-direction: column; gap: 2.5rem; }
  section h2 { font-family: var(--font-heading); color: var(--accent-light); font-size: 1.3rem; margin-bottom: 1rem; }

  .links { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 0.75rem; }
  .links a { color: var(--accent); text-decoration: none; border-bottom: 1px dotted var(--accent); padding-bottom: 2px; font-size: 1rem; }
  .links a:hover { color: var(--accent-light); border-color: var(--accent-light); }

  .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
  .stat { background: var(--card); border: 1px solid #333; border-radius: var(--radius); padding: 1.5rem; text-align: center; display: flex; flex-direction: column; gap: 0.4rem; }
  .stat-value { font-family: var(--font-heading); font-size: 2.2rem; color: var(--accent-light); display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; }
  .stat-label { color: var(--text-muted); font-size: 0.85rem; }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: #4a9e5c; box-shadow: 0 0 6px #4a9e5c; animation: pulse 1.6s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.4 } }

  .note { color: var(--text-muted); font-size: 0.8rem; margin-top: 1rem; font-style: italic; }

  @media (max-width: 500px) { .stats { grid-template-columns: 1fr; } }
</style>
