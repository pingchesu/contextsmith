import { redirect } from 'next/navigation';

// Retrieval eval runs, history, and evidence were consolidated into the
// canonical /quality gate dashboard (PR4). Keep this route reachable so
// existing links/bookmarks do not 404.
export default function EvalsRedirect() {
  redirect('/quality');
}
