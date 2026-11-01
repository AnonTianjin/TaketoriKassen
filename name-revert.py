#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
name-revert.py —— 人名 / 武器名直接替换脚本（Python 版，规则来自同目录 map.tsv）

功能：
  1) compare：把 map.tsv 的「新名」与当前 src/main/resources/characters.yml、
     weapons.yml 里的角色 id / 显示名、武器 id / 显示名逐条比对，列出映射漂移。
  2) replace：按 map.tsv 直接替换仓库里的人名、武器名及其 id（默认 revert：新名→旧名）。
     支持 -Direction apply 反方向；支持 --kinds 只替换指定类别；--dry-run 只统计不落盘。

与 revert.ps1 的差异：
  * 纯 Python，零第三方依赖（compare 需要 PyYAML，replace 不需要）。
  * 增加 compare 子命令，先核对再替换，避免用过期映射替换漏项。
  * 文件来源优先 git ls-files，跳过 build/.git/.gradle/.idea/.name-revert 与二进制。

用法：
  python .name-revert/name-revert.py compare
  python .name-revert/name-revert.py replace --dry-run
  python .name-revert/name-revert.py replace --direction apply
  python .name-revert/name-revert.py replace --kinds charname,wname --dry-run
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文/符号报 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

KINDS = ("proj", "projid", "charid", "charname", "wid", "wname", "term", "lore")
BOUNDED = {"projid", "charid", "wid"}          # 走标识符边界匹配
NAME_KINDS = ("charname", "wname")             # 「人名 / 武器名」显示名
ID_KINDS = ("charid", "wid")                   # 对应 id

# 上下文守卫：旧名作中文常用词时，避免在 apply（旧→新）方向误伤日常用语
GUARDS = {
    "雷": r"(?!暴)",
    "帝": r"(?!之)",
    "真实": r"(?!存在|物品|占用|结果|伤害|世界|性|感)",
    "命": r"(?!令|leng|运)",
}

BINARY_EXT = {
    ".jar", ".class", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp",
    ".bundle", ".pack", ".idx", ".zip", ".gz", ".7z", ".exe", ".dll", ".so",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".ogg", ".wav", ".nbt", ".dat",
}
SKIP_DIRS = {".git", "build", ".gradle", "node_modules", "libs", ".idea",
             ".mimosa", ".name-revert"}
MINI_RE = re.compile(r"</?[^>]+>")


def strip_mini(text):
    """去掉 MiniMessage 标签，取纯显示文本。"""
    return MINI_RE.sub("", text or "").strip()


# ---------------------------------------------------------------- map.tsv

def load_map(map_path):
    rules, exceptions = [], []
    for lineno, raw in enumerate(Path(map_path).read_text("utf-8").splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        kind = parts[0].strip()
        if kind == "例外":
            if len(parts) >= 4:
                exceptions.append((parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()))
            continue
        if len(parts) < 3:
            raise ValueError(f"map.tsv 第 {lineno} 行格式不对，需要 3 列 TAB 分隔：{line!r}")
        rules.append({"kind": kind, "old": parts[1], "new": parts[2], "line": lineno})
    return rules, exceptions


def build_replace_rules(rules, direction):
    out = []
    for r in rules:
        if direction == "revert":
            frm, to = r["new"], r["old"]
            guard = ""
        else:
            frm, to = r["old"], r["new"]
            guard = GUARDS.get(frm, "")
        if not frm:
            continue
        out.append({
            "kind": r["kind"], "frm": frm, "to": to,
            "bounded": r["kind"] in BOUNDED, "guard": guard,
        })
    # 长串优先：kaguya_hammer 先于 kaguya，帝之大太刀先于帝
    out.sort(key=lambda x: len(x["frm"]), reverse=True)
    return out


# ---------------------------------------------------------------- files

def collect_files(root):
    files = []
    if (root / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "ls-files"], cwd=str(root),
                capture_output=True, text=True, encoding="utf-8",
            )
            if res.returncode == 0 and res.stdout.strip():
                files = [ln for ln in res.stdout.splitlines() if ln.strip()]
        except OSError:
            files = []
    if not files:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                files.append(rel)
    result = []
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext in BINARY_EXT:
            continue
        segs = re.split(r"[\\/]", rel)
        if any(s in SKIP_DIRS for s in segs):
            continue
        result.append(rel)
    return result


# ---------------------------------------------------------------- compare

def load_config_names(root):
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("compare 需要 PyYAML：pip install pyyaml") from exc
    chars = yaml.safe_load((root / "src/main/resources/characters.yml").read_text("utf-8"))["characters"]
    weapons = yaml.safe_load((root / "src/main/resources/weapons.yml").read_text("utf-8"))["weapons"]
    char_disp = {cid: strip_mini(rec.get("display", "")) for cid, rec in chars.items()}
    weapon_disp = {wid: strip_mini(rec.get("display", "")) for wid, rec in weapons.items()}
    return chars, weapons, char_disp, weapon_disp


