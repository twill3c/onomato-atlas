"use client";
import { useMemo, useState } from "react";
import type { AxisMeta, Word } from "@/lib/data";
import { search, type Query } from "@/lib/filter";

const ONSETS: [string, string][] = [
  ["", "指定なし"], ["k", "か行 k"], ["g", "が行 g"], ["s", "さ行 s"], ["z", "ざ行 z"],
  ["t", "た行 t"], ["d", "だ行 d"], ["n", "な行 n"], ["h", "は行 h"], ["b", "ば行 b"],
  ["p", "ぱ行 p"], ["m", "ま行 m"], ["r", "ら行 r"], ["y", "や行 y"], ["w", "わ行 w"],
  ["", "—"],
];
const FORMS = ["", "ABAB", "ABり", "ABん", "ABっ", "ABっと", "ABー"];

export default function FindClient({ words, axes }:
  { words: Word[]; axes: AxisMeta[] }) {
  const [q, setQ] = useState<Query>({});
  const [use, setUse] = useState<Record<string, boolean>>({});

  const ranges = useMemo(() => {
    const r: Record<string, [number, number]> = {};
    for (const a of axes) if (use[a.id]) r[a.id] = q.ranges?.[a.id] ?? [0, a.sd * 3];
    return r;
  }, [q.ranges, use, axes]);

  const hits = useMemo(() => search(words, { ...q, ranges }), [words, q, ranges]);

  const set = (k: keyof Query, v: unknown) => setQ((p) => ({ ...p, [k]: v }));

  return (
    <>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.9rem 1.4rem",
                    margin: "1.2rem 0" }}>
        <label>表記に含む<br />
          <input type="text" value={q.text ?? ""} placeholder="ふわ"
                 onChange={(e) => set("text", e.target.value)}
                 style={{ padding: "0.3rem 0.5rem", width: "8rem" }} /></label>
        <label>語頭子音<br />
          <select value={q.onset1 ?? ""} onChange={(e) => set("onset1", e.target.value)}
                  style={{ padding: "0.3rem" }}>
            {ONSETS.filter((o) => o[1] !== "—").map(([v, l], i) => (
              <option key={i} value={v}>{l}</option>))}
          </select></label>
        <label>形<br />
          <select value={q.form ?? ""} onChange={(e) => set("form", e.target.value)}
                  style={{ padding: "0.3rem" }}>
            {FORMS.map((f) => <option key={f} value={f}>{f || "指定なし"}</option>)}
          </select></label>
        <label>濁音<br />
          <select value={q.voiced === undefined ? "" : String(q.voiced)}
                  onChange={(e) => set("voiced",
                    e.target.value === "" ? undefined : e.target.value === "true")}
                  style={{ padding: "0.3rem" }}>
            <option value="">指定なし</option>
            <option value="true">あり</option>
            <option value="false">なし</option>
          </select></label>
      </div>

      {axes.map((a) => (
        <div key={a.id} style={{ margin: "0.6rem 0" }}>
          <label>
            <input type="checkbox" checked={!!use[a.id]}
                   onChange={(e) => setUse((p) => ({ ...p, [a.id]: e.target.checked }))} />
            {" "}{a.name} の右寄り(スコア 0 以上)で絞る
            <span className="meta"> — {a.n_scored} 語にしか付いていません</span>
          </label>
        </div>
      ))}

      <p className="meta" style={{ marginTop: "1.2rem" }}>{hits.length} 語</p>
      <p style={{ lineHeight: 2.2 }}>
        {hits.slice(0, 200).map((w) => (
          <a key={w.word} href={`/o/${encodeURIComponent(w.word)}/`}
             style={{ marginRight: "1.1rem", whiteSpace: "nowrap" }}>
            {w.word}<span className="meta" style={{ fontSize: "0.75em" }}> {w.freq}</span>
          </a>
        ))}
      </p>
      {hits.length > 200 && <p className="meta">(先頭 200 語まで表示)</p>}
    </>
  );
}
