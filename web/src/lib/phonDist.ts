/**
 * 音側の距離。**pipeline/phon.py の distance と同一の定義**(N-04)。
 * 変えるときは両方を同時に変え、gold/phon_cross.json を作り直して O-4 を通すこと。
 *
 * これは**音が似ているかであって、意味が似ているかではない**(F-32b)。
 */
import type { Phon } from "./data";

export const WEIGHTS: Record<string, number> = {
  onset1: 3.0, onset2: 2.0, vowels: 3.0, form: 2.0,
  voiced: 1.0, semivoiced: 1.0, geminate: 0.5, moraic_n: 0.5, long: 0.5,
};

export function distance(a: Phon, b: Phon): number {
  let total = 0;
  for (const [key, w] of Object.entries(WEIGHTS)) {
    const va = (a as unknown as Record<string, unknown>)[key];
    const vb = (b as unknown as Record<string, unknown>)[key];
    if (va === null || vb === null) {
      if (va !== vb) total += w;
    } else if (va !== vb) total += w;
  }
  return Math.round(total * 10000) / 10000;
}

export function nearest(word: string, phons: Record<string, Phon>, n = 8):
    { word: string; distance: number }[] {
  const self = phons[word];
  if (!self) return [];
  return Object.entries(phons)
    .filter(([w]) => w !== word)
    .map(([w, p]) => ({ word: w, distance: distance(self, p) }))
    .sort((x, y) => x.distance - y.distance || (x.word < y.word ? -1 : 1))
    .slice(0, n);
}