def run_compare(root, rules):
    chars, weapons, char_disp, weapon_disp = load_config_names(root)
    by_kind = {}
    for r in rules:
        by_kind.setdefault(r["kind"], []).append(r)

    print(f"目标仓库：{root}")
    print(f"角色 {len(char_disp)} 个，武器 {len(weapon_disp)} 把，map.tsv 规则 {len(rules)} 条")
    print("=" * 78)

    ok = True

    def section(title, mapped_new, current, kept=()):
        nonlocal ok
        mapped_new = {x for x in mapped_new if x}
        current = set(current)
        missing = sorted(mapped_new - current)      # 映射里写了，但仓库没有 → 过期/未落地
        extra = sorted(current - mapped_new - set(kept))  # 仓库有，但映射没写 → 新增/公共词
        print(f"\n[{title}] 映射 {len(mapped_new)} 条 / 仓库 {len(current)} 项")
        if missing:
            ok = False
            print("  [X] 映射的「新值」在仓库中找不到（映射过时或尚未落地）：")
            for x in missing:
                print(f"      - {x}")
        if extra:
            print("  ! 仓库中存在但未纳入映射（公共词或保留名可忽略）：")
            for x in extra:
                print(f"      - {x}")
        if not missing and not extra:
            print("  [OK] 完全一致")

    section("角色 id（charid）",
            [r["new"] for r in by_kind.get("charid", [])], char_disp.keys())
    section("角色显示名（charname）",
            [r["new"] for r in by_kind.get("charname", [])], char_disp.values())
    section("武器 id（wid）",
            [r["new"] for r in by_kind.get("wid", [])], weapon_disp.keys(),
            kept=("moon_mirror", "frozen_swordfish"))
    section("武器显示名（wname）",
            [r["new"] for r in by_kind.get("wname", [])], weapon_disp.values())

    print("\n" + "=" * 78)
    print("结论：" + ("全部一致，可安全替换。" if ok else "存在映射漂移，请先更新 map.tsv 的「新值」再替换。"))
    return 0 if ok else 2


# ---------------------------------------------------------------- replace

def run_replace(root, rules, direction, kinds, dry_run):
    selected = [r for r in rules if r["kind"] in kinds]
    picked = build_replace_rules(selected, direction)
    files = collect_files(root)

    total_hits, changed = 0, []
    for rel in files:
        full = root / rel
        try:
            text = full.read_text("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        original = text
        hits, used = 0, set()
        for r in picked:
            if r["bounded"]:
                pattern = r"(?<![A-Za-z0-9_])" + re.escape(r["frm"]) + r"(?![A-Za-z0-9_])"
            else:
                pattern = re.escape(r["frm"]) + r["guard"]
            rx = re.compile(pattern)
            n = len(rx.findall(text))
            if n:
                text = rx.sub(lambda m: r["to"], text)
                hits += n
                used.add(r["kind"])
        if text != original:
            total_hits += hits
            changed.append((rel, hits, ",".join(sorted(used))))
            if not dry_run:
                full.write_text(text, encoding="utf-8")

    mode = "演练（未落盘）" if dry_run else "已写回"
    print(f"\n方向 {direction} / {mode} / 类别 {','.join(kinds)} / 规则 {len(picked)} 条 -> {root}")
    print("-" * 78)
    if not changed:
        print("没有任何文件命中规则。")
    else:
        for rel, hits, kinds_used in sorted(changed):
            print(f"  {rel:<52} {hits:>4} 处  [{kinds_used}]")
        print("-" * 78)
        print(f"合计 {len(changed)} 个文件，{total_hits} 处替换。")
    if dry_run:
        print("\n提示：去掉 --dry-run 即写回。revert=新名→旧名，apply=旧名→新名。")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="人名 / 武器名直接替换（规则来自 map.tsv）")
    ap.add_argument("command", choices=["compare", "replace"], help="compare=比对；replace=替换")
    ap.add_argument("--direction", choices=["revert", "apply"], default="revert",
                    help="revert=新名→旧名（默认）；apply=旧名→新名")
    ap.add_argument("--path", default="", help="要处理的仓库根目录，默认脚本上一级")
    ap.add_argument("--dry-run", action="store_true", help="只统计不落盘")
    ap.add_argument("--kinds", default=",".join(KINDS),
                    help="参与替换的类别，逗号分隔；只换人名武器名可用简写 names 或 charid,charname,wid,wname")
    ap.add_argument("--map", default="", help="map.tsv 路径，默认脚本同目录")
    args = ap.parse_args(argv)

    root = Path(args.path).resolve() if args.path else DEFAULT_ROOT
    map_path = Path(args.map) if args.map else HERE / "map.tsv"
    if not map_path.exists():
        raise SystemExit(f"找不到规则表：{map_path}")

    rules, _exceptions = load_map(map_path)
    if args.command == "compare":
        return run_compare(root, rules)

    aliases = {"names": ["charid", "charname", "wid", "wname"],
               "ids": ["charid", "wid"]}
    kinds = []
    for k in (x.strip() for x in args.kinds.split(",") if x.strip()):
        kinds.extend(aliases.get(k, [k]))
    # 去重并保持顺序
    kinds = list(dict.fromkeys(kinds))
    bad = [k for k in kinds if k not in KINDS]
    if bad:
        raise SystemExit(f"未知类别：{bad}，可选：{', '.join(KINDS)}")
    return run_replace(root, rules, args.direction, kinds, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
