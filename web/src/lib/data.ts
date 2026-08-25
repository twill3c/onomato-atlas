import fs from "node:fs";
import path from "node:path";

export type Phon = {
  word: string; stem: string; form: string;
  onset1: string | null; onset2: string | null; vowels: string | null;
  voiced: boolean | null; semivoiced: boolean | null;
  geminate: boolean | null; moraic_n: boolean | null; long: boolean | null;
};

export type Word = {
  word: string; id: number; freq: number; phon: Phon;
  axes: Record<string, number>; n_quotes: number;
};

export type AxisMeta = {
  id: string; name: string; source: string;
  density_floor: number | null; reliability: number | null;
  sd: number; sem: number | null;
  n_scored: number;
  stats: { n: number; same_direction?: number; mean_cos?: number;
           p_binomial: number; control_p_empirical: number; control_z_ratio?: number };
};

export type Paradigm = {
  axis: string; stem: string; variant: string;
  stem_score: number; variant_score: number; delta: number;
};

export type VoicedPair = {
  axis: string; plain: string; voiced: string;
  plain_score: number; voiced_score: number; delta: number;
};

export type Index = {
  generated_on: string;
  corpus: { works: number; chars: number; authors: number };
  axes: AxisMeta[];
  rejected_axes: { id: string; name: string; stats: AxisMeta["stats"] }[];
  words: Record<string, Word>;
  paradigms: Paradigm[];
  voiced_pairs: VoicedPair[];
};

const DATA = path.join(process.cwd(), "public", "data");

export function loadIndex(): Index {
  return JSON.parse(fs.readFileSync(path.join(DATA, "index.json"), "utf-8"));
}

export type AuthorTop = { word: string; z: number; delta: number;
                          count: number; author_total: number };
export type Author = { author: string; works: number; tokens: number; types: number;
                       top: AuthorTop[]; n_significant: number };
export type Authors = {
  generated_on: string; min_tokens: number; prior_strength: number;
  bonferroni_z: number; n_authors: number; authors: Record<string, Author>;
};

export function loadAuthors(): Authors {
  return JSON.parse(fs.readFileSync(path.join(DATA, "authors.json"), "utf-8"));
}

export type Quote = {
  quote: string; surface: string;
  source: { work_id: string; title: string; author: string;
            底本名: string; 入力者: string; 校正者: string };
};

export function loadQuotes(id: number): Quote[] {
  const p = path.join(DATA, "quotes", `${id}.json`);
  if (!fs.existsSync(p)) return [];
  return JSON.parse(fs.readFileSync(p, "utf-8")).quotes ?? [];
}

/** ルビ《…》と注記［＃…］を表示用の断片に分解する。原文は変更しない(N-05)。 */
export type Frag = { t: "text"; s: string } | { t: "ruby"; base: string; rt: string }
  | { t: "note"; s: string };

export function parseRuby(raw: string): Frag[] {
  const out: Frag[] = [];
  let buf = "";
  for (let i = 0; i < raw.length; ) {
    if (raw.startsWith("［＃", i)) {
      const j = raw.indexOf("］", i);
      if (j < 0) { buf += raw.slice(i); break; }
      if (buf) { out.push({ t: "text", s: buf }); buf = ""; }
      out.push({ t: "note", s: raw.slice(i + 2, j) });
      i = j + 1; continue;
    }
    if (raw[i] === "《") {
      const j = raw.indexOf("》", i);
      if (j < 0) { buf += raw.slice(i); break; }
      const rt = raw.slice(i + 1, j);
      let k = buf.length;
      const bar = buf.lastIndexOf("｜");
      if (bar >= 0) { k = bar; }
      else { while (k > 0 && /[一-鿿々ヶヵ]/.test(buf[k - 1])) k--; }
      const base = buf.slice(k).replace("｜", "");
      out.push({ t: "text", s: buf.slice(0, k).replace("｜", "") });
      out.push({ t: "ruby", base, rt });
      buf = ""; i = j + 1; continue;
    }
    buf += raw[i]; i++;
  }
  if (buf) out.push({ t: "text", s: buf.replace("｜", "") });
  return out.filter((f) => f.t !== "text" || f.s.length > 0);
}
