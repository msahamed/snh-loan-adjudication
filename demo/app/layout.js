import "./globals.css";

export const metadata = {
  title: "SNH AI Loan Decision Demo",
  description: "Hybrid LLM and deterministic loan adjudication walkthrough",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
