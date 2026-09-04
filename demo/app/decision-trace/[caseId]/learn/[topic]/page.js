import Link from "next/link";
import { notFound } from "next/navigation";
import { DemoFooter, DemoHeader } from "../../../../components/demo-ui";
import { adjudicate, decisionMeta, examples, getExample, projectLinks } from "../../../../lib/loan-demo";

const topics = {
  "extracted-application": {
    step: "Step 1",
    title: "How the conversation becomes application data",
    summary: "The fine-tuned model reads the full conversation and returns ten normalized application fields. Missing or unresolved values remain null.",
    why: "The rules engine needs the observed values to reproduce the decision independently. A model-generated decision or list of failed rules is not enough evidence.",
    resources: [
      { label: "Model responsibilities", note: "The extraction contract and its safety boundary.", href: `${projectLinks.github}/blob/main/docs/system-design.md#model-responsibilities` },
      { label: "Preprocessing design", note: "How records are validated and formatted for training.", href: `${projectLinks.github}/blob/main/docs/fine-tuning.md#preprocessing` },
      { label: "Preprocessing code", note: "The script that prepares training records.", href: `${projectLinks.github}/blob/main/scripts/prepare_training_data.py` },
    ],
  },
  "model-output": {
    step: "Step 2",
    title: "What the model produces",
    summary: "The model receives the active rules and customer dialogue. It returns the ten fields, a shadow decision, failed rule IDs, and a short explanation in one JSON object.",
    why: "The shadow result measures what the model learned and provides a disagreement signal. It is never sent directly to the customer as the final decision.",
    resources: [
      { label: "Fine-tuning approach", note: "Training setup and measured evaluation results.", href: `${projectLinks.github}/blob/main/docs/fine-tuning.md` },
      { label: "Training code", note: "The QLoRA training pipeline.", href: `${projectLinks.github}/blob/main/scripts/train_qlora.py` },
      { label: "Published model adapter", note: "The trained LoRA adapter on Hugging Face.", href: projectLinks.model },
    ],
  },
  "deterministic-verification": {
    step: "Step 3",
    title: "How the deterministic rules engine verifies the result",
    summary: "Code evaluates every active rule again using the extracted values. Rejection takes priority over human review, and missing information prevents a lending decision.",
    why: "This makes thresholds, rule citations, and decisions reproducible. A client can also update the rules file without retraining the model. The engine cannot repair an incorrectly extracted value, so unresolved evidence must be blocked earlier.",
    resources: [
      { label: "Rules-engine responsibilities", note: "Decision precedence, versioning, and audit behavior.", href: `${projectLinks.github}/blob/main/docs/system-design.md#rules-engine-responsibilities` },
      { label: "Active credit rules", note: "The JSON policy evaluated by the engine.", href: `${projectLinks.github}/blob/main/credit_rules.json` },
      { label: "Model and engine metrics", note: "Results reported separately for both layers.", href: `${projectLinks.github}/blob/main/docs/evaluation-metrics.md` },
    ],
  },
  "customer-response": {
    step: "Step 4",
    title: "How the customer response stays grounded",
    summary: "The response is built from the verified decision, observed values, and failed rules. Internal rule IDs remain in the audit record while the customer receives a plain-language reason.",
    why: "A fluent model explanation can still contain the wrong threshold or reason. Building the response from verified facts prevents a model citation from becoming the customer-facing explanation.",
    resources: [
      { label: "Explanation and citation design", note: "What the customer sees and what the audit retains.", href: `${projectLinks.github}/blob/main/docs/system-design.md#explanations-and-citations` },
      { label: "Representative outputs", note: "Examples comparing model and verified results.", href: `${projectLinks.github}/blob/main/docs/representative-outputs.md` },
      { label: "Why deterministic control matters", note: "Business and regulatory reasoning from the final report.", href: `${projectLinks.github}/blob/main/docs/final-report.md#why-deterministic-control-is-necessary-in-lending` },
    ],
  },
};

const topicOrder = Object.keys(topics);

const visualFields = [
  ["age", "Age"], ["credit_score", "Credit"], ["annual_income_usd", "Income"],
  ["debt_to_income_ratio_percent", "DTI"], ["employment_status", "Employment"],
  ["current_employment_duration_months", "Tenure"], ["residency_status", "Residency"],
  ["has_bankruptcy_recent", "Bankruptcy"], ["requested_amount_usd", "Amount"],
  ["has_verifiable_bank_account", "Bank account"],
];

