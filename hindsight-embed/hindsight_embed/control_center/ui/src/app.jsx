import { Fragment } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import { api, forgetToken, pn, profileParam, syncProfileUrl, tabParam } from "./api.js";
import { ServicePanel } from "./service-panel.jsx";

const TABS = [
  { id: "quick", label: "快速配置" },
  { id: "config", label: "配置" },
  { id: "files", label: "文件" },
  { id: "logs", label: "日志" },
];

const escHtml = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Highlight active KEY=value lines; dim comments/blanks.
function envHighlight(text) {
  return text
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (t === "") return "<span></span>";
      if (t.startsWith("#")) return `<span class="l-off">${escHtml(line)}</span>`;
      const eq = line.indexOf("=");
      if (eq > 0)
        return (
          `<span class="l-on"><span class="k">${escHtml(line.slice(0, eq))}</span>` +
          `<span class="eq">=</span>${escHtml(line.slice(eq + 1))}</span>`
        );
      return `<span class="l-on">${escHtml(line)}</span>`;
    })
    .join("\n");
}

export function App() {
  const [version, setVersion] = useState("");
  const [noAuth, setNoAuth] = useState(false);
  const [providers, setProviders] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [current, setCurrent] = useState(null); // "" = default, null = none
  const [tab, setTab] = useState("quick");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState({ text: "", kind: "" });

  // Quick-config form
  const [cfg, setCfg] = useState(null);
  const [form, setForm] = useState({ provider: "", apiKey: "", model: "", apiPort: "", uiPort: "", apiVersion: "", cpVersion: "" });

  // status / health
  const [daemonRunning, setDaemonRunning] = useState(false);
  const [uiRunning, setUiRunning] = useState(false);
  const [daemonText, setDaemonText] = useState("—");
  const [uiText, setUiText] = useState("—");
  const [health, setHealth] = useState({ api_ok: false, api_detail: "", ui_ok: false });
  const [paths, setPaths] = useState(null);

  // env editor + logs
  const [envText, setEnvText] = useState("");
  const [envPath, setEnvPath] = useState("");
  const [envMsg, setEnvMsg] = useState({ text: "", kind: "" });
  const [envEffective, setEnvEffective] = useState(true); // show only active KEY=value lines
  const [logText, setLogText] = useState("");
  const [logPath, setLogPath] = useState("");
  const [logLines, setLogLines] = useState(200);
  const [logAuto, setLogAuto] = useState(true);
  const [logSource, setLogSource] = useState("daemon"); // "daemon" (API) or "ui" (control plane)

  const busyRef = useRef(false);
  busyRef.current = busy;
  const envPre = useRef(null);
  const envArea = useRef(null);

  const onUnauthorized = (e) => {
    if (e && e.unauthorized) {
      forgetToken();
      setNoAuth(true);
      return true;
    }
    return false;
  };

  // ----- data loads ----------------------------------------------------
  async function loadProfiles() {
    const { profiles } = await api("GET", "/api/profiles");
    setProfiles(profiles);
    return profiles;
  }

  async function selectProfile(name) {
    setCurrent(name);
    syncProfileUrl(name);
    setMsg({ text: "", kind: "" });
    try {
      const [cfgv, pathsv, env] = await Promise.all([
        api("GET", `/api/profiles/${pn(name)}/config`),
        api("GET", `/api/profiles/${pn(name)}/paths`),
        api("GET", `/api/profiles/${pn(name)}/env`),
      ]);
      setCfg(cfgv);
      setForm({
        provider: cfgv.provider || (providers[0] && providers[0].id) || "openai",
        apiKey: "",
        model: cfgv.model || "",
        apiPort: String(cfgv.api_port),
        uiPort: cfgv.ui_port_is_default ? "" : String(cfgv.ui_port),
        apiVersion: cfgv.api_version || "",
        cpVersion: cfgv.cp_version || "",
      });
      setPaths(pathsv);
      setEnvText(env.content);
      setEnvPath(env.path);
      setEnvMsg({ text: "", kind: "" });
    } catch (e) {
      onUnauthorized(e);
    }
  }

  async function loadLogs(name = current) {
    if (name === null) return;
    try {
      const r = await api("GET", `/api/profiles/${pn(name)}/logs?lines=${logLines}&source=${logSource}`);
      setLogPath(r.path);
      setLogText(r.exists ? r.content || "（空）" : "（尚无日志文件）");
    } catch (e) {
      if (!onUnauthorized(e)) setLogText(e.message);
    }
  }

  async function refreshHealth(name = current) {
    if (name === null || busyRef.current) return;
    try {
      const h = await api("GET", `/api/profiles/${pn(name)}/health`);
      setHealth(h);
      setDaemonRunning(h.api_ok);
      setUiRunning(h.ui_ok);
      setDaemonText(h.api_ok ? "运行中" : "已停止");
      setUiText(h.ui_ok ? "运行中" : "已停止");
    } catch (e) {
      onUnauthorized(e);
    }
  }

  // ----- actions -------------------------------------------------------
  function keyPayload() {
    if (form.apiKey) return form.apiKey;
    return cfg && cfg.has_api_key ? "__unchanged__" : "";
  }

  async function save() {
    setMsg({ text: "保存中…", kind: "" });
    try {
      await api("POST", `/api/profiles/${pn(current)}/config`, {
        provider: form.provider,
        api_key: keyPayload(),
        model: form.model.trim(),
        api_port: form.apiPort.trim(),
        ui_port: form.uiPort.trim(),
        api_version: form.apiVersion.trim(),
        cp_version: form.cpVersion.trim(),
      });
      setMsg({ text: "已保存。重启守护进程后生效。", kind: "ok" });
      await selectProfile(current);
      loadProfiles();
    } catch (e) {
      if (!onUnauthorized(e)) setMsg({ text: e.message, kind: "err" });
    }
  }

  async function saveEnv() {
    setEnvMsg({ text: "保存中…", kind: "" });
    try {
      await api("POST", `/api/profiles/${pn(current)}/env`, { content: envText });
      setEnvMsg({ text: "已保存。重启守护进程后生效。", kind: "ok" });
      loadProfiles();
    } catch (e) {
      if (!onUnauthorized(e)) setEnvMsg({ text: e.message, kind: "err" });
    }
  }

  async function daemonAction(action) {
    setBusy(true);
    setLogSource("daemon");
    setTab("logs"); // jump to the daemon log so the user can watch it
    setDaemonText({ start: "启动中…", stop: "停止中…", restart: "重启中…" }[action] || "处理中…");
    try {
      const r = await api("POST", `/api/profiles/${pn(current)}/daemon/${action}`);
      setDaemonRunning(r.running);
      setDaemonText(r.running ? "运行中" : "已停止");
    } catch (e) {
      if (!onUnauthorized(e)) setMsg({ text: e.message, kind: "err" });
    } finally {
      setBusy(false);
      loadProfiles();
      loadLogs();
    }
  }

  async function cpAction(action) {
    setBusy(true);
    setLogSource("ui");
    setTab("logs"); // jump to the control-plane log so the user can see why it starts/fails
    setUiText({ start: "启动中…", stop: "停止中…", restart: "重启中…" }[action] || "处理中…");
    try {
      const u = await api("POST", `/api/profiles/${pn(current)}/ui/${action}`);
      setUiRunning(u.running);
      setUiText(u.running ? "运行中" : "已停止");
    } catch (e) {
      if (!onUnauthorized(e)) setMsg({ text: e.message, kind: "err" });
    } finally {
      setBusy(false);
      loadProfiles();
      refreshHealth();
    }
  }

  async function deleteProfile() {
    if (!current) return; // default profile isn't deletable
    if (!confirm(`删除配置档 "${current}"？这将停止其守护进程并删除其配置与日志，且无法撤销。`))
      return;
    setBusy(true);
    try {
      const r = await api("POST", `/api/profiles/${pn(current)}/delete`);
      if (!r.ok) {
        setMsg({ text: r.message, kind: "err" });
        return;
      }
      setCurrent(null);
      history.replaceState(null, "", location.pathname);
      loadProfiles();
    } catch (e) {
      if (!onUnauthorized(e)) setMsg({ text: e.message, kind: "err" });
    } finally {
      setBusy(false);
    }
  }

  // ----- effects -------------------------------------------------------
  // Boot: health (version), providers, profiles, optional deep-link.
  useEffect(() => {
    (async () => {
      try {
        const h = await fetch("/api/health").then((r) => r.json());
        setVersion("v" + h.version);
        const { providers } = await api("GET", "/api/providers");
        setProviders(providers);
        const list = await loadProfiles();
        if (profileParam !== null) {
          const internal = profileParam === "default" ? "" : profileParam;
          if (list.some((p) => p.name === internal)) {
            await selectProfile(internal);
            if (tabParam && TABS.some((t) => t.id === tabParam)) setTab(tabParam);
          }
        }
      } catch (e) {
        onUnauthorized(e);
      }
    })();
  }, []);

  // Health poll for the selected profile (every 4s).
  useEffect(() => {
    if (current === null) return;
    refreshHealth(current);
    const id = setInterval(() => refreshHealth(current), 4000);
    return () => clearInterval(id);
  }, [current]);

  // Log tail poll while the Logs tab is open.
  useEffect(() => {
    if (current === null || tab !== "logs") return;
    loadLogs(current);
    if (!logAuto) return;
    const id = setInterval(() => loadLogs(current), 2000);
    return () => clearInterval(id);
  }, [current, tab, logAuto, logLines, logSource]);

  // Keep the highlight layer scroll-synced with the textarea.
  const syncEnvScroll = () => {
    if (envPre.current && envArea.current) {
      envPre.current.scrollTop = envArea.current.scrollTop;
      envPre.current.scrollLeft = envArea.current.scrollLeft;
    }
  };

  // ----- render --------------------------------------------------------
  const defaultVer = version.replace(/^v/, "") || "embed default";
  // "Effective only" shows just active KEY=value lines (read-only); the full
  // envText is preserved for editing/saving when the toggle is off.
  const envDisplay = envEffective
    ? envText.split("\n").filter((l) => l.trim() && !l.trim().startsWith("#")).join("\n")
    : envText;

  if (noAuth) {
    return (
      <Fragment>
        <AppBar version={version} />
        <div class="banner">
          暂无访问令牌。请先通过 CLI 打开一次控制中心——之后此 URL 会被记住，你可以收藏它：<code>hindsight-embed control start</code>
        </div>
      </Fragment>
    );
  }

  return (
    <Fragment>
      <AppBar version={version} />
      <div class="shell">
        <aside class="sidebar">
          <div class="sect">配置档</div>
          <ul class="profiles">
            {profiles.map((p) => (
              <li
                key={p.name}
                class={p.name === current ? "sel" : ""}
                onClick={() => selectProfile(p.name)}
                ref={(el) => p.name === current && el && el.scrollIntoView({ block: "nearest" })}
              >
                <span class={"dot " + (p.daemon_running ? "on" : "off")} />
                <span class="nm">{p.display_name}</span>
                {p.is_active && <span class="badge">活跃</span>}
              </li>
            ))}
          </ul>
        </aside>

        <main class="content">
          {current === null ? (
            <div class="empty">从左侧选择一个配置档以查看和编辑。</div>
          ) : (
            <Fragment>
              <div class="chead">
                <div class="chead-row">
                  <span class="ptitle grad-text">{cfg ? cfg.display_name : ""}</span>
                  <span style="margin-left:auto" />
                  {current !== "" && (
                    <button class="ghost danger" disabled={busy} onClick={deleteProfile}>
                      删除配置档
                    </button>
                  )}
                </div>
                <div class="services">
                  <ServicePanel
                    title="API"
                    running={daemonRunning}
                    statusText={daemonText}
                    healthOk={health.api_ok}
                    url={paths && paths.daemon_url}
                    detail={health.api_ok ? health.api_detail : "不可达"}
                    busy={busy}
                    onStart={() => daemonAction("start")}
                    onRestart={() => daemonAction("restart")}
                    onStop={() => daemonAction("stop")}
                  />
                  <ServicePanel
                    title="控制平面"
                    running={uiRunning}
                    statusText={uiText}
                    healthOk={health.ui_ok}
                    url={paths && paths.ui_url}
                    detail=""
                    busy={busy}
                    onStart={() => cpAction("start")}
                    onRestart={() => cpAction("restart")}
                    onStop={() => cpAction("stop")}
                  />
                </div>
              </div>

              <div class="tabs">
                {TABS.map((t) => (
                  <div key={t.id} class={"tab " + (tab === t.id ? "active " : "") + (tab === t.id ? "grad-text" : "")} onClick={() => setTab(t.id)}>
                    {t.label}
                  </div>
                ))}
              </div>

              {tab === "quick" && cfg && (
                <div class="panel narrow">
                  <label>
                    提供商
                    <select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                      {providers.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    API key
                    <input
                      type="password"
                      autocomplete="off"
                      value={form.apiKey}
                      onInput={(e) => setForm({ ...form, apiKey: e.target.value })}
                    />
                    <span class="hint">
                      {cfg.has_api_key ? `已存储密钥（${cfg.api_key_masked}）。留空则保持不变。` : "尚未存储密钥。"}
                    </span>
                  </label>
                  <label>
                    模型 <span class="hint">（留空 = 提供商默认）</span>
                    <input type="text" autocomplete="off" placeholder="提供商默认" value={form.model} onInput={(e) => setForm({ ...form, model: e.target.value })} />
                  </label>
                  <div class="ports">
                    <label>
                      API 端口
                      <input type="number" value={form.apiPort} onInput={(e) => setForm({ ...form, apiPort: e.target.value })} />
                    </label>
                    <label>
                      UI 端口 <span class="hint">（留空 = API + 10000）</span>
                      <input type="number" placeholder={String(cfg.ui_port)} value={form.uiPort} onInput={(e) => setForm({ ...form, uiPort: e.target.value })} />
                    </label>
                  </div>
                  <div class="ports">
                    <label>
                      API 版本 <span class="hint">（留空 = {defaultVer}）</span>
                      <input type="text" autocomplete="off" placeholder={defaultVer} value={form.apiVersion} onInput={(e) => setForm({ ...form, apiVersion: e.target.value })} />
                    </label>
                    <label>
                      控制平面版本 <span class="hint">（留空 = {defaultVer}）</span>
                      <input type="text" autocomplete="off" placeholder={defaultVer} value={form.cpVersion} onInput={(e) => setForm({ ...form, cpVersion: e.target.value })} />
                    </label>
                  </div>
                  <div class="row">
                    <button onClick={save} disabled={busy}>
                      保存
                    </button>
                  </div>
                  <div class={"msg " + msg.kind}>{msg.text}</div>
                </div>
              )}

              {tab === "config" && (
                <div class="panel">
                  <div class="note">
                    此配置档的 <code>{envPath}</code>——其中以明文形式包含你的 API 密钥。活跃的{" "}
                    <code>KEY=value</code> 行会高亮显示，注释会变暗。保存后需重启守护进程才能生效。
                  </div>
                  <label class="row" style="margin-bottom:12px; color:var(--color-muted); font-size:12px">
                    <input type="checkbox" style="width:auto" checked={envEffective} onChange={(e) => setEnvEffective(e.target.checked)} /> 仅显示生效项（隐藏注释和空行）
                  </label>
                  <div class="env-editor">
                    <pre class="env-hl" ref={envPre} aria-hidden="true" dangerouslySetInnerHTML={{ __html: envHighlight(envDisplay) }} />
                    <textarea
                      ref={envArea}
                      spellcheck={false}
                      readOnly={envEffective}
                      value={envDisplay}
                      onInput={(e) => setEnvText(e.target.value)}
                      onScroll={syncEnvScroll}
                    />
                  </div>
                  <div class="row" style="margin-top:12px">
                    <button class="ghost" onClick={() => selectProfile(current)}>
                      重新加载
                    </button>
                    {!envEffective && (
                      <button onClick={saveEnv} disabled={busy}>
                        保存 .env
                      </button>
                    )}
                  </div>
                  {envEffective && <div class="hint" style="margin-top:8px">只读视图——取消勾选“仅显示生效项”即可编辑原始文件。</div>}
                  <div class={"msg " + envMsg.kind}>{envMsg.text}</div>
                </div>
              )}

              {tab === "files" && paths && (
                <div class="panel">
                  <div class="note">
                    此配置档在磁盘上的位置与 URL——包括其配置文件、守护进程日志、锁文件、本地 pg0 数据库目录，
                    以及守护进程 / 控制平面的地址。
                  </div>
                  <dl class="files">
                    {[
                      ["端口", String(paths.port)],
                      ["配置文件 (.env)", paths.config_path],
                      ["守护进程日志", paths.log_path],
                      ["锁文件", paths.lock_path],
                      ["数据库 URL", paths.database_url],
                      ["数据库目录", paths.database_path || "—"],
                      ["守护进程 URL", paths.daemon_url],
                      ["控制平面", paths.ui_url],
                    ].map(([k, v]) => (
                      <Fragment key={k}>
                        <dt>{k}</dt>
                        <dd>{v}</dd>
                      </Fragment>
                    ))}
                  </dl>
                </div>
              )}

              {tab === "logs" && (
                <div class="panel">
                  <div class="row" style="margin-bottom:12px">
                    <select style="width:auto" value={logSource} onChange={(e) => setLogSource(e.target.value)}>
                      <option value="daemon">API（守护进程）</option>
                      <option value="ui">控制平面</option>
                    </select>
                    <label class="row" style="margin:0; color:var(--color-muted); font-size:12px">
                      <input type="checkbox" style="width:auto" checked={logAuto} onChange={(e) => setLogAuto(e.target.checked)} /> 自动刷新
                    </label>
                    <select style="width:auto" value={logLines} onChange={(e) => setLogLines(Number(e.target.value))}>
                      <option value={100}>100 行</option>
                      <option value={200}>200 行</option>
                      <option value={500}>500 行</option>
                    </select>
                    <button class="ghost" onClick={() => loadLogs()}>
                      刷新
                    </button>
                    <span class="hint">{logPath}</span>
                  </div>
                  <pre class="logs">{logText || "—"}</pre>
                </div>
              )}
            </Fragment>
          )}
        </main>
      </div>
    </Fragment>
  );
}

function AppBar({ version }) {
  return (
    <div class="appbar">
      <img src="./logo.png" alt="Hindsight" />
      <span class="title grad-text">嵌入版控制中心</span>
      <span class="ver">{version}</span>
    </div>
  );
}
