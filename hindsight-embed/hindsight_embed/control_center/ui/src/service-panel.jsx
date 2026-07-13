// One of the two header panels (API / Control plane): health dot, status pill,
// URL, optional detail, and state-aware Start/Restart/Stop.
export function ServicePanel({ title, running, statusText, healthOk, url, detail, busy, onStart, onRestart, onStop }) {
  return (
    <div class="svc">
      <div class="svc-top">
        <span class="svc-name">
          <span class={"hdot " + (healthOk ? "ok" : "bad")} />
          {title}
        </span>
        <span class={"status " + (running ? "on" : "off")}>{statusText}</span>
      </div>
      <a class="svc-url" href={url || "#"} target="_blank" rel="noopener">
        {url}
      </a>
      <div class="svc-detail">{detail}</div>
      <div class="svc-actions">
        <button class="ghost sm" disabled={busy || running} onClick={onStart}>
          启动
        </button>
        <button class="ghost sm" disabled={busy || !running} onClick={onRestart}>
          重启
        </button>
        <button class="ghost sm" disabled={busy || !running} onClick={onStop}>
          停止
        </button>
      </div>
    </div>
  );
}
