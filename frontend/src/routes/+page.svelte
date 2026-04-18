<!-- frontend/src/routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import KegCard from '$lib/KegCard.svelte';
  import { fetchKegs } from '$lib/api.js';
  import { startHeartbeat, recordVisitOnce } from '$lib/presence.js';

  let kegs = [];
  let error = null;
  let loading = true;
  let stopHeartbeat = null;

  onMount(async () => {
    try {
      kegs = await fetchKegs();
    } catch (e) {
      error = 'Could not load kegs. Is the API running?';
    } finally {
      loading = false;
    }
    recordVisitOnce();
    stopHeartbeat = startHeartbeat();
  });

  onDestroy(() => { if (stopHeartbeat) stopHeartbeat(); });
</script>

<svelte:head><title>Bear Brew</title></svelte:head>

<main>
  <header>
    <div class="header-inner">
      <div class="logo">🍻</div>
      <div>
        <h1>Bear Brew</h1>
        <p class="tagline">What's on tap</p>
      </div>
      <a href="/info" class="admin-link">Info</a>
      <a href="/admin" class="admin-link">Admin</a>
    </div>
    <div class="wood-strip"></div>
  </header>

  {#if loading}
    <div class="state-msg">Loading kegs…</div>
  {:else if error}
    <div class="state-msg error">{error}</div>
  {:else}
    <div class="grid">
      {#each kegs as keg (keg.id)}
        <KegCard {keg} />
      {/each}
    </div>
  {/if}
</main>

<style>
  main { min-height: 100vh; background: var(--bg); }

  header { background: #111; border-bottom: 3px solid var(--accent); }
  .header-inner {
    max-width: 1200px; margin: 0 auto; padding: 1.2rem 2rem;
    display: flex; align-items: center; gap: 1rem;
  }
  .logo { font-size: 2.5rem; }
  h1 { font-family: var(--font-heading); font-size: 2rem; color: var(--accent-light); }
  .tagline { color: var(--text-muted); font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; }
  .admin-link {
    margin-left: auto; color: var(--text-muted); font-size: 0.8rem;
    text-decoration: none; border: 1px solid #444; padding: 4px 12px; border-radius: 6px;
  }
  .admin-link:hover { color: var(--accent); border-color: var(--accent); }

  .wood-strip {
    height: 8px;
    background: repeating-linear-gradient(90deg, #5c3d1e 0px, #7a5230 40px, #5c3d1e 80px);
    opacity: 0.6;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
  }

  @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 500px) { .grid { grid-template-columns: 1fr; } }

  .state-msg { text-align: center; padding: 4rem; color: var(--text-muted); }
  .state-msg.error { color: #e06060; }
</style>
