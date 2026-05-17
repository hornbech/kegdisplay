<script>
  import KegSvg from './KegSvg.svelte';
  import StarRating from './StarRating.svelte';
  import { recipeUrl, fetchReviews, submitReview } from './api.js';
  export let keg;

  const FULL_KEG_LITERS = 19;

  function daysSince(iso) {
    if (!iso) return null;
    return Math.floor((new Date() - new Date(iso)) / 86400000);
  }
  function humanAge(days) {
    if (days == null) return '—';
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 14) return `${days} days`;
    if (days < 60) return `${Math.round(days / 7)} weeks`;
    return `${Math.round(days / 30)} months`;
  }
  function fillLevelFor(k) {
    if (k.status === 'empty') return 0;
    if (k.status === 'archived') return 0.08;
    if (k.status === 'conditioning') return 0.95;
    if (k.status === 'fermenting') return 0.92;
    return Math.min(1, Math.max(0, (k.volume_liters ?? FULL_KEG_LITERS) / FULL_KEG_LITERS));
  }

  $: isEmpty = keg.status === 'empty';
  $: isOnTap = keg.status === 'on_tap';
  $: isArchived = keg.status === 'archived';
  $: fill = fillLevelFor(keg);

  $: primaryAge = (keg.status === 'conditioning' || keg.status === 'fermenting')
    ? humanAge(daysSince(keg.brew_date))
    : humanAge(daysSince(keg.tap_date));
  $: ageLabel = {
    on_tap: 'On tap',
    conditioning: 'Conditioning',
    fermenting: 'Fermenting',
    archived: 'Kicked',
  }[keg.status] ?? '';

  let showRecipe = false;
  let showReviews = false;
  let reviews = [];
  let reviewsLoaded = false;
  let reviewForm = { name: '', stars: 0, comment: '' };
  let reviewSubmitting = false;
  let reviewError = null;
  let reviewSuccess = false;
  let showAllReviews = false;

  async function toggleReviews() {
    showReviews = !showReviews;
    if (showReviews && !reviewsLoaded) {
      reviews = await fetchReviews(keg.id);
      reviewsLoaded = true;
    }
  }

  async function handleSubmitReview() {
    if (!reviewForm.name.trim() || reviewForm.stars === 0) {
      reviewError = 'Name and a star rating are required.';
      return;
    }
    reviewSubmitting = true;
    reviewError = null;
    try {
      const created = await submitReview(keg.id, {
        name: reviewForm.name.trim(),
        stars: reviewForm.stars,
        comment: reviewForm.comment.trim() || null,
      });
      reviews = [created, ...reviews];
      reviewForm = { name: '', stars: 0, comment: '' };
      reviewSuccess = true;
      setTimeout(() => reviewSuccess = false, 3000);
    } catch (e) {
      reviewError = 'Could not submit review. Please try again.';
    } finally {
      reviewSubmitting = false;
    }
  }

  function relativeDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const diff = Math.floor((Date.now() - d) / 86400000);
    if (diff === 0) return 'Today';
    if (diff === 1) return 'Yesterday';
    if (diff < 30) return `${diff}d ago`;
    return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
  }

  $: displayedReviews = showAllReviews ? reviews : reviews.slice(0, 5);
  $: avgStars = keg.avg_stars;
  $: reviewCount = keg.review_count ?? 0;
</script>

