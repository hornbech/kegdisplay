<script>
  import { onMount } from 'svelte';
  import KegSvg from '$lib/KegSvg.svelte';
  import { fetchKegs, updateKeg, clearKeg, uploadRecipe, deleteRecipe, recipeUrl } from '$lib/api.js';

  let kegs = [];
  let editing = null;   // keg object being edited
  let saving = false;
  let error = null;
  let successMsg = null;
  let recipeFile = null;       // pending upload (File)
  let recipeBusy = false;

  onMount(async () => {
    kegs = await fetchKegs();
  });

  function startEdit(keg) {
    editing = { ...keg };
    recipeFile = null;
  }

  function cancelEdit() {
    editing = null;
    error = null;
    recipeFile = null;
  }

  async function saveEdit() {
    saving = true; error = null; successMsg = null;
    try {
      let updated = await updateKeg(editing.id, editing);
      if (recipeFile) {
        updated = await uploadRecipe(editing.id, recipeFile);
      }
      kegs = kegs.map(k => k.id === updated.id ? updated : k);
      editing = null;
      recipeFile = null;
      successMsg = 'Keg updated!';
      setTimeout(() => successMsg = null, 3000);
    } catch (e) {
      error = e?.detail?.detail || 'Save failed. Check all fields.';
    } finally {
      saving = false;
    }
  }

  async function handleRemoveRecipe() {
    if (!editing?.recipe_filename) return;
    if (!confirm('Remove attached recipe PDF?')) return;
    recipeBusy = true;
    try {
      const updated = await deleteRecipe(editing.id);
      editing = { ...editing, recipe_filename: null };
      kegs = kegs.map(k => k.id === updated.id ? updated : k);
    } finally {
      recipeBusy = false;
    }
  }

  async function handleClear(keg) {
    if (!confirm(`Clear slot ${keg.slot} (${keg.name || 'empty'})?`)) return;
    const updated = await clearKeg(keg.id);
    kegs = kegs.map(k => k.id === updated.id ? updated : k);
  }

  const statusOptions = ['empty', 'fermenting', 'conditioning', 'on_tap', 'archived'];

  // Beer styles ordered light → dark, colours picked from the SRM scale.
  const beerStyles = [
    { name: 'Pale Lager',           color: '#F3F993' },
    { name: 'Pilsner',              color: '#F5E73C' },
    { name: 'Witbier',              color: '#F3E7AF' },
    { name: 'Berliner Weisse',      color: '#F5E73C' },
    { name: 'Gose',                 color: '#F5E73C' },
    { name: 'Helles',               color: '#F3C04F' },
    { name: 'Blonde Ale',           color: '#F5F75C' },
    { name: 'Kölsch',               color: '#EACA5E' },
    { name: 'Hefeweizen',           color: '#E6CE55' },
    { name: 'Saison',               color: '#E6B825' },
    { name: 'Belgian Tripel',       color: '#E6B825' },
    { name: 'American Pale Ale',    color: '#D5BC26' },
    { name: 'Session IPA',          color: '#D5BC26' },
    { name: 'Hazy IPA / NEIPA',     color: '#E8B55A' },
    { name: 'IPA',                  color: '#BF813A' },
    { name: 'Double IPA',           color: '#BF813A' },
    { name: 'English Bitter / ESB', color: '#BC6733' },
    { name: 'Vienna Lager',         color: '#B26033' },
    { name: 'Märzen / Oktoberfest', color: '#B26033' },
    { name: 'Amber Ale',            color: '#8D4C32' },
    { name: 'Red Ale',              color: '#8D4C32' },
    { name: 'Barleywine',           color: '#8D4C32' },
    { name: 'Bock',                 color: '#7C3F00' },
    { name: 'Belgian Dubbel',       color: '#7C3F00' },
    { name: 'Dunkel',               color: '#5D341A' },
    { name: 'Doppelbock',           color: '#5D341A' },
    { name: 'Brown Ale',            color: '#5D341A' },
    { name: 'Porter',               color: '#3B1F1A' },
    { name: 'Belgian Quadrupel',    color: '#3B1F1A' },
    { name: 'Baltic Porter',        color: '#261716' },
    { name: 'Dry Stout',            color: '#1F1210' },
    { name: 'Milk Stout',           color: '#1F1210' },
    { name: 'Oatmeal Stout',        color: '#1F1210' },
    { name: 'Imperial Stout',       color: '#030403' },
  ];
</script>

<svelte:head><title>Admin — Bear Brew</title></svelte:head>

