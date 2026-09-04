import Link from "next/link";
import { decisionMeta, examples } from "../lib/loan-demo";

const steps = [
  { id: "select", label: "Select case" },
  { id: "conversation", label: "Customer dialogue" },
  { id: "decision", label: "Decision trace" },
];

export function DemoHeader({ activeStep, caseId }) {
  const hrefFor = (step) => {
    if (step === "select") return "/select-loan-application";
    if (!caseId) return "/select-loan-application";
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
        {examples.map((item) => (
          <Link
            key={item.id}
            href={`/application-flow/${item.id}`}
            className={selectedId === item.id ? "case-item active" : "case-item"}
            aria-current={selectedId === item.id ? "page" : undefined}
          >
            <span className={`scenario-dot ${item.accent}`} />
            <span>
              <b>{item.short}</b>
              <small>{item.title}</small>
            </span>
          </Link>
        ))}
      </nav>
      <Link className="sidebar-back" href="/select-loan-application">Choose from overview</Link>
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
      <span>Final decisions come from the policy engine</span>
    </footer>
  );
}