function visualValue(field, value) {
  if (value === null || value === undefined) return "Missing";
  if (["annual_income_usd", "requested_amount_usd"].includes(field)) return `$${Math.round(value / 1000)}k`;
  if (field === "debt_to_income_ratio_percent") return `${value}%`;
  if (field === "current_employment_duration_months") return `${value} mo`;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value).replace("employed_", "").replaceAll("_", " ");
}

function shortLine(value, limit = 31) {
  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
}

function exampleCaption(topic, example, engine) {
  const missing = Object.values(example.application).filter((value) => value === null || value === undefined).length;
  const exceptions = engine.checks.filter((check) => check.passed !== true).length;
  if (topic === "extracted-application") return `${10 - missing}/10 fields captured from this conversation${missing ? ` · ${missing} unresolved` : ""}.`;
  if (topic === "model-output") return `The model proposed ${decisionMeta[example.model.decision].label.toLowerCase()} with ${example.model.failed_rule_ids.length} rule citation${example.model.failed_rule_ids.length === 1 ? "" : "s"}.`;
  if (topic === "deterministic-verification") return `The engine checked all 10 rules and found ${exceptions} exception${exceptions === 1 ? "" : "s"}: ${decisionMeta[engine.decision].label}.`;
  return `The customer receives the verified ${decisionMeta[engine.decision].label.toLowerCase()} result; the audit keeps ${engine.failed_rule_ids.length} rule citation${engine.failed_rule_ids.length === 1 ? "" : "s"}.`;
}

function resultClass(check) {
  if (check.passed === true) return "viz-pass";
  if (check.passed === null || check.action === "FLAG_REVIEW") return "viz-review";
  return "viz-fail";
}

