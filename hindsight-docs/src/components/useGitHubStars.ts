import {useEffect, useState} from 'react';
import {usePluginData} from '@docusaurus/useGlobalData';

const REPO = 'vectorize-io/hindsight';
const CACHE_KEY = 'github-stars';

/* One request per browser session, shared by every caller on the page. The
   unauthenticated 60/hr limit is per visitor IP, not per site, so this is the
   same pattern Material for MkDocs ships on every site built with it. (The count
   used to be build-time only, on the belief that browser fetches would exhaust
   the limit; instead the deploy build got 403s and shipped the 10k fallback.) */
let live: Promise<number | null> | null = null;
function fetchLiveStars(): Promise<number | null> {
  if (live) return live;
  try {
    const cached = Number(sessionStorage.getItem(CACHE_KEY));
    if (cached > 0) return (live = Promise.resolve(cached));
  } catch {
    // Storage blocked (private mode, sandboxed iframe): just fetch.
  }
  live = fetch(`https://api.github.com/repos/${REPO}`)
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      const stars = data?.stargazers_count;
      if (typeof stars !== 'number') return null;
      try {
        sessionStorage.setItem(CACHE_KEY, String(stars));
      } catch {
        // Not cached; the next page load fetches again.
      }
      return stars;
    })
    .catch(() => null);
  return live;
}

/**
 * Star count, pre-formatted for display ("12.4k"). Shared by the navbar GitHub
 * item and the homepage hero so the two can never disagree.
 *
 * Renders the build-time count from the `github-stars` plugin first (no layout
 * shift, works without JS), then swaps in the live count — so a build that hit
 * GitHub's rate limit and baked in the fallback still shows the real number.
 */
export function useGitHubStars(): string {
  const data = usePluginData('github-stars') as {stars?: number} | undefined;
  const [stars, setStars] = useState(data?.stars);
  useEffect(() => {
    let active = true;
    fetchLiveStars().then((n) => {
      if (active && n !== null) setStars(n);
    });
    return () => {
      active = false;
    };
  }, []);
  if (typeof stars !== 'number') return '';
  return stars >= 1000 ? `${(stars / 1000).toFixed(1)}k` : String(stars);
}
