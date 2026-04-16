<script>
  import { onMount } from 'svelte';
  import KegSvg from '$lib/KegSvg.svelte';
  import { fetchKegs, updateKeg, clearKeg } from '$lib/api.js';

  let kegs = [];
  let editing = null;   // keg object being edited
  let saving = false;
  let error = null;
  let successMsg = null;

  onMount(async () => {
    kegs = await fetchKegs();
  });

  function startEdit(keg) {
    editing = { ...keg };
  }

  function cancelEdit() {
    editing = null;
    error = null;
  }

  async function saveEdit() {
    saving = true; error = null; successMsg = null;
    try {
      const updated = await updateKeg(editing.id, editing);
      kegs = kegs.map(k => k.id === updated.id ? updated : k);
      editing = null;
      successMsg = 'Keg updated!';
      setTimeout(() => successMsg = null, 3000);
    } catch (e) {
      error = 'Save failed. Check all fields.';
    } finally {
      saving = false;
    }
  }

  async function handleClear(keg) {
    if (!confirm(`Clear slot ${keg.slot} (${keg.name || 'empty'})?`)) return;
    const updated = await clearKeg(keg.id);
    kegs = kegs.map(k => k.id === updated.id ? updated : k);
  }

  const statusOptions = ['empty', 'conditioning', 'on_tap', 'archived'];
</script>

<svelte:head><title>Admin — Jacob's Brewery</title></svelte:head>

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
            <label>Brew Date <input type="date" bind:value={editing.brew_date} /></label>
            <label>Tap Date <input type="date" bind:value={editing.tap_date} /></label>
            <label>
              Beer Colour
              <div class="color-row">
                <input type="color" bind:value={editing.color_hex} />
                <input type="text" bind:value={editing.color_hex} placeholder="#C8860A" style="width:100px" />
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
  input[type="color"] { width: 44px; height: 36px; padding: 2px; cursor: pointer; }

  .modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
  .success { color: #4a9e5c; font-size: 0.9rem; margin-bottom: 1rem; }
  .error { color: #e06060; font-size: 0.85rem; margin-bottom: 1rem; }
</style>
