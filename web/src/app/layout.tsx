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
        <footer className="site-footer">
          <p className="meta">
            音象アトラス — 自作データ CC BY 4.0 /
            引用本文は青空文庫(パブリックドメイン・底本表記つき) ・{" "}
            <a href="/method/">方法と限界</a>
          </p>
          <p className="meta">
            <a
              href="https://github.com/twill3c/onomato-atlas/blob/main/LICENSE"
              target="_blank"
              rel="noopener"
            >
              MIT License
            </a>{" "}
            © 2026 坂田哲朗 ・{" "}
            <a href="https://github.com/twill3c/onomato-atlas" target="_blank" rel="noopener">
              GitHub
            </a>{" "}
            ・{" "}
            <a
              href="https://claude.ai/code/artifact/e5f3ef35-95c6-440c-9574-970206449c41"
              target="_blank"
              rel="noopener"
            >
              音象アトラスの歩き方
            </a>{" "}
            ・{" "}
            <a
              href="https://claude.ai/code/artifact/90b68bcb-2a86-4235-ab99-18618f3447b5"
              target="_blank"
              rel="noopener"
            >
              音象アトラス設計図
            </a>{" "}
            ・{" "}
            <a href="https://app-menu-amber.vercel.app" target="_blank" rel="noopener">
              App Menu
            </a>
          </p>
        </footer>
      </body>
    </html>
  );
}
