<script>
  import KegSvg from './KegSvg.svelte';
  export let keg;

  const statusLabel = { empty: 'Empty', conditioning: 'Conditioning', on_tap: 'On Tap', archived: 'Archived' };
  const statusColor = { empty: '#555', conditioning: '#C8860A', on_tap: '#4a9e5c', archived: '#666' };

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
      {#if keg.untappd_url}
        <a href={keg.untappd_url} target="_blank" rel="noopener" aria-label="View on Untappd" class="untappd-link">
          🍺 Untappd
        </a>
      {/if}
    </div>
  {/if}
</div>

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

  .untappd-link {
    display: inline-block; margin-top: 0.4rem;
    font-size: 0.75rem; color: var(--accent);
    text-decoration: none; border-bottom: 1px dotted var(--accent);
  }
</style>
