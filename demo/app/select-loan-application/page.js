import Link from "next/link";
import { DemoFooter, DemoHeader } from "../components/demo-ui";
import { examples } from "../lib/loan-demo";

export const metadata = { title: "Select a test application | SNH AI" };

export default function SelectLoanApplication() {
  return (
    <main className="application-shell">
      <DemoHeader activeStep="select" />

      <section className="selection-scroll">
        <div className="selection-page">
          <div className="selection-heading">
            <p className="recipient">Test cases</p>
            <h1>Choose an application to review</h1>
            <p>Each conversation tests a different decision path or failure mode.</p>
          </div>

          <div className="case-card-grid">
            {examples.map((example, index) => (
              <Link className="case-card" href={`/application-flow/${example.id}`} key={example.id}>
                <div className="case-card-top">
                  <span className={`scenario-dot ${example.accent}`} />
                  <span>Case {String(index + 1).padStart(2, "0")}</span>
                </div>
                <h2>{example.title}</h2>
                <p>{example.description}</p>
                <span className="case-card-link">Open conversation <span aria-hidden="true">→</span></span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <DemoFooter />
    </main>
  );
}
