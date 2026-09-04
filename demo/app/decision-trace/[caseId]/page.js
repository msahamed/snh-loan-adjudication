import Link from "next/link";
import { notFound } from "next/navigation";
import { DecisionPill, DemoFooter, DemoHeader } from "../../components/demo-ui";
import {
  adjudicate,
  decisionMeta,
  examples,
  getExample,
  humanize,
  observedValue,
  ruleRequirement,
} from "../../lib/loan-demo";

const fields = [
  ["age", "Age"],
  ["credit_score", "Credit score"],
  ["annual_income_usd", "Annual income"],
  ["debt_to_income_ratio_percent", "Debt-to-income"],
  ["employment_status", "Employment"],
  ["current_employment_duration_months", "Employment duration"],
  ["residency_status", "Residency"],
  ["has_bankruptcy_recent", "Recent bankruptcy"],
  ["requested_amount_usd", "Requested amount"],
  ["has_verifiable_bank_account", "Verified bank account"],
];

function formatField(field, value) {
  if (value === null || value === undefined) return "Missing";
  if (["annual_income_usd", "requested_amount_usd"].includes(field)) return `$${value.toLocaleString()}`;
  if (field === "debt_to_income_ratio_percent") return `${value}%`;
  if (field === "current_employment_duration_months") return `${value} months`;
  return humanize(value);
}

export function generateStaticParams() {
  return examples.map((example) => ({ caseId: example.id }));
}

