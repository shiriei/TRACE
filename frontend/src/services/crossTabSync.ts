/**
 * TRACE Cross-Tab Synchronization Service
 *
 * Coordinates cross-tab state updates via the browser BroadcastChannel API
 * so that exploration streak indicators, streak summaries, and Sticker Garden collections
 * stay in sync across open tabs when a trace is saved in any tab.
 */

export const TRACE_BROADCAST_CHANNEL = 'trace_events';

export interface TraceBroadcastMessage {
  type: 'trace_saved';
  eventId: string;
  timestamp: number;
}

let activeChannel: BroadcastChannel | null = null;
let listenerCount = 0;
const seenEventIds = new Set<string>();
const MAX_SEEN_EVENT_IDS = 100;

function rememberEventId(eventId: string): void {
  seenEventIds.add(eventId);
  if (seenEventIds.size > MAX_SEEN_EVENT_IDS) {
    const oldest = seenEventIds.values().next().value;
    if (oldest) {
      seenEventIds.delete(oldest);
    }
  }
}

/**
 * Returns or initializes the shared BroadcastChannel instance for this browsing context.
 */
function getOrCreateChannel(): BroadcastChannel | null {
  if (typeof window === 'undefined' || !('BroadcastChannel' in window)) {
    return null;
  }

  if (!activeChannel) {
    try {
      activeChannel = new BroadcastChannel(TRACE_BROADCAST_CHANNEL);
      activeChannel.onmessage = (event: MessageEvent<TraceBroadcastMessage>) => {
        // Validate incoming message structure
        if (event?.data && event.data.type === 'trace_saved') {
          const { eventId, timestamp } = event.data;

          // Deduplicate true duplicates based on unique eventId (safe for same-millisecond saves)
          if (eventId && seenEventIds.has(eventId)) {
            return;
          }
          if (eventId) {
            rememberEventId(eventId);
          }

          // Dispatch local custom event in this tab for same-tab consumers
          window.dispatchEvent(
            new CustomEvent('trace:saved', {
              detail: { source: 'cross-tab', timestamp, eventId },
            })
          );
        }
      };
    } catch (err) {
      console.warn('[crossTabSync] Failed to initialize BroadcastChannel:', err);
      activeChannel = null;
    }
  }

  return activeChannel;
}

/**
 * Initializes cross-tab synchronization listener for this tab.
 * Supports reference counting so multiple mounting components can safely register.
 * Returns an unmount cleanup function.
 */
export function initCrossTabSync(): () => void {
  const channel = getOrCreateChannel();
  if (channel) {
    listenerCount += 1;
  }

  return () => {
    if (channel) {
      listenerCount = Math.max(0, listenerCount - 1);
      if (listenerCount === 0 && activeChannel) {
        try {
          activeChannel.onmessage = null;
          activeChannel.close();
        } catch (err) {
          console.warn('[crossTabSync] Error closing channel:', err);
        }
        activeChannel = null;
      }
    }
  };
}

/**
 * Broadcasts a trace save notification.
 * 1. Dispatches 'trace:saved' to same-tab consumers immediately.
 * 2. Posts a minimal { type: 'trace_saved', eventId, timestamp } message to other tabs via BroadcastChannel.
 *
 * Does NOT broadcast any photos, audio, observations, coordinates, or private rewards.
 */
export function broadcastTraceSaved(): void {
  const timestamp = Date.now();
  const eventId = `${timestamp}-${Math.random().toString(36).slice(2, 10)}`;

  // Remember our own eventId so sender never processes it even if echoed
  rememberEventId(eventId);

  // 1. Same-tab notification for current tab consumers (works even without BroadcastChannel)
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('trace:saved', {
        detail: { source: 'local', timestamp, eventId },
      })
    );
  }

  // 2. Cross-tab notification to other tabs
  if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
    try {
      // Use active channel if open, or create a transient one
      const channel = activeChannel || new BroadcastChannel(TRACE_BROADCAST_CHANNEL);
      const payload: TraceBroadcastMessage = {
        type: 'trace_saved',
        eventId,
        timestamp,
      };
      channel.postMessage(payload);

      // If we created a transient channel, close it
      if (channel !== activeChannel) {
        channel.close();
      }
    } catch (err) {
      console.warn('[crossTabSync] Failed to postMessage to BroadcastChannel:', err);
    }
  }
}