<div class="card" class:empty={isEmpty} class:archived={isArchived}>
  <div class="slot-tag" class:active={isOnTap}>TAP {String(keg.slot).padStart(2, '0')}</div>

  <div class="keg-viz">
    <KegSvg color={keg.color_hex} status={keg.status} slot={keg.slot} size={110} {fill} />
  </div>

  <div class="info">
    {#if isEmpty}
      <div class="empty-slot">Pouring next…</div>
    {:else}
      <div class="style-caption">{keg.style}</div>
      <h2 class="beer-name">{keg.name}</h2>

      <div class="stats">
        <div class="stat">
          <div class="stat-value accent">{keg.abv != null ? keg.abv.toFixed(1) : '—'}<span class="unit">%</span></div>
          <div class="stat-label">ABV</div>
        </div>
        <div class="divider" />
        <div class="stat">
          <div class="stat-value">{primaryAge}</div>
          <div class="stat-label">{ageLabel}</div>
        </div>
        <div class="divider" />
        <div class="fill-col">
          <div class="fill-bar">
            <div class="fill-fill" style="width:{Math.round(fill * 100)}%; background:linear-gradient(90deg, {keg.color_hex}, {keg.color_hex}dd);" />
          </div>
          <div class="fill-meta">
            <span>Fill</span>
            <span class="fill-pct">{Math.round(fill * 100)}%</span>
          </div>
        </div>
      </div>

      {#if keg.ibu != null || keg.ebc != null || keg.untappd_url || keg.recipe_filename}
        <div class="meta-row">
          {#if keg.ibu != null}<span class="meta-item">{keg.ibu} IBU</span>{/if}
          {#if keg.ebc != null}<span class="meta-item">{keg.ebc} EBC</span>{/if}
          {#if keg.untappd_url}
            <a class="meta-link" href={keg.untappd_url} target="_blank" rel="noopener">↗ Untappd</a>
          {/if}
          {#if keg.recipe_filename}
            <button type="button" class="meta-link" on:click={() => showRecipe = true}>Recipe</button>
          {/if}
        </div>
      {/if}

      {#if keg.notes}
        <p class="notes">"{keg.notes}"</p>
      {/if}

      <!-- Review strip -->
      <div class="review-strip">
        <button type="button" class="review-toggle" on:click={toggleReviews}>
          <StarRating value={avgStars ?? 0} />
          {#if reviewCount > 0}
            <span class="review-meta">{avgStars} ★ ({reviewCount} {reviewCount === 1 ? 'review' : 'reviews'})</span>
          {:else}
            <span class="review-meta no-reviews">No reviews yet</span>
          {/if}
          <span class="chevron">{showReviews ? '▲' : '▼'}</span>
        </button>

        {#if showReviews}
          <div class="review-panel">
            {#each displayedReviews as rev (rev.id)}
              <div class="review-item">
                <div class="review-header">
                  <strong>{rev.name}</strong>
                  <StarRating value={rev.stars} />
                  <span class="review-date">{relativeDate(rev.created_at)}</span>
                </div>
                {#if rev.comment}<p class="review-comment">"{rev.comment}"</p>{/if}
              </div>
            {/each}
            {#if reviews.length > 5 && !showAllReviews}
              <button type="button" class="show-all" on:click={() => showAllReviews = true}>
                Show all {reviews.length} reviews
              </button>
            {/if}

            <div class="review-form">
              <div class="form-row">
                <input
                  class="form-input"
                  placeholder="Your name"
                  bind:value={reviewForm.name}
                  maxlength="80"
                />
                <StarRating value={reviewForm.stars} interactive on:change={(e) => reviewForm.stars = e.detail} />
              </div>
              <textarea
                class="form-textarea"
                placeholder="Tasting notes (optional)"
                bind:value={reviewForm.comment}
                maxlength="500"
                rows="2"
              ></textarea>
              {#if reviewError}<p class="form-error">{reviewError}</p>{/if}
              {#if reviewSuccess}<p class="form-success">Review posted!</p>{/if}
              <button
                type="button"
                class="submit-btn"
                on:click={handleSubmitReview}
                disabled={reviewSubmitting}
              >
                {reviewSubmitting ? 'Posting…' : 'Post review'}
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<svelte:window on:keydown={(e) => { if (e.key === 'Escape' && showRecipe) showRecipe = false; }} />

{#if showRecipe && keg.recipe_filename}
  <div class="pdf-backdrop" on:click|self={() => showRecipe = false} role="dialog" aria-modal="true" aria-label="Recipe PDF">
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
    position: relative;
    background: linear-gradient(180deg, rgba(40,30,22,0.9), rgba(20,14,10,0.95));
    border: 1px solid rgba(200,134,10,0.18);
    border-radius: 4px;
    padding: 22px 22px 20px;
    display: flex;
    gap: 20px;
    min-height: 220px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 4px 20px rgba(0,0,0,0.4);
  }
  .card.empty {
    background: rgba(255,255,255,0.015);
    border: 1.5px dashed rgba(154,134,104,0.3);
    box-shadow: none;
  }
  .card.archived { opacity: 0.45; }

  .slot-tag {
    position: absolute;
    top: -1px;
    left: 20px;
    background: #3a3024;
    color: #9a8668;
    padding: 6px 14px 5px;
    font-size: 11px;
    letter-spacing: 0.2em;
    font-weight: 700;
    font-family: 'Playfair Display', serif;
  }
  .slot-tag.active { background: #c8860a; color: #0f0907; }

  .keg-viz { flex-shrink: 0; display: flex; align-items: center; }

  .info { flex: 1; display: flex; flex-direction: column; padding-top: 14px; min-width: 0; }

  .empty-slot {
    margin: auto 0;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 28px;
    color: #5a4a33;
  }

  .style-caption {
    font-size: 11px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #9a8668;
    margin-bottom: 4px;
  }

  .beer-name {
    font-family: 'Playfair Display', serif;
    font-size: 34px;
    font-weight: 900;
    line-height: 1.05;
    color: #f4e7c9;
    letter-spacing: -0.5px;
    margin-bottom: 14px;
    overflow-wrap: break-word;
  }

  .stats { display: flex; gap: 24px; margin-bottom: 10px; align-items: stretch; }
  .stat-value {
    font-family: 'Playfair Display', serif;
    font-size: 30px;
    font-weight: 900;
    line-height: 1;
    color: #f4e7c9;
  }
  .stat-value.accent { color: #c8860a; }
  .stat-value .unit { font-size: 16px; margin-left: 2px; font-weight: 700; }
  .stat-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6a5a44;
    margin-top: 2px;
  }
  .divider { width: 1px; background: rgba(200,134,10,0.2); }
  .fill-col { flex: 1; display: flex; flex-direction: column; justify-content: center; min-width: 60px; }
  .fill-bar { height: 6px; background: rgba(200,134,10,0.12); border-radius: 3px; overflow: hidden; }
  .fill-fill { height: 100%; transition: width 0.5s ease; }
  .fill-meta {
    display: flex; justify-content: space-between;
    font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
    color: #6a5a44; margin-top: 6px;
  }
  .fill-pct { color: #9a8668; }

  .meta-row {
    display: flex; flex-wrap: wrap; gap: 10px 14px;
    margin-top: 4px; margin-bottom: 8px;
    font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
    color: #6a5a44; font-weight: 600;
  }
  .meta-item { color: #9a8668; }
  .meta-link {
    background: none; border: none; padding: 0; cursor: pointer;
    color: #c8860a; font: inherit; letter-spacing: 0.2em; text-transform: uppercase;
    text-decoration: none; border-bottom: 1px dotted rgba(200,134,10,0.4);
  }
  .meta-link:hover { color: #e8a020; border-color: #e8a020; }

  .notes {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 13px;
    color: #9a8668;
    line-height: 1.45;
    margin-top: auto;
    border-top: 1px solid rgba(200,134,10,0.15);
    padding-top: 10px;
  }

  @media (max-width: 700px) {
    .card { gap: 14px; padding: 20px 18px 18px; }
    .beer-name { font-size: 26px; }
    .stat-value { font-size: 24px; }
    .stats { gap: 16px; }
  }

  .pdf-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.85);
    display: flex; align-items: center; justify-content: center;
    z-index: 200; padding: 1rem;
  }
  .pdf-modal {
    background: #1a1613; border-radius: 4px; border: 1px solid rgba(200,134,10,0.25);
    width: 100%; max-width: 900px; height: 90vh;
    display: flex; flex-direction: column; overflow: hidden;
  }
  .pdf-header {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.75rem 1rem; border-bottom: 1px solid rgba(200,134,10,0.15);
    font-size: 0.85rem; color: #f4e7c9;
  }
  .pdf-header strong { color: #e8a020; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pdf-open { color: #c8860a; text-decoration: none; font-size: 0.8rem; }
  .pdf-open:hover { color: #e8a020; }
  .pdf-close {
    background: transparent; border: 1px solid #4a3d2e; color: #9a8668;
    width: 28px; height: 28px; border-radius: 4px; cursor: pointer;
  }
  .pdf-close:hover { border-color: #c8860a; color: #c8860a; }
  .pdf-frame { flex: 1; border: none; background: #fff; }

  .review-strip { margin-top: 10px; border-top: 1px solid rgba(200,134,10,0.15); padding-top: 8px; }

  .review-toggle {
    display: flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: #9a8668; font-size: 12px; padding: 0; width: 100%; text-align: left;
  }
  .review-toggle:hover { color: #e8a020; }
  .review-meta { font-size: 11px; color: #7a6a54; }
  .review-meta.no-reviews { font-style: italic; }
  .chevron { margin-left: auto; font-size: 9px; color: #5a4a33; }

  .review-panel { margin-top: 8px; display: flex; flex-direction: column; gap: 8px; }

  .review-item { padding: 6px 0; border-bottom: 1px solid rgba(200,134,10,0.08); }
  .review-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .review-header strong { font-size: 12px; color: #c8b080; }
  .review-date { font-size: 10px; color: #5a4a33; margin-left: auto; }
  .review-comment { margin: 4px 0 0; font-size: 11px; color: #9a8668; font-style: italic; }

  .show-all {
    background: none; border: none; cursor: pointer;
    font-size: 11px; color: #7a6a54; text-decoration: underline; padding: 0;
  }

  .review-form { margin-top: 6px; display: flex; flex-direction: column; gap: 6px; }
  .form-row { display: flex; align-items: center; gap: 8px; }
  .form-input {
    flex: 1; background: rgba(255,255,255,0.04); border: 1px solid rgba(200,134,10,0.2);
    color: #f0e3c8; padding: 5px 8px; border-radius: 3px; font-size: 12px;
  }
  .form-input::placeholder { color: #5a4a33; }
  .form-textarea {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(200,134,10,0.2);
    color: #f0e3c8; padding: 5px 8px; border-radius: 3px; font-size: 12px;
    resize: vertical; font-family: inherit;
  }
  .form-textarea::placeholder { color: #5a4a33; }
  .form-error { font-size: 11px; color: #e06060; margin: 0; }
  .form-success { font-size: 11px; color: #6abf6a; margin: 0; }
  .submit-btn {
    align-self: flex-start;
    background: rgba(200,134,10,0.15); border: 1px solid rgba(200,134,10,0.35);
    color: #e8a020; padding: 5px 14px; border-radius: 3px; font-size: 12px;
    cursor: pointer; transition: background 0.15s;
  }
  .submit-btn:hover:not(:disabled) { background: rgba(200,134,10,0.28); }
  .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
