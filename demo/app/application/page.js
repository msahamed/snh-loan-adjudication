"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

const rules = [
  { id: "RULE-AGE-001", field: "age", label: "Age", operator: ">=", expected: 18, action: "REJECT" },
  { id: "RULE-CREDIT-001", field: "credit_score", label: "Credit score", operator: ">=", expected: 670, action: "REJECT" },
  { id: "RULE-INCOME-001", field: "annual_income_usd", label: "Annual income", operator: ">=", expected: 30000, action: "REJECT" },
  { id: "RULE-DTI-001", field: "debt_to_income_ratio_percent", label: "Debt-to-income", operator: "<=", expected: 40, action: "REJECT" },
  { id: "RULE-EMPLOY-001", field: "employment_status", label: "Employment", operator: "in", expected: ["employed_full_time", "employed_part_time", "self_employed", "retired"], action: "REJECT" },
  { id: "RULE-EMPLOY-002", field: "current_employment_duration_months", label: "Employment duration", operator: ">=", expected: 6, action: "FLAG_REVIEW" },
  { id: "RULE-RESIDENCY-001", field: "residency_status", label: "Residency", operator: "in", expected: ["US_Citizen", "Permanent_Resident"], action: "REJECT" },
  { id: "RULE-BANKRUPTCY-001", field: "has_bankruptcy_recent", label: "Recent bankruptcy", operator: "is", expected: false, action: "REJECT" },
  { id: "RULE-LOANAMT-001", field: "requested_amount_usd", label: "Loan-to-income", operator: "income ×", expected: 0.5, action: "FLAG_REVIEW" },
  { id: "RULE-BANKACCTS-001", field: "has_verifiable_bank_account", label: "Bank account", operator: "is", expected: true, action: "REJECT" },
];

const examples = [
  {
    id: "approve",
    short: "Accept",
    title: "Clean approval",
    description: "All reported values satisfy the active policy.",
    accent: "green",
    application: {
      age: 34,
      credit_score: 742,
      annual_income_usd: 84000,
      debt_to_income_ratio_percent: 24,
      employment_status: "employed_full_time",
      current_employment_duration_months: 36,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 20000,
      has_verifiable_bank_account: true,
    },
    model: {
      decision: "APPROVE",
      failed_rule_ids: [],
      explanation: "The application meets the current requirements.",
    },
    messages: [
      ["assistant", "Hi, I can help with your personal-loan application. How much would you like to borrow?"],
      ["user", "I need $20,000 for home repairs."],
      ["assistant", "Thanks. Please tell me your age, annual income, and current credit score."],
      ["user", "I’m 34, earn $84,000 a year, and my score is 742."],
      ["assistant", "What is your debt-to-income ratio and current employment situation?"],
      ["user", "My DTI is 24%. I’ve worked full-time in this role for three years."],
      ["assistant", "Last check: residency, recent bankruptcy, and an active bank account?"],
      ["user", "U.S. citizen, no bankruptcy in seven years, and yes, my account is active."],
    ],
  },
  {
    id: "reject",
    short: "Corrected reject",
    title: "Model error caught",
    description: "The model approves, but verified income is below policy.",
    accent: "red",
    application: {
      age: 68,
      credit_score: 712,
      annual_income_usd: 29500,
      debt_to_income_ratio_percent: 19,
      employment_status: "retired",
      current_employment_duration_months: 46,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 14000,
      has_verifiable_bank_account: true,
    },
    model: {
      decision: "APPROVE",
      failed_rule_ids: [],
      explanation: "The application meets the current requirements.",
    },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$14,000."],
      ["assistant", "Please share your age, annual income, and credit score."],
      ["user", "I’m 68, retired, make $29,500 a year, and my score is 712."],
      ["assistant", "How long have you had this income, and what is your DTI?"],
      ["user", "Forty-six months. My DTI is 19%."],
      ["assistant", "Do you meet the residency, bankruptcy, and bank-account requirements?"],
      ["user", "I’m a U.S. citizen, no recent bankruptcy, and I have an active bank account."],
    ],
  },
  {
    id: "review",
    short: "Escalate",
    title: "Human review",
    description: "Two review rules fail; no automatic rejection applies.",
    accent: "amber",
    application: {
      age: 29,
      credit_score: 710,
      annual_income_usd: 68000,
      debt_to_income_ratio_percent: 31,
      employment_status: "employed_full_time",
      current_employment_duration_months: 3,
      residency_status: "Permanent_Resident",
      has_bankruptcy_recent: false,
      requested_amount_usd: 50000,
      has_verifiable_bank_account: true,
    },
    model: {
      decision: "REVIEW",
      failed_rule_ids: ["RULE-EMPLOY-002"],
      explanation: "The current employment period is below the required minimum.",
    },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$50,000 to consolidate debt."],
      ["assistant", "Please share your age, income, credit score, and DTI."],
      ["user", "I’m 29, earn $68,000, my score is 710, and DTI is 31%."],
      ["assistant", "Tell me about your employment and residency."],
      ["user", "Full-time for three months. I’m a permanent resident."],
      ["assistant", "Any recent bankruptcy, and do you have an active bank account?"],
      ["user", "No recent bankruptcy. Yes, I have an active account."],
    ],
  },
  {
    id: "collect",
    short: "Need information",
    title: "Incomplete application",
    description: "Age is unresolved, so no lending decision is made.",
    accent: "blue",
    application: {
      age: null,
      credit_score: 695,
      annual_income_usd: 62000,
      debt_to_income_ratio_percent: 29,
      employment_status: "employed_full_time",
      current_employment_duration_months: 12,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 20000,
      has_verifiable_bank_account: true,
    },
    model: {
      decision: "COLLECTING_INFORMATION",
      failed_rule_ids: [],
      explanation: "More information is needed for: age.",
    },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$20,000."],
      ["assistant", "Please share your age, annual income, and credit score."],
      ["user", "I’d rather not say my age yet. I earn $62,000 and my score is 695."],
      ["assistant", "I can continue collecting information, but I cannot assess eligibility without your age."],
    ],
  },
];

