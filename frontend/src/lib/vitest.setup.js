// Patch localStorage to a proper in-memory implementation
// to override Node.js's --localstorage-file experimental feature
const store = {};
const mockLocalStorage = {
  getItem: (key) => (key in store ? store[key] : null),
  setItem: (key, value) => { store[key] = String(value); },
  removeItem: (key) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  get length() { return Object.keys(store).length; },
  key: (n) => Object.keys(store)[n] ?? null,
};
Object.defineProperty(globalThis, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
  configurable: true,
});
