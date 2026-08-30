#!/usr/bin/env python3
"""自动解决 hindsight-cn fork 与 upstream/main 合并冲突。

在 `git merge upstream/main` 出现冲突后运行，然后提交合并。
策略与手动合并保持一致（保护 CN 定制 + 吸收上游功能）：

- zh-CN.json 等中文 i18n：本地术语优先（沉淀认知/知识摘要），上游新增 key 并入并做术语归一
- package.json：本地依赖版本优先（取较新），上游新增依赖并入
- package-lock.json / uv.lock：取上游版本（由构建/部署时重新生成对齐）
- 其余冲突文件（README.md、.env.example、Dockerfile、start-all.sh、test.yml 等）：保留本地

用法：
  python3 scripts/auto-resolve-merge.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

# 术语归一表：仅作用于上游新增的文案，本地文案不受影响（已符合术语）
TERM_MAP = [
    ("心智模型", "知识摘要"),
    ("观察范围", "沉淀认知范围"),
    ("每条观察", "每条沉淀认知"),
    ("生成单个观察", "生成单个沉淀认知"),
    ("最大观察数", "最大沉淀认知数"),
    ("个观察", "个沉淀认知"),
]

# 需智能 JSON 合并的文件（相对仓库根）
I18N_JSON = ["hindsight-control-plane/src/messages/zh-CN.json"]
PKG_JSON = ["hindsight-control-plane/package.json"]
# 采用上游版本（theirs）的锁文件
THEIRS_FILES = {"package-lock.json", "uv.lock"}


def sh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def get_conflicts() -> list[str]:
    r = sh("git", "diff", "--name-only", "--diff-filter=U")
    return [f for f in r.stdout.splitlines() if f]


def json_merge(local, upstream):
    """本地值优先，上游新增 key 并入（递归）。"""
    if not isinstance(local, dict) or not isinstance(upstream, dict):
        return local
    out = dict(local)
    for k, v in upstream.items():
        if k not in out:
            out[k] = v
        elif isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = json_merge(out[k], v)
    return out


def term_normalize(text: str) -> str:
    for old, new in TERM_MAP:
        text = text.replace(old, new)
    return text


def fix_i18n_json(path: str) -> None:
    """合并中文 i18n：本地值优先 + 上游新增 key 并入 + 术语归一。

    merge 冲突时工作区文件含冲突标记，因此本地版本从 `git show HEAD:path`
    读取（ours 侧 = fork 当前分支），上游从 `git show upstream/main:path` 读取。
    """
    r_local = sh("git", "show", "HEAD:" + path)
    if r_local.returncode != 0:
        print(f"  [跳过] 本地无 {path}")
        return
    local = json.loads(r_local.stdout)
    r = sh("git", "show", "upstream/main:" + path)
    if r.returncode != 0:
        print(f"  [跳过] 上游无 {path}")
        return
    upstream = json.loads(r.stdout)

    merged = json_merge(local, upstream)

    # 术语归一（递归字符串值）
    def walk(d):
        for k, v in d.items():
            if isinstance(v, str):
                d[k] = term_normalize(v)
            elif isinstance(v, dict):
                walk(v)

    walk(merged)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    sh("git", "add", "--force", path)
    print(f"  [i18n] {path} 已合并（本地术语优先 + 上游新 key）")


def fix_package_json(path: str) -> None:
    """合并 package.json：本地依赖版本优先 + 上游新增依赖并入。"""
    r_local = sh("git", "show", "HEAD:" + path)
    if r_local.returncode != 0:
        return
    local = json.loads(r_local.stdout)
    r = sh("git", "show", "upstream/main:" + path)
    if r.returncode != 0:
        return
    upstream = json.loads(r.stdout)

    merged = json_merge(local, upstream)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    sh("git", "add", "--force", path)
    print(f"  [pkg] {path} 已合并（本地版本优先 + 上游新依赖）")


def take_ours(path: str) -> None:
    """保留本地版本。"""
    if sh("git", "checkout", "--ours", "--", path).returncode != 0:
        sh("git", "rm", "--force", "--", path)
    sh("git", "add", "--force", "--", path)
    print(f"  [本地] {path}")


def take_theirs(path: str) -> None:
    """采用上游版本。"""
    if sh("git", "checkout", "--theirs", "--", path).returncode != 0:
        sh("git", "rm", "--force", "--", path)
    sh("git", "add", "--force", "--", path)
    print(f"  [上游] {path}")


def main() -> int:
    conflicts = get_conflicts()
    if not conflicts:
        print("无冲突文件")
        return 0
    print(f"待解决冲突 {len(conflicts)} 个文件")
    for path in conflicts:
        if path in I18N_JSON:
            fix_i18n_json(path)
        elif path in PKG_JSON:
            fix_package_json(path)
        elif path in THEIRS_FILES:
            take_theirs(path)
        else:
            take_ours(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())