<main>
  <div class="container">
    <h1>Keg Management</h1>
    {#if successMsg}<p class="success">{successMsg}</p>{/if}

    <div class="keg-list">
      {#each kegs as keg (keg.id)}
        <div class="keg-row">
          <div class="keg-preview">
            <KegSvg color={keg.color_hex} status={keg.status} slot={keg.slot} />
            <span class="slot">Slot #{keg.slot}</span>
          </div>
          <div class="keg-summary">
            <strong>{keg.name || '—'}</strong>
            <span>{keg.style || '—'}</span>
            <span class="status-badge {keg.status}">{keg.status}</span>
          </div>
          <div class="keg-actions">
            <button on:click={() => startEdit(keg)}>Edit</button>
            <button class="danger" on:click={() => handleClear(keg)}>Clear</button>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Edit modal -->
  {#if editing}
    <div class="modal-backdrop" on:click|self={cancelEdit}>
      <div class="modal">
        <h2>Edit Slot #{editing.slot}</h2>
        {#if error}<p class="error">{error}</p>{/if}

        <form on:submit|preventDefault={saveEdit}>
          <div class="form-grid">
            <label>Beer Name <input bind:value={editing.name} /></label>
            <label>Style <input bind:value={editing.style} /></label>
            <label>ABV (%) <input type="number" step="0.1" min="0" max="100" bind:value={editing.abv} /></label>
            <label>Volume (L) <input type="number" step="0.1" min="0" bind:value={editing.volume_liters} /></label>
            <label>IBU <input type="number" step="1" min="0" max="200" bind:value={editing.ibu} placeholder="—" /></label>
            <label>EBC <input type="number" step="1" min="0" max="200" bind:value={editing.ebc} placeholder="—" /></label>
            <label>Brew Date <input type="date" bind:value={editing.brew_date} /></label>
            <label>Tap Date <input type="date" bind:value={editing.tap_date} /></label>
            <label>
              Beer Colour
              <div class="color-row">
                <span class="swatch" style="background:{editing.color_hex || '#444'}"></span>
                <select bind:value={editing.color_hex}>
                  {#each beerStyles as bs}
                    <option value={bs.color}>{bs.name}</option>
                  {/each}
                </select>
              </div>
            </label>
            <label>
              Status
              <select bind:value={editing.status}>
                {#each statusOptions as s}<option value={s}>{s}</option>{/each}
              </select>
            </label>
            <label class="full">Untappd URL (optional)
              <input type="url" bind:value={editing.untappd_url} placeholder="https://untappd.com/b/..." />
            </label>
            <label class="full">Notes
              <textarea rows="3" bind:value={editing.notes}></textarea>
            </label>
            <div class="full recipe-row">
              <span class="recipe-label">Recipe PDF</span>
              {#if editing.recipe_filename && !recipeFile}
                <a href={recipeUrl(editing.id)} target="_blank" rel="noopener" class="recipe-link">
                  📄 {editing.recipe_filename}
                </a>
                <button type="button" class="danger" on:click={handleRemoveRecipe} disabled={recipeBusy}>Remove</button>
              {/if}
              <input type="file" accept="application/pdf" on:change={(e) => recipeFile = e.target.files?.[0] || null} />
              {#if recipeFile}
                <span class="pending">→ will upload <strong>{recipeFile.name}</strong> on save</span>
              {/if}
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" on:click={cancelEdit}>Cancel</button>
            <button type="submit" class="primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</main>

<style>
  main { background: var(--bg); min-height: 100vh; padding-bottom: 4rem; }
  .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
  h1 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }

  .keg-list { display: flex; flex-direction: column; gap: 0.75rem; }
  .keg-row { background: var(--card); border-radius: var(--radius); padding: 1rem 1.5rem; display: flex; align-items: center; gap: 1.5rem; border: 1px solid #333; }
  .keg-preview { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; min-width: 60px; }
  .slot { font-size: 0.7rem; color: var(--text-muted); }
  .keg-summary { flex: 1; display: flex; flex-direction: column; gap: 0.2rem; }
  .keg-summary strong { color: var(--text); }
  .keg-summary span { font-size: 0.8rem; color: var(--text-muted); }
  .status-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; width: fit-content; }
  .status-badge.on_tap { background: #4a9e5c22; color: #4a9e5c; }
  .status-badge.conditioning { background: #C8860A22; color: #C8860A; }
  .status-badge.fermenting { background: #d4652b22; color: #d4652b; }
  .status-badge.empty { background: #44444422; color: #666; }
  .status-badge.archived { background: #33333322; color: #555; }
  .keg-actions { display: flex; gap: 0.5rem; }

  button { background: #333; color: var(--text); border: 1px solid #444; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
  button:hover { border-color: var(--accent); color: var(--accent); }
  button.danger:hover { border-color: #e06060; color: #e06060; }
  button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
  button.primary:hover { background: var(--accent-light); }

  .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
  .modal { background: var(--card); border-radius: var(--radius); padding: 2rem; width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto; border: 1px solid #444; }
  .modal h2 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }

  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .form-grid .full { grid-column: 1 / -1; }
  label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; color: var(--text-muted); }
  input, select, textarea { background: #1a1a1a; border: 1px solid #444; color: var(--text); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.9rem; width: 100%; }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); }
  textarea { resize: vertical; font-family: var(--font-body); }
  .color-row { display: flex; gap: 0.5rem; align-items: center; }
  .swatch { display: inline-block; width: 36px; height: 36px; border-radius: 6px; border: 1px solid #444; flex-shrink: 0; }

  .modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
  .success { color: #4a9e5c; font-size: 0.9rem; margin-bottom: 1rem; }
  .error { color: #e06060; font-size: 0.85rem; margin-bottom: 1rem; }

  .recipe-row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; font-size: 0.85rem; color: var(--text-muted); }
  .recipe-label { width: 100%; }
  .recipe-link { color: var(--accent); text-decoration: none; border-bottom: 1px dotted var(--accent); }
  .recipe-link:hover { color: var(--accent-light); }
  .pending { font-size: 0.8rem; color: var(--accent-light); }
</style>
