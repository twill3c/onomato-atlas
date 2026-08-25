/**
 * 「探す」の絞り込み(F-33)。**クライアント完結**で、API を呼ばない。
 *
 * 絞れるのは、決定論的に得られる音側素性と、検定を通った軸のスコアだけ。
 * 意味の近さでは絞れない(語レベルの意味主張は再現しないため — F-32b)。
 */
import type { Word } from "./data";

export type Query = {
  onset1?: string;
  vowels?: string;
  form?: string;
  voiced?: boolean;
  ranges?: Record<string, [number, number]>;
  text?: string;
};

export function matches(w: Word, q: Query): boolean {
  if (q.onset1 !== undefined && q.onset1 !== "" && w.phon.onset1 !== q.onset1) return false;
  if (q.vowels !== undefined && q.vowels !== "" && w.phon.vowels !== q.vowels) return false;
  if (q.form !== undefined && q.form !== "" && w.phon.form !== q.form) return false;
  if (q.voiced !== undefined && w.phon.voiced !== q.voiced) return false;
  if (q.text) {
    const t = q.text.trim();
    if (t && !w.word.includes(t)) return false;
  }
  for (const [axis, [lo, hi]] of Object.entries(q.ranges ?? {})) {
    const v = w.axes[axis];
    if (v === undefined) return false;
    if (v < lo || v > hi) return false;
  }
  return true;
}

export function search(words: Word[], q: Query): Word[] {
  return words.filter((w) => matches(w, q)).sort((a, b) => b.freq - a.freq);
}
