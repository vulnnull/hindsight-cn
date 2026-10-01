/**
 * Build-time GitHub star count.
 *
 * The navbar GitHub item and the homepage hero both show the star count — it is
 * the cheapest social proof on the page and turns an unlabeled icon into a
 * target worth clicking. The build-time number is the first paint (no layout
 * shift, no JS needed); `useGitHubStars` then refreshes it from the visitor's
 * browser, so a stale or fallback build number never sticks.
 *
 * FALLBACK is what renders when the fetch fails — offline dev, a CI runner with
 * no egress, or a rate-limited IP. It is deliberately a round number below the
 * real count: a stale-low number is honest, a stale-high one is not.
 */
const FALLBACK = 40000;
const REPO = 'vectorize-io/hindsight';

/* A build must not be able to hang on this. Without a deadline a slow or
   black-holed api.github.com stalls `docusaurus build` indefinitely, which in CI
   means a job that burns its whole timeout for a decoration. Five seconds is far
   more than the call needs and the fallback covers the rest. */
const TIMEOUT_MS = 5000;

module.exports = function githubStarsPlugin() {
  return {
    name: 'github-stars',

    async loadContent() {
      try {
        const res = await fetch(`https://api.github.com/repos/${REPO}`, {
          signal: AbortSignal.timeout(TIMEOUT_MS),
          headers: {
            Accept: 'application/vnd.github+json',
            // GITHUB_TOKEN lifts the 60/hr unauthenticated limit on shared CI IPs.
            ...(process.env.GITHUB_TOKEN
              ? {Authorization: `Bearer ${process.env.GITHUB_TOKEN}`}
              : {}),
          },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const {stargazers_count: stars} = await res.json();
        if (typeof stars !== 'number') throw new Error('no stargazers_count');
        return {stars};
      } catch (err) {
        console.warn(
          `[github-stars] could not fetch ${REPO} stars (${err.message}) — using ${FALLBACK}`,
        );
        return {stars: FALLBACK};
      }
    },

    async contentLoaded({content, actions}) {
      actions.setGlobalData(content);
    },
  };
};
