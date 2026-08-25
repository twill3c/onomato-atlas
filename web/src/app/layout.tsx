import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "音象アトラス — 近代日本語オノマトペの音と意味",
  description:
    "青空文庫 2,200 作品から、オノマトペの音韻素性と用法分布を独立に測り、" +
    "両者が一致する範囲だけを地図にする。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        {children}
        <footer>
          <main style={{ padding: "0 1.25rem 3rem" }}>
            <p className="meta">
              音象アトラス — コード MIT / 自作データ CC BY 4.0 /
              引用本文は青空文庫(パブリックドメイン・底本表記つき)
            </p>
            <p className="meta">
              <a href="/method/">方法と限界</a>
            </p>
          </main>
        </footer>
      </body>
    </html>
  );
}
