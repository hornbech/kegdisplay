<script>
  import KegSvg from './KegSvg.svelte';
  import { recipeUrl } from './api.js';
  export let keg;

  const statusLabel = { empty: 'Empty', conditioning: 'Conditioning', on_tap: 'On Tap', archived: 'Archived' };
  const statusColor = { empty: '#555', conditioning: '#C8860A', on_tap: '#4a9e5c', archived: '#666' };

  let showRecipe = false;

  function formatDate(d) {
    if (!d) return null;
    return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }
</script>

<div class="card" class:empty={keg.status === 'empty'} class:archived={keg.status === 'archived'}>
  <div class="slot-badge">#{keg.slot}</div>

  <div class="keg-visual">
    <KegSvg color={keg.color_hex} status={keg.status} slot={keg.slot} />
  </div>

  {#if keg.status === 'empty'}
    <p class="empty-label">Empty</p>
  {:else}
    <div class="info">
      <h3 class="beer-name">{keg.name}</h3>
      <p class="beer-style">{keg.style}</p>
      <div class="badges">
        <span class="badge abv">{keg.abv != null ? keg.abv.toFixed(1) : '—'}% ABV</span>
        {#if keg.ibu != null}<span class="badge meta">{keg.ibu} IBU</span>{/if}
        {#if keg.ebc != null}<span class="badge meta">{keg.ebc} EBC</span>{/if}
        <span class="badge status" style="background:{statusColor[keg.status]}">
          {statusLabel[keg.status]}
        </span>
      </div>
      {#if keg.brew_date}
        <p class="date">Brewed {formatDate(keg.brew_date)}</p>
      {/if}
      {#if keg.tap_date}
        <p class="date">Tapped {formatDate(keg.tap_date)}</p>
      {/if}
      {#if keg.notes}
        <p class="notes">{keg.notes}</p>
      {/if}
      <div class="links">
        {#if keg.untappd_url}
          <a href={keg.untappd_url} target="_blank" rel="noopener" class="link-btn">🍺 Untappd</a>
        {/if}
        {#if keg.recipe_filename}
          <button type="button" class="link-btn" on:click={() => showRecipe = true}>📄 Recipe</button>
        {/if}
      </div>
    </div>
  {/if}
</div>

{#if showRecipe && keg.recipe_filename}
  <div class="pdf-backdrop" on:click|self={() => showRecipe = false} role="dialog">
    <div class="pdf-modal">
      <div class="pdf-header">
        <strong>{keg.name} — {keg.recipe_filename}</strong>
        <a href={recipeUrl(keg.id)} target="_blank" rel="noopener" class="pdf-open">Open in new tab ↗</a>
        <button type="button" class="pdf-close" on:click={() => showRecipe = false} aria-label="Close">✕</button>
      </div>
      <iframe src={recipeUrl(keg.id)} title="Recipe PDF" class="pdf-frame"></iframe>
    </div>
  </div>
{/if}

<style>
  .card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    border: 1px solid #333;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    min-height: 280px;
  }
  .card:not(.empty):hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
  .card.empty { opacity: 0.5; border-style: dashed; }
  .card.archived { opacity: 0.6; }

  .slot-badge {
    position: absolute; top: 8px; left: 8px;
    background: #333; color: var(--text-muted);
    font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;
  }

  .keg-visual { margin: 0.5rem 0; }

  .empty-label { color: var(--text-muted); font-size: 0.9rem; }

  .info { width: 100%; text-align: center; }
  .beer-name { font-family: var(--font-heading); font-size: 1.1rem; color: var(--accent-light); }
  .beer-style { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }

  .badges { display: flex; gap: 0.4rem; justify-content: center; flex-wrap: wrap; margin-bottom: 0.4rem; }
  .badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
  .badge.abv { background: #333; color: var(--accent-light); }
  .badge.meta { background: #2a2a2a; color: var(--text-muted); }
  .badge.status { color: #fff; }

  .date { font-size: 0.75rem; color: var(--text-muted); }
  .notes {
    font-size: 0.75rem; color: var(--text-muted); font-style: italic;
    margin-top: 0.25rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .links { display: flex; gap: 0.6rem; justify-content: center; margin-top: 0.4rem; flex-wrap: wrap; }
  .link-btn {
    font-size: 0.75rem; color: var(--accent);
    text-decoration: none; border: none; background: none; padding: 0;
    border-bottom: 1px dotted var(--accent); cursor: pointer;
  }
  .link-btn:hover { color: var(--accent-light); border-color: var(--accent-light); }

  .pdf-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.85);
    display: flex; align-items: center; justify-content: center;
    z-index: 200; padding: 1rem;
  }
  .pdf-modal {
    background: var(--card); border-radius: var(--radius); border: 1px solid #444;
    width: 100%; max-width: 900px; height: 90vh;
    display: flex; flex-direction: column; overflow: hidden;
  }
  .pdf-header {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.75rem 1rem; border-bottom: 1px solid #333;
    font-size: 0.85rem;
  }
  .pdf-header strong { color: var(--accent-light); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pdf-open { color: var(--accent); text-decoration: none; font-size: 0.8rem; }
  .pdf-open:hover { color: var(--accent-light); }
  .pdf-close {
    background: transparent; border: 1px solid #444; color: var(--text-muted);
    width: 28px; height: 28px; border-radius: 4px; cursor: pointer;
  }
  .pdf-close:hover { border-color: var(--accent); color: var(--accent); }
  .pdf-frame { flex: 1; border: none; background: #fff; }
</style>
