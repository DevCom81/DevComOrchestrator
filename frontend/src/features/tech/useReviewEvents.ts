import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";
import type { TechEventDto, TechEventListDto } from "./techTypes";

const POLL_MS = 3000;
const MAX_SSE_RETRIES = 5;

export function useReviewEvents(reviewId: string, active: boolean) {
  const client = useQueryClient();
  const [events, setEvents] = useState<TechEventDto[]>([]);
  const [loading, setLoading] = useState(true);
  const cursor = useRef(0);

  useEffect(() => {
    if (!reviewId || !active) {
      return;
    }
    let cancelled = false;
    let source: EventSource | null = null;
    let pollTimer: number | undefined;
    let retries = 0;

    async function pull(after: number) {
      const page = await apiGet<TechEventListDto>(
        `/api/tech/reviews/${reviewId}/events?after_seq=${after}&limit=100`,
      );
      if (cancelled) {
        return page;
      }
      if (page.items.length) {
        cursor.current = page.items[page.items.length - 1]?.seq ?? cursor.current;
        setEvents((prev) => mergeEvents(prev, page.items));
        void client.invalidateQueries({ queryKey: ["tech-review", reviewId] });
      }
      setLoading(false);
      return page;
    }

    function startPoll() {
      pollTimer = window.setInterval(() => {
        void pull(cursor.current);
      }, POLL_MS);
    }

    function startSse() {
      source = new EventSource(
        `/api/tech/reviews/${reviewId}/events/stream?after_seq=${cursor.current}`,
      );
      source.onmessage = (message) => {
        try {
          const item = JSON.parse(message.data) as TechEventDto;
          cursor.current = item.seq;
          setEvents((prev) => mergeEvents(prev, [item]));
          void client.invalidateQueries({ queryKey: ["tech-review", reviewId] });
        } catch {
          /* ignore malformed frames */
        }
      };
      source.onerror = () => {
        source?.close();
        source = null;
        retries += 1;
        if (retries >= MAX_SSE_RETRIES) {
          startPoll();
          return;
        }
        window.setTimeout(() => {
          if (!cancelled) {
            startSse();
          }
        }, 1000 * retries);
      };
    }

    void pull(0).then(() => {
      if (!cancelled) {
        startSse();
      }
    });

    return () => {
      cancelled = true;
      source?.close();
      if (pollTimer !== undefined) {
        window.clearInterval(pollTimer);
      }
    };
  }, [reviewId, active, client]);

  return { events, loading };
}

function mergeEvents(prev: TechEventDto[], incoming: TechEventDto[]): TechEventDto[] {
  const bySeq = new Map(prev.map((item) => [item.seq, item]));
  for (const item of incoming) {
    bySeq.set(item.seq, item);
  }
  return [...bySeq.values()].sort((a, b) => a.seq - b.seq);
}
