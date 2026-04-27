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
  let refreshInterval = null;

  onMount(async () => {
    try {
      kegs = await fetchKegs();
      await recordVisitOnce();
      stopHeartbeat = startHeartbeat();
      refreshInterval = setInterval(async () => {
        try { kegs = await fetchKegs(); } catch {}
      }, 60_000);
    } catch (e) {
      error = 'Could not load kegs. Is the API running?';
    } finally {
      loading = false;
    }
  });

  onDestroy(() => {
    if (stopHeartbeat) stopHeartbeat();
    if (refreshInterval) clearInterval(refreshInterval);
  });

  $: onTapCount = kegs.filter(k => k.status === 'on_tap').length;
  $: totalSlots = kegs.length || 10;
</script>

<svelte:head><title>Bear Brew</title></svelte:head>

<main class="tavern">
  <div class="chalk-texture" aria-hidden="true"></div>

  <nav class="corner-links">
    <a href="/info">Info</a>
    <a href="/admin">Admin</a>
  </nav>

  <header class="tavern-header">
    <div class="wordmark">
      <h1 class="brand">Bear Brew<span class="brand-dot">.</span></h1>
      <div class="tagline">
        <span>Est. 2016</span>
        <span class="bullet"></span>
        <span>Aalborg</span>
        <span class="bullet"></span>
        <span>Ten taps. No shortcuts.</span>
      </div>
    </div>

    <div class="counter">
      <div class="counter-caption">currently pouring</div>
      <div class="counter-value">
        {onTapCount}<span class="slash">/</span><span class="total">{totalSlots}</span>
      </div>
    </div>
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
  .tavern {
    min-height: 100vh;
    background: radial-gradient(ellipse at 30% 20%, #1f1815 0%, #0e0907 70%);
    color: #f0e3c8;
    font-family: 'Inter', system-ui, sans-serif;
    position: relative;
    overflow-x: hidden;
  }
  .chalk-texture {
    position: absolute; inset: 0;
    background:
      repeating-linear-gradient(90deg, rgba(255,255,255,0.015) 0px, transparent 2px, transparent 7px),
      radial-gradient(circle at 80% 60%, rgba(200,134,10,0.06), transparent 50%);
    pointer-events: none;
  }

  .corner-links {
    position: absolute; top: 16px; right: 16px;
    display: flex; gap: 8px; z-index: 10;
  }
  .corner-links a {
    color: #6a5a44;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    text-decoration: none;
    border: 1px solid rgba(200,134,10,0.18);
    padding: 5px 10px;
    border-radius: 3px;
    transition: color 0.15s, border-color 0.15s;
  }
  .corner-links a:hover { color: #e8a020; border-color: rgba(200,134,10,0.5); }

  .tavern-header {
    position: relative;
    padding: 40px 64px 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 32px;
    border-bottom: 1px solid rgba(200,134,10,0.25);
  }

  .brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 68px;
    font-weight: 900;
    font-style: italic;
    letter-spacing: -1.5px;
    line-height: 0.95;
    color: #f4e7c9;
  }
  .brand-dot { color: #c8860a; }

  .tagline {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 14px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #9a8668;
    font-weight: 500;
  }
  .bullet { width: 4px; height: 4px; background: #c8860a; border-radius: 50%; }

  .counter { text-align: right; flex-shrink: 0; }
  .counter-caption {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 16px;
    color: #9a8668;
    margin-bottom: 4px;
  }
  .counter-value {
    font-family: 'Playfair Display', serif;
    font-size: 56px;
    font-weight: 900;
    color: #e8a020;
    line-height: 1;
  }
  .counter-value .slash { color: #5a4a33; margin: 0 8px; }
  .counter-value .total { color: #9a8668; font-size: 40px; }

  .grid {
    position: relative;
    padding: 32px 64px 40px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }

  .state-msg {
    position: relative;
    text-align: center;
    padding: 6rem 2rem;
    color: #9a8668;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 20px;
  }
  .state-msg.error { color: #e06060; }

  @media (max-width: 900px) {
    .tavern-header { flex-direction: column; align-items: flex-start; padding: 32px 28px 24px; }
    .brand { font-size: 48px; letter-spacing: -1px; }
    .counter { text-align: left; }
    .counter-value { font-size: 44px; }
    .grid { grid-template-columns: 1fr; padding: 24px 20px 32px; }
  }

  @media (max-width: 500px) {
    .brand { font-size: 40px; }
    .tagline { font-size: 11px; gap: 10px; }
    .counter-value { font-size: 36px; }
    .counter-value .total { font-size: 26px; }
  }
</style>