function StepVisualization({ topic, example, engine }) {
  if (topic === "extracted-application") {
    return (
      <svg className="system-illustration" viewBox="0 0 920 300" role="img" aria-labelledby="extract-title extract-desc">
        <title id="extract-title">Conversation field extraction</title>
        <desc id="extract-desc">Customer messages converge on a field extractor and become ten typed application values.</desc>
        <path className="viz-route" d="M226 70 C290 70 286 128 330 138" />
        <path className="viz-route" d="M255 145 C294 145 298 148 330 148" />
        <path className="viz-route" d="M218 220 C286 220 286 170 330 158" />
        <g className="dialogue-mark assistant-mark">
          <path d="M28 36 H200 Q216 36 216 52 V80 Q216 96 200 96 H62 L44 110 V96 H28 Q12 96 12 80 V52 Q12 36 28 36 Z" />
          <text x="34" y="61">How much would you</text><text x="34" y="79">like to borrow?</text>
        </g>
        <g className="dialogue-mark user-mark">
          <path d="M70 120 H235 Q251 120 251 136 V157 Q251 173 235 173 H218 V187 L200 173 H70 Q54 173 54 157 V136 Q54 120 70 120 Z" />
          <text x="78" y="151">{shortLine(example.messages[1]?.[1] || "Loan amount provided")}</text>
        </g>
        <g className="dialogue-mark user-mark">
          <path d="M28 200 H192 Q208 200 208 216 V238 Q208 254 192 254 H62 L44 268 V254 H28 Q12 254 12 238 V216 Q12 200 28 200 Z" />
          <text x="34" y="231">{shortLine(example.messages[3]?.[1] || "More details provided")}</text>
        </g>
        <g className="extractor-core">
          <circle cx="395" cy="150" r="66" />
          <circle cx="395" cy="150" r="49" />
          <path d="M370 133 H420 M370 150 H420 M370 167 H405" />
          <text x="395" y="115" textAnchor="middle">LANGUAGE</text>
          <text x="395" y="199" textAnchor="middle">TO FIELDS</text>
        </g>
        <path className="viz-route output-route" d="M461 150 C500 150 494 62 535 62 M461 150 C500 150 494 238 535 238" />
        <line className="field-spine" x1="535" y1="48" x2="535" y2="252" />
        {visualFields.map(([field, label], index) => {
          const column = index < 5 ? 0 : 1;
          const row = index % 5;
          const x = 560 + column * 180;
          const y = 62 + row * 44;
          const value = example.application[field];
          const missing = value === null || value === undefined;
          return (
            <g className={missing ? "field-signal missing-signal" : "field-signal"} key={label}>
              <line x1={column ? 715 : 535} y1={y} x2={x - 12} y2={y} />
              <circle cx={x} cy={y} r="5" />
              <text x={x + 13} y={y - 2}>{label}</text>
              <text className="field-value" x={x + 13} y={y + 13}>{visualValue(field, value)}</text>
            </g>
          );
        })}
        <text className="viz-caption" x="12" y="290">Unstructured conversation</text>
        <text className="viz-caption" x="350" y="290">Normalization</text>
        <text className="viz-caption" x="720" y="290">Typed schema</text>
      </svg>
    );
  }

  if (topic === "model-output") {
    return (
      <svg className="system-illustration" viewBox="0 0 920 300" role="img" aria-labelledby="model-title model-desc">
        <title id="model-title">Fine-tuned model inference</title>
        <desc id="model-desc">The rules and dialogue enter the fine-tuned model and leave as constrained JSON with an untrusted shadow decision.</desc>
        <g className="input-stream rules-stream">
          <path d="M24 42 H214 L238 66 V130 H24 Z" />
          <path d="M214 42 V66 H238" />
          <text x="48" y="75">ACTIVE RULES</text>
          <line x1="48" y1="91" x2="190" y2="91" /><line x1="48" y1="105" x2="168" y2="105" />
        </g>
        <g className="input-stream dialogue-stream">
          <path d="M24 168 H238 V248 H58 L40 264 V248 H24 Z" />
          <text x="48" y="200">CUSTOMER DIALOGUE</text>
          <circle cx="52" cy="221" r="4" /><line x1="65" y1="221" x2="190" y2="221" />
          <circle cx="52" cy="237" r="4" /><line x1="65" y1="237" x2="167" y2="237" />
        </g>
        <path className="viz-route" d="M238 95 C300 95 297 126 336 134 M238 210 C300 210 297 174 336 164" />
        <g className="model-core">
          <circle cx="425" cy="150" r="91" />
          <circle cx="425" cy="150" r="68" />
          <circle cx="425" cy="150" r="45" />
          <circle cx="389" cy="112" r="5" /><circle cx="467" cy="124" r="5" /><circle cx="401" cy="184" r="5" /><circle cx="458" cy="180" r="5" />
          <path d="M389 112 L467 124 L458 180 L401 184 Z M389 112 L401 184 M467 124 L401 184" />
          <text x="425" y="145" textAnchor="middle">QWEN3</text><text x="425" y="162" textAnchor="middle">1.7B + LoRA</text>
        </g>
        <path className="viz-route output-route" d="M516 150 C557 150 560 150 592 150" />
        <g className="json-output">
          <path d="M610 34 C584 34 584 66 584 86 V122 C584 141 571 150 557 150 C571 150 584 159 584 178 V214 C584 234 584 266 610 266" />
          <path d="M884 34 C910 34 910 66 910 86 V122 C910 141 923 150 937 150 C923 150 910 159 910 178 V214 C910 234 910 266 884 266" transform="translate(-34 0)" />
          <text x="628" y="72">10 normalized fields</text>
          <text x="628" y="112">decision: {example.model.decision}</text>
          <text x="628" y="152">failed_rule_ids: {example.model.failed_rule_ids.length}</text>
          <text x="628" y="192">short explanation</text>
          <text className="shadow-label" x="628" y="232">SHADOW OUTPUT ONLY</text>
        </g>
      </svg>
    );
  }

  if (topic === "deterministic-verification") {
    return (
      <svg className="system-illustration" viewBox="0 0 920 300" role="img" aria-labelledby="rules-title rules-desc">
        <title id="rules-title">Deterministic rule verification</title>
        <desc id="rules-desc">Ten configured rules evaluate the extracted fields, then decision precedence produces the verified outcome.</desc>
        <text className="viz-kicker" x="22" y="27">ACTIVE RULESET · 10 CHECKS</text>
        <line className="rule-bus" x1="172" y1="44" x2="172" y2="268" />
        {engine.checks.map((check, index) => {
          const y = 51 + index * 23;
          return (
            <g className={`rule-signal ${resultClass(check)}`} key={check.id}>
              <text x="22" y={y + 4}>{check.label}</text>
              <line x1="172" y1={y} x2="560" y2={y} />
              <circle cx="224" cy={y} r="5" />
              <circle cx="340" cy={y} r="5" />
              <circle cx="456" cy={y} r="5" />
              <path d={`M560 ${y} C598 ${y} 596 150 630 150`} />
            </g>
          );
        })}
        <g className="priority-gate">
          <path d="M630 78 H742 L712 150 L742 222 H630 L660 150 Z" />
          <text x="686" y="116" textAnchor="middle">DECISION</text>
          <text x="686" y="135" textAnchor="middle">PRIORITY</text>
          <text x="686" y="165" textAnchor="middle">REJECT</text>
          <text x="686" y="182" textAnchor="middle">REVIEW</text>
          <text x="686" y="199" textAnchor="middle">APPROVE</text>
        </g>
        <path className="viz-route output-route" d="M742 150 H790" />
        <g className={`verified-orbit ${decisionMeta[engine.decision].tone}`}>
          <circle cx="846" cy="150" r="52" />
          <circle cx="846" cy="150" r="40" />
          <text x="846" y="144" textAnchor="middle">VERIFIED</text>
          <text x="846" y="165" textAnchor="middle">{decisionMeta[engine.decision].label.toUpperCase()}</text>
        </g>
      </svg>
    );
  }

  return (
    <svg className="system-illustration" viewBox="0 0 920 300" role="img" aria-labelledby="response-title response-desc">
      <title id="response-title">Verified customer response construction</title>
      <desc id="response-desc">The verified decision and rule evidence pass through a citation gate before a customer explanation and audit record are created.</desc>
      <g className={`decision-source ${decisionMeta[engine.decision].tone}`}>
        <circle cx="105" cy="150" r="64" /><circle cx="105" cy="150" r="49" />
        <text x="105" y="138" textAnchor="middle">RULES</text><text x="105" y="158" textAnchor="middle">DECISION</text>
        <text x="105" y="181" textAnchor="middle">{decisionMeta[engine.decision].label.toUpperCase()}</text>
      </g>
      <path className="viz-route" d="M169 132 C226 132 228 102 278 102 M169 168 C226 168 228 198 278 198" />
      <g className="evidence-lines">
        <line x1="278" y1="82" x2="420" y2="82" /><circle cx="292" cy="82" r="5" />
        <text x="310" y="87">Observed value</text>
        <line x1="278" y1="124" x2="420" y2="124" /><circle cx="292" cy="124" r="5" />
        <text x="310" y="129">Policy threshold</text>
        <line x1="278" y1="176" x2="420" y2="176" /><circle cx="292" cy="176" r="5" />
        <text x="310" y="181">Verified rule ID</text>
        <line x1="278" y1="218" x2="420" y2="218" /><circle cx="292" cy="218" r="5" />
        <text x="310" y="223">Ruleset version</text>
      </g>
      <g className="citation-gate">
        <path d="M480 68 L550 94 V151 C550 200 521 226 480 244 C439 226 410 200 410 151 V94 Z" />
        <path d="M451 151 L471 171 L512 128" />
        <text x="480" y="113" textAnchor="middle">CITATION</text>
        <text x="480" y="129" textAnchor="middle">CHECK</text>
      </g>
      <path className="viz-route output-route" d="M550 150 C592 150 594 150 628 150" />
      <g className="customer-message-mark">
        <path d="M648 62 H886 Q904 62 904 80 V204 Q904 222 886 222 H718 L690 244 V222 H648 Q630 222 630 204 V80 Q630 62 648 62 Z" />
        <text x="658" y="94">CUSTOMER RESPONSE</text>
        <line x1="658" y1="116" x2="860" y2="116" /><line x1="658" y1="136" x2="842" y2="136" />
        <line x1="658" y1="156" x2="870" y2="156" /><line x1="658" y1="176" x2="816" y2="176" />
        <text x="658" y="204">Plain language · verified facts</text>
      </g>
      <path className="audit-trail" d="M480 244 V274 H816" />
      <text className="viz-caption" x="650" y="289">Audit record keeps the technical evidence</text>
    </svg>
  );
}

