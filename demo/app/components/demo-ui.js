import Link from "next/link";
import { adjudicate, decisionMeta, examples } from "../lib/loan-demo";

const steps = [
  { id: "conversation", label: "Customer dialogue" },
  { id: "decision", label: "Decision trace" },
];

export function DemoHeader({ activeStep, caseId }) {
  const hrefFor = (step) => {
    if (!caseId) return "/application-flow/approve";
    return step === "conversation" ? `/application-flow/${caseId}` : `/decision-trace/${caseId}`;
  };

  return (
    <header className="journey-header">
      <Link className="brand" href="/" aria-label="Return to introduction">
        <span className="brand-mark">S</span>
        <span className="brand-copy">
          <strong>SNH AI</strong>
          <span>Loan decision lab</span>
        </span>
      </Link>

      <nav className="journey-steps" aria-label="Walkthrough progress">
        {steps.map((step, index) => (
          <Link
            key={step.id}
            href={hrefFor(step.id)}
            className={activeStep === step.id ? "journey-step active" : "journey-step"}
            aria-current={activeStep === step.id ? "step" : undefined}
          >
            <span>{index + 1}</span>
            {step.label}
          </Link>
        ))}
      </nav>

      <div className="header-status">
        <span className="live-dot" />
        <span>Ruleset v1.0</span>
      </div>
    </header>
  );
}

export function CaseSidebar({ selectedId }) {
  return (
    <aside className="case-sidebar fixed-case-sidebar">
      <div className="sidebar-head">
        <p className="panel-label">Test conversations</p>
        <h2>Applications</h2>
      </div>
      <nav className="case-list" aria-label="Sample applications">
        {examples.map((item, index) => (
          <Link
            key={item.id}
            href={`/application-flow/${item.id}`}
            className={selectedId === item.id ? "case-item active" : "case-item"}
            aria-current={selectedId === item.id ? "page" : undefined}
          >
            <span className={`scenario-dot ${item.accent}`} />
            <span>
              <b>Application-{index + 1}</b>
              <small>Status: {decisionMeta[adjudicate(item.application).decision].label}</small>
            </span>
          </Link>
        ))}
      </nav>
      <Link className="sidebar-back" href="/">Back to introduction</Link>
    </aside>
  );
}

export function DecisionPill({ decision }) {
  const meta = decisionMeta[decision];
  return <span className={`decision-pill ${meta.tone}`}>{meta.label}</span>;
}

export function DemoFooter() {
  return (
    <footer>
      <span>Representative simulated outputs</span>
      <span>Final decisions come from the rules engine</span>
    </footer>
  );
}