export default async function DecisionTrace({ params }) {
  const { caseId } = await params;
  const example = getExample(caseId);
  if (!example) notFound();

  const engine = adjudicate(example.application);
  const meta = decisionMeta[engine.decision];
  const decisionChanged = example.model.decision !== engine.decision;
  const citationsChanged = JSON.stringify(example.model.failed_rule_ids) !== JSON.stringify(engine.failed_rule_ids);
  const exceptions = engine.checks.filter((check) => check.passed !== true);
  const modelJson = JSON.stringify({ ...example.application, model_prediction: example.model }, null, 2);

  return (
    <main className="application-shell">
      <DemoHeader activeStep="decision" caseId={caseId} />

      <section className="decision-layout">
        <aside className="decision-summary">
          <p className="panel-label">Verified outcome</p>
          <DecisionPill decision={engine.decision} />
          <h1>{meta.route}</h1>
          <p>{example.description}</p>
          <dl>
            <div><dt>Model proposed</dt><dd>{decisionMeta[example.model.decision].label}</dd></div>
            <div><dt>Policy engine</dt><dd>{meta.label}</dd></div>
            <div><dt>Rules checked</dt><dd>{engine.checks.length}</dd></div>
            <div><dt>Exceptions</dt><dd>{exceptions.length}</dd></div>
          </dl>
          {(decisionChanged || citationsChanged) && (
            <div className="override-alert">
              <strong>{decisionChanged ? "Model decision corrected" : "Citations corrected"}</strong>
              <span>The customer receives only the verified result.</span>
            </div>
          )}
          <Link className="secondary-action trace-back" href={`/application-flow/${caseId}`}>← Back to conversation</Link>
        </aside>

        <div className="decision-scroll">
          <div className="decision-document">
            <div className="pipeline-strip" aria-label="Decision pipeline">
              <span>Customer dialogue</span><i>→</i>
              <span>Model output</span><i>→</i>
              <span>Policy verification</span><i>→</i>
              <span className="active">Final outcome</span>
            </div>

            <section className="audit-section">
              <div className="audit-heading">
                <span>01</span>
                <div><h2>Extracted application</h2><p>Structured values parsed from the conversation.</p></div>
                <Link className="learn-link" href={`/decision-trace/${caseId}/learn/extracted-application`}>Learn how this works →</Link>
              </div>
              <div className="field-grid">
                {fields.map(([field, label]) => (
                  <div className={example.application[field] === null ? "field-item missing-field" : "field-item"} key={field}>
                    <span>{label}</span><strong>{formatField(field, example.application[field])}</strong>
                  </div>
                ))}
              </div>
            </section>

            <section className="audit-section">
              <div className="audit-heading">
                <span>02</span>
                <div><h2>Model output</h2><p>Useful for interpretation, but not trusted as the final decision.</p></div>
                <Link className="learn-link" href={`/decision-trace/${caseId}/learn/model-output`}>Learn how this works →</Link>
              </div>
              <div className="shadow-output">
                <div className="shadow-row">
                  <div><span>Shadow decision</span><DecisionPill decision={example.model.decision} /></div>
                  <div><span>Proposed rule citations</span><strong>{example.model.failed_rule_ids.length ? example.model.failed_rule_ids.join(", ") : "None"}</strong></div>
                </div>
                <p>{example.model.explanation}</p>
                <details><summary>View complete model JSON</summary><pre>{modelJson}</pre></details>
              </div>
            </section>

            <section className="audit-section">
              <div className="audit-heading">
                <span>03</span>
                <div><h2>Deterministic verification</h2><p>The engine recalculates every active rule from the extracted values.</p></div>
                <Link className="learn-link" href={`/decision-trace/${caseId}/learn/deterministic-verification`}>Learn how this works →</Link>
              </div>
              <div className="verification-summary">
                <div><strong>{engine.checks.filter((check) => check.passed === true).length}</strong><span>Passed</span></div>
                <div><strong>{exceptions.length}</strong><span>Exceptions</span></div>
                <div><strong>{engine.failed_rule_ids.length}</strong><span>Final citations</span></div>
              </div>
              {exceptions.length > 0 ? (
                <div className="exception-list">
                  {exceptions.map((rule) => (
                    <div className="exception-row" key={rule.id}>
                      <div><strong>{rule.label}</strong><code>{rule.id}</code></div>
                      <span>{observedValue(rule, example.application)}</span>
                      <span>{rule.passed === null ? "Required value missing" : `Requires ${ruleRequirement(rule, example.application)}`}</span>
                      <b className={rule.passed === null ? "missing" : rule.action === "REJECT" ? "fail" : "review-tag"}>
                        {rule.passed === null ? "Missing" : rule.action === "REJECT" ? "Fail" : "Review"}
                      </b>
                    </div>
                  ))}
                </div>
              ) : <p className="all-clear">All 10 policy checks passed.</p>}

              <details className="all-rules">
                <summary>View all 10 policy checks</summary>
                <div className="rules-table">
                  <div className="rule-row rule-header"><span>Rule</span><span>Observed</span><span>Requirement</span><span>Result</span></div>
                  {engine.checks.map((rule) => (
                    <div className="rule-row" key={rule.id}>
                      <span><b>{rule.label}</b><small>{rule.id}</small></span>
                      <span>{observedValue(rule, example.application)}</span>
                      <span>{ruleRequirement(rule, example.application)}</span>
                      <span className={rule.passed === true ? "pass" : rule.passed === false ? rule.action === "REJECT" ? "fail" : "review-tag" : "missing"}>
                        {rule.passed === true ? "Pass" : rule.passed === false ? rule.action === "REJECT" ? "Fail" : "Review" : "Missing"}
                      </span>
                    </div>
                  ))}
                </div>
              </details>
            </section>

            <section className="audit-section final-response-section">
              <div className="audit-heading">
                <span>04</span>
                <div><h2>Customer response</h2><p>Generated only from the verified decision and rule citations.</p></div>
                <Link className="learn-link" href={`/decision-trace/${caseId}/learn/customer-response`}>Learn how this works →</Link>
              </div>
              <div className={`customer-response ${meta.tone}`}>
                <DecisionPill decision={engine.decision} />
                <h3>{meta.customer}</h3>
                {engine.decision !== "APPROVE" && <p>{engine.explanation}</p>}
                {engine.failed_rule_ids.length > 0 && <div className="citation-list">{engine.failed_rule_ids.map((id) => <code key={id}>{id}</code>)}</div>}
              </div>
            </section>
          </div>
        </div>
      </section>

      <DemoFooter />
    </main>
  );
}
