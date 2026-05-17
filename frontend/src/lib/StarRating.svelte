<script>
  import { createEventDispatcher } from 'svelte';

  export let value = 0;
  export let interactive = false;

  const dispatch = createEventDispatcher();
  let hovered = 0;

  function pick(n) {
    if (!interactive) return;
    dispatch('change', n);
  }
</script>

<span class="stars" class:interactive>
  {#each [1, 2, 3, 4, 5] as n}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <span
      class="star"
      class:filled={n <= (interactive ? (hovered || value) : value)}
      on:mouseenter={() => { if (interactive) hovered = n; }}
      on:mouseleave={() => { if (interactive) hovered = 0; }}
      on:click={() => pick(n)}
      role={interactive ? 'button' : undefined}
      tabindex={interactive ? 0 : undefined}
      on:keydown={(e) => e.key === 'Enter' && pick(n)}
      aria-label={interactive ? `Rate ${n} star${n > 1 ? 's' : ''}` : undefined}
    >★</span>
  {/each}
</span>

<style>
  .stars { display: inline-flex; gap: 2px; line-height: 1; }
  .star { color: #3a2f20; font-size: 1em; }
  .star.filled { color: #c8860a; }
  .interactive .star { cursor: pointer; transition: color 0.1s; }
  .interactive .star:focus { outline: 1px solid #c8860a; border-radius: 2px; }
</style>
