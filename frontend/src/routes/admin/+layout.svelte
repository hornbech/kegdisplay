<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isLoggedIn, clearToken } from '$lib/api.js';

  onMount(() => {
    if (!isLoggedIn()) goto('/login');
  });

  function logout() {
    clearToken();
    goto('/login');
  }
</script>

<nav>
  <a href="/">🍻 Display</a>
  <span>Admin</span>
  <button on:click={logout}>Logout</button>
</nav>

<slot />

<style>
  nav { background: #111; border-bottom: 2px solid var(--accent); padding: 0.8rem 2rem; display: flex; align-items: center; gap: 1.5rem; }
  nav a { color: var(--text-muted); text-decoration: none; font-size: 0.9rem; }
  nav a:hover { color: var(--accent); }
  nav span { color: var(--accent-light); font-weight: 500; }
  nav button { margin-left: auto; background: transparent; border: 1px solid #444; color: var(--text-muted); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  nav button:hover { border-color: var(--accent); color: var(--accent); }
</style>
