import { describe, it, expect } from "vitest";
import { matches, search } from "../filter";
import type { Word } from "../data";

const mk = (word: string, onset1: string, vowels: string, form: string,
            voiced: boolean, freq: number, axes: Record<string, number> = {}): Word => ({
  word, id: 0, freq, n_quotes: 1, axes,
  phon: { word, stem: word.slice(0, 2), form, onset1, onset2: "r", vowels,
          voiced, semivoiced: false, geminate: false, moraic_n: false, long: false },
});

const WORDS = [
  mk("きらきら", "k", "ia", "ABAB", false, 413, { duration: -0.26 }),
  mk("ぎらぎら", "g", "ia", "ABAB", true, 242, { duration: -0.20 }),
  mk("ころり", "k", "oo", "ABり", false, 30, { duration: 0.31 }),
];

describe("探すの絞り込み", () => {
  it("語頭子音で絞れる", () => {
    expect(search(WORDS, { onset1: "g" }).map((w) => w.word)).toEqual(["ぎらぎら"]);
  });

  it("濁音の有無で絞れる", () => {
    expect(search(WORDS, { voiced: false }).length).toBe(2);
  });

  it("形態で絞れる", () => {
    expect(search(WORDS, { form: "ABり" }).map((w) => w.word)).toEqual(["ころり"]);
  });

  it("軸の範囲で絞れる", () => {
    const got = search(WORDS, { ranges: { duration: [0, 1] } });
    expect(got.map((w) => w.word)).toEqual(["ころり"]);
  });

  it("軸スコアを持たない語は範囲指定で落ちる", () => {
    const noScore = mk("ぬめぬめ", "n", "ue", "ABAB", false, 10);
    expect(matches(noScore, { ranges: { duration: [-1, 1] } })).toBe(false);
  });

  it("条件が無ければ全件を頻度順で返す", () => {
    expect(search(WORDS, {}).map((w) => w.freq)).toEqual([413, 242, 30]);
  });

  it("表記の部分一致で絞れる", () => {
    expect(search(WORDS, { text: "きら" }).map((w) => w.word)).toEqual(["きらきら"]);
  });
});
