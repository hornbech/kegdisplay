// frontend/src/lib/api.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { getToken, setToken, clearToken, isLoggedIn } from './api.js';

beforeEach(() => {
  localStorage.clear();
});

describe('token helpers', () => {
  it('returns null when no token set', () => {
    expect(getToken()).toBeNull();
  });

  it('stores and retrieves token', () => {
    setToken('abc123');
    expect(getToken()).toBe('abc123');
  });

  it('clears token', () => {
    setToken('abc123');
    clearToken();
    expect(getToken()).toBeNull();
  });

  it('isLoggedIn true when token exists', () => {
    setToken('abc');
    expect(isLoggedIn()).toBe(true);
  });

  it('isLoggedIn false when no token', () => {
    expect(isLoggedIn()).toBe(false);
  });
});
