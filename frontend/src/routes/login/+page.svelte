<script>
  import { login, setToken } from '$lib/api.js';
  import { goto } from '$app/navigation';

  let username = '', password = '', error = null, loading = false;

  async function handleLogin() {
    error = null;
    loading = true;
    try {
      const data = await login(username, password);
      setToken(data.access_token);
      goto('/admin');
    } catch (e) {
      error = 'Invalid username or password.';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Login — Bear Brew</title></svelte:head>

<div class="page">
  <div class="card">
    <div class="logo">🍺</div>
    <h1>Admin Login</h1>
    <form on:submit|preventDefault={handleLogin}>
      <label>
        Username
        <input type="text" bind:value={username} required autocomplete="username" />
      </label>
      <label>
        Password
        <input type="password" bind:value={password} required autocomplete="current-password" />
      </label>
      {#if error}<p class="error">{error}</p>{/if}
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in…' : 'Login'}
      </button>
    </form>
    <a href="/" class="back">← Back to display</a>
  </div>
</div>

<style>
  .page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); }
  .card { background: var(--card); padding: 2.5rem; border-radius: var(--radius); width: 100%; max-width: 380px; text-align: center; border: 1px solid #333; }
  .logo { font-size: 3rem; margin-bottom: 0.5rem; }
  h1 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }
  form { display: flex; flex-direction: column; gap: 1rem; text-align: left; }
  label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; color: var(--text-muted); }
  input { background: #1a1a1a; border: 1px solid #444; color: var(--text); padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 1rem; }
  input:focus { outline: none; border-color: var(--accent); }
  button { background: var(--accent); color: #fff; border: none; padding: 0.75rem; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 0.5rem; }
  button:hover:not(:disabled) { background: var(--accent-light); }
  button:disabled { opacity: 0.6; cursor: default; }
  .error { color: #e06060; font-size: 0.85rem; }
  .back { display: block; margin-top: 1.5rem; color: var(--text-muted); font-size: 0.8rem; text-decoration: none; }
  .back:hover { color: var(--accent); }
</style>
