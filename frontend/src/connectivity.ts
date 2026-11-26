// Online/offline state for the UI. Fed by the browser's online/offline events
// and by request() in api.ts; it reports connectivity only, never data.

import { useSyncExternalStore } from 'react';

let online = true;
const listeners = new Set<() => void>();

/** Records whether the server was last reachable and notifies subscribers. */
export function setOnline(next: boolean) {
  if (next === online) return;
  online = next;
  listeners.forEach((listener) => listener());
}

window.addEventListener('online', () => setOnline(true));
window.addEventListener('offline', () => setOnline(false));

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** False after the browser or a request reported the server unreachable. */
export function useOnline(): boolean {
  return useSyncExternalStore(subscribe, () => online);
}
