import Link from "next/link";
import { notFound } from "next/navigation";
import { CaseSidebar, DemoFooter, DemoHeader } from "../../components/demo-ui";
import { examples, getExample } from "../../lib/loan-demo";

export function generateStaticParams() {
  return examples.map((example) => ({ caseId: example.id }));
}

export default async function ApplicationFlow({ params }) {
  const { caseId } = await params;
  const example = getExample(caseId);
  if (!example) notFound();

  const captured = Object.values(example.application).filter((value) => value !== null && value !== undefined).length;

  return (
    <main className="application-shell">
      <DemoHeader activeStep="conversation" caseId={caseId} />

      <section className="conversation-layout">
        <CaseSidebar selectedId={caseId} />

        <article className="conversation-panel">
          <header className="conversation-head">
            <div>
              <p className="panel-label">Customer view</p>
              <h1>Loan application assistant</h1>
              <p>{example.title}</p>
            </div>
            <div className="capture-status">
              <span>{captured}/10</span>
              <small>fields captured</small>
            </div>
          </header>

          <div className="conversation-scroll">
            <div className="conversation-thread">
              <div className="chat-date">Sample conversation</div>
              {example.messages.map(([role, content], index) => (
                <div className={`message-row ${role}`} key={`${caseId}-${index}`}>
                  {role === "assistant" && <span className="avatar">S</span>}
                  <div className="message">{content}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="conversation-actionbar">
            <div>
              <span className="ready-dot" />
              <span>{captured === 10 ? "Conversation complete" : "Information still missing"}</span>
            </div>
            <Link className="primary-action decision-cta" href={`/decision-trace/${caseId}`}>
              See how this conversation becomes an adjudication decision
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </article>
      </section>

      <DemoFooter />
    </main>
  );
}
