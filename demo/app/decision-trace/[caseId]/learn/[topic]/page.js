import Link from "next/link";
import { notFound } from "next/navigation";
import { DemoFooter, DemoHeader } from "../../../../components/demo-ui";
import { examples, getExample, projectLinks } from "../../../../lib/loan-demo";

const topics = {
  "extracted-application": {
    step: "Step 1",
    title: "How the conversation becomes application data",
    summary: "The fine-tuned model reads the full conversation and returns ten normalized application fields. Missing or unresolved values remain null.",
    why: "The rules engine needs the observed values to reproduce the decision independently. A model-generated decision or list of failed rules is not enough evidence.",
    nodes: [
      { title: "Customer dialogue", lines: ["Natural language", "Corrections and omissions"] },
      { title: "Field extraction", lines: ["Qwen3-1.7B LoRA", "Normalize ten values"] },
      { title: "Schema validation", lines: ["Types and allowed values", "Null stays unresolved"] },
    ],
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
    nodes: [
      { title: "Rules + dialogue", lines: ["Current policy", "Full conversation"] },
      { title: "1.7B model", lines: ["LoRA adapter", "Constrained JSON"] },
      { title: "Shadow output", lines: ["Fields and decision", "Rule IDs and reason"] },
    ],
    resources: [
      { label: "Fine-tuning approach", note: "Training setup and measured evaluation results.", href: `${projectLinks.github}/blob/main/docs/fine-tuning.md` },
      { label: "Training code", note: "The QLoRA training pipeline.", href: `${projectLinks.github}/blob/main/scripts/train_qlora.py` },
      { label: "Published model adapter", note: "The trained LoRA adapter on Hugging Face.", href: projectLinks.model },
    ],
  },
  "deterministic-verification": {
    step: "Step 3",
    title: "How the policy engine verifies the result",
    summary: "Code evaluates every active rule again using the extracted values. Rejection takes priority over human review, and missing information prevents a lending decision.",
    why: "This makes thresholds, rule citations, and decisions reproducible. A client can also update the rules file without retraining the model. The engine cannot repair an incorrectly extracted value, so unresolved evidence must be blocked earlier.",
    nodes: [
      { title: "Extracted fields", lines: ["Observed values", "Missing-value state"] },
      { title: "Configured rules", lines: ["Ten checks", "Actions on failure"] },
      { title: "Decision priority", lines: ["Rejected → review", "Approved if all pass"] },
      { title: "Verified result", lines: ["Decision", "Exact rule IDs"] },
    ],
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
    nodes: [
      { title: "Verified decision", lines: ["Authoritative outcome", "Policy version"] },
      { title: "Verified reasons", lines: ["Observed value", "Required value"] },
      { title: "Response template", lines: ["Plain language", "No invented facts"] },
      { title: "Customer + audit", lines: ["Clear explanation", "Internal rule record"] },
    ],
    resources: [
      { label: "Explanation and citation design", note: "What the customer sees and what the audit retains.", href: `${projectLinks.github}/blob/main/docs/system-design.md#explanations-and-citations` },
      { label: "Representative outputs", note: "Examples comparing model and verified results.", href: `${projectLinks.github}/blob/main/docs/representative-outputs.md` },
      { label: "Why deterministic control matters", note: "Business and regulatory reasoning from the final report.", href: `${projectLinks.github}/blob/main/docs/final-report.md#why-deterministic-control-is-necessary-in-lending` },
    ],
  },
};

const topicOrder = Object.keys(topics);

export function generateStaticParams() {
  return examples.flatMap((example) => topicOrder.map((topic) => ({ caseId: example.id, topic })));
}

export default async function LearnDecisionStep({ params }) {
  const { caseId, topic } = await params;
  const example = getExample(caseId);
  const content = topics[topic];
  if (!example || !content) notFound();

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

          <section className="concept-visual" aria-label={`${content.title} process`}>
            {content.nodes.map((node, index) => (
              <div className="concept-node-group" key={node.title}>
                <div className="concept-node">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{node.title}</strong>
                  {node.lines.map((line) => <small key={line}>{line}</small>)}
                </div>
                {index < content.nodes.length - 1 && <span className="concept-arrow" aria-hidden="true">→</span>}
              </div>
            ))}
          </section>

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
