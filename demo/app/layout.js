import localFont from "next/font/local";
import "./globals.css";

const hanken = localFont({
  src: [{ path: "./fonts/HankenGrotesk-Variable.woff2", style: "normal" }],
  variable: "--font-hanken",
  display: "swap",
  fallback: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
});

export const metadata = {
  title: "SNH AI Loan Decision Demo",
  description: "Hybrid LLM and deterministic loan adjudication walkthrough",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={hanken.variable}>
      <body>{children}</body>
    </html>
  );
}