export function generateStaticParams() {
  return examples.flatMap((example) => topicOrder.map((topic) => ({ caseId: example.id, topic })));
}

export default async function LearnDecisionStep({ params }) {
  const { caseId, topic } = await params;
  const example = getExample(caseId);
  const content = topics[topic];
  if (!example || !content) notFound();
  const engine = adjudicate(example.application);

  const topicIndex = topicOrder.indexOf(topic);
  const previous = topicOrder[topicIndex - 1];
  const next = topicOrder[topicIndex + 1];

  return (
    <main className="application-shell">
      <DemoHeader activeStep="decision" caseId={caseId} />

      <div className="learn-scroll">
        <article className="learn-page">
          <Link className="learn-back" href={`/decision-trace/${caseId}`}>← Back to decision trace</Link>

          <header className="learn-heading">
            <p className="recipient">{content.step} · {example.title}</p>
            <h1>{content.title}</h1>
            <p>{content.summary}</p>
          </header>

          <section className="system-visual-wrap">
            <StepVisualization topic={topic} example={example} engine={engine} />
            <div className="visual-example"><span>This application</span><strong>{exampleCaption(topic, example, engine)}</strong></div>
          </section>

          {topic === "extracted-application" && (
            <section className="learn-json" aria-labelledby="extraction-json-title">
              <div>
                <p className="panel-label">Actual output</p>
                <h2 id="extraction-json-title">Structured application JSON</h2>
                <p>This flat object passes directly to schema validation and the deterministic rules engine.</p>
              </div>
              <pre><code>{JSON.stringify(example.application, null, 2)}</code></pre>
            </section>
          )}

          {topic === "model-output" && (
            <section className="learn-json" aria-labelledby="model-json-title">
              <div>
                <p className="panel-label">Actual output</p>
                <h2 id="model-json-title">Complete model JSON</h2>
                <p>The decision, citations, and explanation remain shadow outputs until the rules engine verifies them.</p>
              </div>
              <pre><code>{JSON.stringify({ ...example.application, ...example.model }, null, 2)}</code></pre>
            </section>
          )}

          {topic === "deterministic-verification" && (
            <section className="learn-json" aria-labelledby="rules-json-title">
              <div>
                <p className="panel-label">Actual output</p>
                <h2 id="rules-json-title">Rules-engine verification JSON</h2>
                <p>This auditable result replaces the model’s shadow decision and citations.</p>
              </div>
              <pre><code>{JSON.stringify({
                ruleset_version: "1.0",
                rules_evaluated: engine.checks.length,
                decision: engine.decision,
                failed_rule_ids: engine.failed_rule_ids,
                explanation: engine.explanation,
                rule_results: engine.checks.map((check) => ({
                  rule_id: check.id,
                  field: check.field,
                  observed_value: example.application[check.field],
                  operator: check.operator,
                  configured_value: check.expected,
                  action_on_fail: check.action,
                  passed: check.passed,
                })),
              }, null, 2)}</code></pre>
            </section>
          )}

          <section className="learn-explanation">
            <div>
              <p className="panel-label">Why this step exists</p>
              <h2>The practical reason</h2>
            </div>
            <p>{content.why}</p>
          </section>

          <section className="resource-section">
            <div className="resource-heading">
              <p className="panel-label">Project references</p>
              <h2>Read the implementation</h2>
            </div>
            <div className="resource-card-list">
              {content.resources.map((resource) => (
                <a href={resource.href} target="_blank" rel="noreferrer" className="resource-card" key={resource.label}>
                  <span><strong>{resource.label}</strong><small>{resource.note}</small></span>
                  <span aria-hidden="true">↗</span>
                </a>
              ))}
            </div>
          </section>

          <nav className="learn-pagination" aria-label="Learning pages">
            {previous ? <Link href={`/decision-trace/${caseId}/learn/${previous}`}>← Previous step</Link> : <span />}
            {next ? <Link href={`/decision-trace/${caseId}/learn/${next}`}>Next step →</Link> : <Link href={`/decision-trace/${caseId}`}>Return to trace →</Link>}
          </nav>
        </article>
      </div>

      <DemoFooter />
    </main>
  );
}
