#!/usr/bin/env python3
"""古文単語データの整合性チェック。使い方: python validate.py"""
import json, sys
from pathlib import Path
d = Path(__file__).parent
ws = json.loads((d / "words.json").read_text(encoding="utf-8"))
CONJ = {"四段活用","上一段活用","上二段活用","下一段活用","下二段活用","カ変","サ変","ナ変","ラ変","ク活用","シク活用","ナリ活用","タリ活用"}
KEI = {"尊敬語","謙譲語","丁寧語"}
err = []
seen_w, seen_no = {}, {}
for x in ws:
    for key, seen in (("w", seen_w), ("no", seen_no)):
        if x[key] in seen: err.append(f"重複: {key}={x[key]}")
        seen[x[key]] = 1
    if x.get("conj") and x["conj"] not in CONJ: err.append(f"{x['w']}: 未定義の活用 {x['conj']}")
    if x.get("kei") and x["kei"] not in KEI: err.append(f"{x['w']}: 未定義の敬語 {x['kei']}")
    if x.get("tb") and len(x["tb"]) != 6: err.append(f"{x['w']}: 活用表が6項目でない")
    if x["ex"]["t"].count(x["ex"]["b"]) != 1: err.append(f"{x['w']}: 例文の空欄語が1回だけ現れない")
    if x.get("gi") and any(x["gi"] in m or m in x["gi"] for m in x["m"]): err.append(f"{x['w']}: 古今異義の語が意味と重なる")
    if x["pos"] == "動詞" and not x.get("conj"): err.append(f"{x['w']}: 動詞に活用の種類がない")
if err: print("NG:", len(err)); print("\n".join(err)); sys.exit(1)
print(f"OK: {len(ws)}語")
