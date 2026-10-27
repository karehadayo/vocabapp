#!/usr/bin/env python3
"""単語データの整合性チェック。使い方: python validate.py"""
import json, re, sys
from pathlib import Path

d = Path(__file__).parent
meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
words = json.loads((d / "words.json").read_text(encoding="utf-8"))
sents = json.loads((d / "sentences.json").read_text(encoding="utf-8"))
errors = []
err = errors.append

section_ids = {s["id"] for s in meta["sections"]}
pos_ids, chunk_ids = set(meta["pos"]), set(meta["chunkTypes"])

# 単語
ws = [w["word"].lower() for w in words]
if ws != sorted(ws):
    err("words.json がアルファベット順になっていません")
word_by_id = {}
for w in words:
    if w["id"] in word_by_id:
        err(f"単語ID重複: {w['id']}")
    word_by_id[w["id"]] = w
    if w["section"] not in section_ids:
        err(f"{w['id']}: 未定義のsection {w['section']}")
    for i, sn in enumerate(w["senses"]):
        if sn["pos"] not in pos_ids:
            err(f"{w['id']} sense{i}: 未定義の品詞 {sn['pos']}")

# 重複チェック(単語・別綴り・番号)
seen={}
for w in words:
    for nm in [w["word"].lower(),*[x.lower() for x in w.get("alt",[])]]:
        if nm in seen:
            err(f"単語の重複: {nm} ({seen[nm]} と {w['id']})")
        seen[nm]=w["id"]
nos={}
for w in words:
    if "no" in w:
        if w["no"] in nos:
            err(f"番号の重複: {w['no']} ({nos[w['no']]} と {w['id']})")
        nos[w["no"]]=w["id"]

# 例文
sent_by_id = {}
for s in sents:
    sid = s["id"]
    if sid in sent_by_id:
        err(f"例文ID重複: {sid}")
    sent_by_id[sid] = s
    toks = s["tokens"]
    joined = re.sub(r"\s+([.,;:?!])", r"\1", " ".join(t["t"] for t in toks))
    if joined != s["text"]:
        err(f"{sid}: tokens連結とtextが不一致\n   tokens: {joined}\n   text:   {s['text']}")
    for t in toks:
        if t["pos"] not in pos_ids:
            err(f"{sid}: 未定義の品詞 {t['pos']} ({t['t']})")
    for c in s["chunks"]:
        if not (0 <= c["from"] <= c["to"] < len(toks)):
            err(f"{sid}: chunk範囲が不正 {c['from']}-{c['to']}")
        if c["type"] not in chunk_ids:
            err(f"{sid}: 未定義のchunk type {c['type']}")
    tg = s["target"]
    w = word_by_id.get(tg["wordId"])
    if not w:
        err(f"{sid}: target.wordId が存在しません")
        continue
    if not (0 <= tg["senseIndex"] < len(w["senses"])):
        err(f"{sid}: senseIndex が範囲外")
    surface = toks[tg["tokenIndex"]]["t"].lower()
    ok = {w["word"].lower(), *[a.lower() for a in w.get("alt", [])],
          *[v.lower() for v in w.get("forms", {}).values()]}
    if surface not in ok:
        err(f"{sid}: target の語 '{surface}' が {w['word']} の活用形にありません")

# 単語→例文の参照
for w in words:
    for i, sn in enumerate(w["senses"]):
        for sid in sn["sentences"]:
            if sid not in sent_by_id:
                err(f"{w['id']} sense{i}: 存在しない例文 {sid}")
            elif sent_by_id[sid]["target"]["wordId"] != w["id"] or sent_by_id[sid]["target"]["senseIndex"] != i:
                err(f"{w['id']} sense{i}: 例文 {sid} のtargetと一致しません")

if errors:
    print(f"NG: {len(errors)} 件")
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: 単語 {len(words)} 語 / 例文 {len(sents)} 文")
