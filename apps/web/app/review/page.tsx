import { redirect } from 'next/navigation';

// Source review queue and review decisions were consolidated into the canonical
// /quality gate dashboard (PR4). Keep this route reachable so existing
// links/bookmarks (including Command Center) do not 404.
export default function ReviewRedirect() {
  redirect('/quality');
}