function passesRule(rule, application) {
  const actual = application[rule.field];
  if (actual === null || actual === undefined) return null;
  if (rule.operator === ">=") return actual >= rule.expected;
  if (rule.operator === "<=") return actual <= rule.expected;
  if (rule.operator === "in") return rule.expected.includes(actual);
  if (rule.operator === "is") return actual === rule.expected;
  if (rule.operator === "income ×") return actual <= application.annual_income_usd * rule.expected;
  return false;
}

function ruleRequirement(rule, application) {
  if (rule.operator === "income ×") {
    return `≤ $${(application.annual_income_usd * rule.expected).toLocaleString()}`;
  }
  if (Array.isArray(rule.expected)) return rule.expected.map(humanize).join(" or ");
  if (typeof rule.expected === "boolean") return rule.expected ? "Yes" : "No";
  if (rule.field === "annual_income_usd") return `≥ $${rule.expected.toLocaleString()}`;
  if (rule.field === "debt_to_income_ratio_percent") return `≤ ${rule.expected}%`;
  return `${rule.operator} ${rule.expected}`;
}

function humanize(value) {
  if (value === null || value === undefined) return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function observedValue(rule, application) {
  const value = application[rule.field];
  if (value === null || value === undefined) return "Missing";
  if (["annual_income_usd", "requested_amount_usd"].includes(rule.field)) return `$${value.toLocaleString()}`;
  if (rule.field === "debt_to_income_ratio_percent") return `${value}%`;
  if (rule.field === "current_employment_duration_months") return `${value} months`;
  return humanize(value);
}

function explanationFor(rule, application) {
  const actual = application[rule.field];
  const explanations = {
    "RULE-AGE-001": `The applicant is ${actual}. The minimum age is 18.`,
    "RULE-CREDIT-001": `The reported credit score is ${actual}. The minimum is 670.`,
    "RULE-INCOME-001": `The reported annual income is $${actual.toLocaleString()}. The minimum is $30,000.`,
    "RULE-DTI-001": `The reported debt-to-income ratio is ${actual}%. The maximum is 40%.`,
    "RULE-EMPLOY-001": "The reported employment status does not meet the current requirement.",
    "RULE-EMPLOY-002": `The reported employment duration is ${actual} months. At least 6 months is required.`,
    "RULE-RESIDENCY-001": "The reported residency status does not meet the current requirement.",
    "RULE-BANKRUPTCY-001": "A bankruptcy was reported within the configured lookback period.",
    "RULE-LOANAMT-001": `The requested amount is $${actual.toLocaleString()}. The maximum for the reported income is $${(application.annual_income_usd * 0.5).toLocaleString()}.`,
    "RULE-BANKACCTS-001": "An active, verifiable bank account was not confirmed.",
  };
  return explanations[rule.id];
}

function adjudicate(application) {
  const checks = rules.map((rule) => ({ ...rule, passed: passesRule(rule, application) }));
  const missing = checks.filter((check) => check.passed === null);
  if (missing.length) {
    return {
      decision: "COLLECTING_INFORMATION",
      failed_rule_ids: [],
      explanation: `More information is needed for: ${missing.map((item) => item.label.toLowerCase()).join(", ")}.`,
      checks,
    };
  }
  const failed = checks.filter((check) => check.passed === false);
  const decision = failed.some((item) => item.action === "REJECT")
    ? "REJECT"
    : failed.some((item) => item.action === "FLAG_REVIEW")
      ? "REVIEW"
      : "APPROVE";
  return {
    decision,
    failed_rule_ids: failed.map((item) => item.id),
    explanation: failed.length
      ? failed.map((item) => explanationFor(item, application)).join(" ")
      : "Based on the information provided, the application meets the current requirements.",
    checks,
  };
}

const decisionMeta = {
  APPROVE: { label: "Accept", route: "Straight-through approval", tone: "green", customer: "Your application meets the current requirements." },
  REJECT: { label: "Reject", route: "Decline with verified reason", tone: "red", customer: "We’re unable to approve this application based on the current requirements." },
  REVIEW: { label: "Escalate", route: "Human credit review", tone: "amber", customer: "Your application needs a specialist review before we can make a final decision." },
  COLLECTING_INFORMATION: { label: "Continue", route: "Return to chatbot", tone: "blue", customer: "I need a little more information before assessing your application." },
};

const projectLinks = {
  github: "https://github.com/msahamed/snh-loan-adjudication",
  model: "https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora",
  dataset: "https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic",
};

function DecisionPill({ decision }) {
  const meta = decisionMeta[decision];
  return <span className={`decision-pill ${meta.tone}`}>{meta.label}</span>;
}

function StepHeader({ number, title, state, children }) {
  return (
    <div className="step-heading">
      <span className={`step-marker ${state >= number ? "complete" : ""}`} />
      <div>
        <p>{title}</p>
        {children && <span>{children}</span>}
      </div>
    </div>
  );
}

function AppHeader() {
  return (
    <header className="topbar">
      <Link className="brand" href="/" aria-label="Return to introduction">
        <span className="brand-mark">S</span>
        <span className="brand-copy">
          <strong>SNH AI</strong>
          <span>Loan decision lab</span>
        </span>
      </Link>
      <div className="header-status">
        <span className="live-dot" />
        <span>Simulated inference</span>
        <span className="divider" />
        <span className="ruleset">Ruleset v1.0</span>
      </div>
    </header>
  );
}

export default function Application() {
  const [selectedId, setSelectedId] = useState("reject");
  const [stage, setStage] = useState(0);
  const timers = useRef([]);
  const example = examples.find((item) => item.id === selectedId);
  const engine = useMemo(() => adjudicate(example.application), [example]);
  const meta = decisionMeta[engine.decision];
  const decisionDisagrees = example.model.decision !== engine.decision;
  const citationDisagrees = JSON.stringify(example.model.failed_rule_ids) !== JSON.stringify(engine.failed_rule_ids);
  const disagrees = decisionDisagrees || citationDisagrees;

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  function chooseExample(id) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setSelectedId(id);
    setStage(0);
  }

  function runAssessment() {
    timers.current.forEach(clearTimeout);
    setStage(1);
    timers.current = [
      setTimeout(() => setStage(2), 550),
      setTimeout(() => setStage(3), 1150),
      setTimeout(() => setStage(4), 1750),
    ];
  }

  const modelJson = JSON.stringify({ ...example.application, ...example.model }, null, 2);

  return (
    <main className="application-shell">
      <AppHeader />

      <section className={`workspace ${stage === 0 ? "pre-assessment" : "processing"}`}>
        <aside className="case-sidebar">
          <div className="sidebar-head">
            <p className="panel-label">Test conversations</p>
            <h2>Applications</h2>
          </div>
          <nav className="case-list" aria-label="Sample applications">
            {examples.map((item) => (
              <button
                type="button"
                key={item.id}
                className={selectedId === item.id ? "case-item active" : "case-item"}
                aria-current={selectedId === item.id ? "true" : undefined}
                onClick={() => chooseExample(item.id)}
              >
                <span className={`scenario-dot ${item.accent}`} />
                <span>
                  <b>{item.short}</b>
                  <small>{item.title}</small>
                </span>
              </button>
            ))}
          </nav>
          <div className="sidebar-note">
            <span>Selected case</span>
            <p>{example.description}</p>
          </div>
        </aside>

        <article className="chat-panel">
          <div className="panel-head">
            <div>
              <p className="panel-label">Customer view</p>
              <h2>Application assistant</h2>
            </div>
            <span className="secure-label">Secure session</span>
          </div>

          <div className="chat-body">
            <div className="chat-date">Today</div>
            {example.messages.map(([role, content], index) => (
              <div className={`message-row ${role}`} key={`${selectedId}-${index}`}>
                {role === "assistant" && <span className="avatar">S</span>}
                <div className="message">{content}</div>
              </div>
            ))}
            {stage === 4 && (
              <div className="customer-result">
                <div className={`result-icon ${meta.tone}`}>{engine.decision === "APPROVE" ? "✓" : engine.decision === "REJECT" ? "×" : "→"}</div>
                <div>
                  <span>Application update</span>
                  <strong>{meta.customer}</strong>
                  {["REJECT", "COLLECTING_INFORMATION"].includes(engine.decision) && <p>{engine.explanation}</p>}
                </div>
              </div>
            )}
          </div>

          <div className="chat-composer">
            <input aria-label="Message" disabled value={stage === 4 ? "Assessment complete" : "Example conversation complete"} readOnly />
            <button type="button" onClick={runAssessment} disabled={stage > 0 && stage < 4}>
              {stage > 0 && stage < 4 ? "Processing…" : stage === 4 ? "Process again" : "Process application"}
            </button>
          </div>
        </article>

        <article className="trace-panel" aria-live="polite">
          <div className="panel-head trace-head">
            <div>
              <p className="panel-label">Internal view</p>
              <h2>Decision trace</h2>
            </div>
            <span className="case-id">CASE · {example.id.toUpperCase()}-001</span>
          </div>

          <div className="trace-body">
            <section className={`trace-step ${stage >= 1 ? "visible" : "muted"}`}>
              <StepHeader number={1} title="Application received" state={stage}>10-field schema parsed · 10 rules loaded</StepHeader>
              {stage >= 1 && (
                <div className="input-summary">
                  <div><span>Requested</span><b>${example.application.requested_amount_usd.toLocaleString()}</b></div>
                  <div><span>Income</span><b>${example.application.annual_income_usd.toLocaleString()}</b></div>
                  <div><span>Credit</span><b>{example.application.credit_score}</b></div>
                  <div><span>Missing</span><b>{Object.values(example.application).filter((value) => value === null).length}</b></div>
                </div>
              )}
            </section>

            <section className={`trace-step ${stage >= 2 ? "visible" : "muted"}`}>
              <StepHeader number={2} title="Model interpretation" state={stage}>Qwen3-1.7B LoRA · shadow output</StepHeader>
              {stage >= 2 && (
                <div className="model-box">
                  <div className="box-bar"><DecisionPill decision={example.model.decision} /><span>Valid JSON</span></div>
                  <div className="model-summary">
                    <span>Proposed citations</span>
                    <strong>{example.model.failed_rule_ids.length ? example.model.failed_rule_ids.join(", ") : "None"}</strong>
                    <p>{example.model.explanation}</p>
                  </div>
                  <details>
                    <summary>View complete model JSON</summary>
                    <pre>{modelJson}</pre>
                  </details>
                </div>
              )}
            </section>

            <section className={`trace-step ${stage >= 3 ? "visible" : "muted"}`}>
              <StepHeader number={3} title="Policy verification" state={stage}>Every rule recalculated from extracted fields</StepHeader>
              {stage >= 3 && (
                <div className="rules-table">
                  <div className="rule-row rule-header"><span>Rule</span><span>Observed</span><span>Requirement</span><span>Result</span></div>
                  {engine.checks.map((rule) => (
                    <div className="rule-row" key={rule.id}>
                      <span><b>{rule.label}</b><small>{rule.id}</small></span>
                      <span>{observedValue(rule, example.application)}</span>
                      <span>{ruleRequirement(rule, example.application)}</span>
                      <span className={rule.passed === true ? "pass" : rule.passed === false ? "fail" : "missing"}>
                        {rule.passed === true ? "Pass" : rule.passed === false ? rule.action === "REJECT" ? "Fail" : "Review" : "Missing"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className={`trace-step final-step ${stage >= 4 ? "visible" : "muted"}`}>
              <StepHeader number={4} title="Customer outcome" state={stage}>Verified decision, citations, and customer reason</StepHeader>
              {stage >= 4 && (
                <div className={`final-card ${meta.tone}`}>
                  <div className="final-top">
                    <div>
                      <span>Final route</span>
                      <h3>{meta.route}</h3>
                    </div>
                    <DecisionPill decision={engine.decision} />
                  </div>
                  {disagrees && (
                    <div className="correction-note">
                      <b>{decisionDisagrees ? "Decision overridden" : "Citation set corrected"}</b>
                      <span>{decisionDisagrees ? `${example.model.decision} → ${engine.decision} · ` : ""}{engine.failed_rule_ids.length} verified rule {engine.failed_rule_ids.length === 1 ? "failure" : "failures"}</span>
                    </div>
                  )}
                  <p>{engine.explanation}</p>
                  {engine.failed_rule_ids.length > 0 && (
                    <div className="citation-list">
                      {engine.failed_rule_ids.map((id) => <code key={id}>{id}</code>)}
                    </div>
                  )}
                </div>
              )}
            </section>

            {stage === 0 && (
              <div className="empty-trace">
                <p>Run the assessment to watch the decision move through each layer.</p>
                <small>{example.description}</small>
              </div>
            )}
          </div>
        </article>
      </section>

      <footer>
        <span>Demo uses representative simulated outputs</span>
        <a href={projectLinks.github} target="_blank" rel="noreferrer">Source and report on GitHub</a>
      </footer>
    </main>
  );
}
