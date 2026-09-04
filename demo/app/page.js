import Link from "next/link";

const projectLinks = {
  github: "https://github.com/msahamed/snh-loan-adjudication",
  model: "https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora",
  dataset: "https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic",
};

export default function Home() {
  return (
    <main>
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

      <section className="welcome">
        <div className="welcome-copy">
          <p className="recipient">A note for Shams</p>
          <h1>Hi Shams, thanks for the opportunity to work through this exercise.</h1>
          <p>
            I built this walkthrough to show how a customer conversation becomes a loan decision. Choose a sample application, follow the dialogue, then see how the model and deterministic rules engine produce the final customer response.
          </p>
          <p>The report, source code, trained adapter, and synthetic dataset are linked below.</p>
          <div className="welcome-actions">
            <Link className="primary-action" href="/application-flow/approve">Begin walkthrough</Link>
            <a className="secondary-action" href={projectLinks.github} target="_blank" rel="noreferrer">View GitHub</a>
          </div>
          <nav className="resource-links" aria-label="Project resources">
            <a href={`${projectLinks.github}/blob/main/final-report.pdf`} target="_blank" rel="noreferrer">Final report</a>
            <a href={projectLinks.model} target="_blank" rel="noreferrer">Model adapter</a>
            <a href={projectLinks.dataset} target="_blank" rel="noreferrer">Dataset</a>
          </nav>
        </div>
      </section>

      <footer>
        <span>Technical exercise prepared for SNH AI</span>
        <span>Final decisions come from the rules engine</span>
      </footer>
    </main>
  );
}
