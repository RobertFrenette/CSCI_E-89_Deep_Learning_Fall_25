import React from 'react'

import shield from './assets/shield.png'

const App: React.FC = () => {
  return (
    <div className="page">
      <header className="nav">
        <div className="nav-left">
          <img src={shield} className="brand-shield" alt="AI Agent Insure Logo" />
          <div className="brand-text">
            <span className="brand-name">AI Agent Insure</span>
            <span className="brand-tagline">Insurance for Agentic AI Builders</span>
          </div>
        </div>
        <nav className="nav-links">
          <a href="#products">Products</a>
          <a href="#why">Why now</a>
          <a href="#how-it-works">How it works</a>
          <a href="#contact">Talk to us</a>
        </nav>
      </header>

      <main>
        <section className="hero">
          <div className="hero-text">
            <h1>De-risk your agentic AI stack.</h1>
            <p>
              AI-native coverage for teams shipping autonomous agents, RAG systems, and AI-first products.
              Translate model, data, and workflow risk into clear, predictable insurance.
            </p>
            <div className="hero-actions">
              <a href="#contact" className="btn btn-primary">Request a coverage review</a>
              <a href="#products" className="btn btn-ghost">Explore products</a>
            </div>
            <div className="hero-meta">
              <span>✔ Built for RAG, agents & AVs</span>
              <span>✔ Designed with AI security & risk teams</span>
            </div>
          </div>
          <div className="hero-panel">
            <div className="panel-header">Live Agentic Risk Snapshot</div>
            <div className="panel-body">
              <div className="metric">
                <span className="metric-label">Agent workflows protected</span>
                <span className="metric-value">128+</span>
              </div>
              <div className="metric">
                <span className="metric-label">Average incident containment</span>
                <span className="metric-value">9 min</span>
              </div>
              <div className="metric">
                <span className="metric-label">AI-native products covered</span>
                <span className="metric-value">42</span>
              </div>
              <div className="metric metric-pill">
                <span className="dot" />
                Real-world coverage for RAG, multi-agent systems, AVs & robotics.
              </div>
            </div>
          </div>
        </section>

        <section id="products" className="section">
          <h2>Coverage designed for agentic AI systems</h2>
          <p className="section-intro">
            From hallucinating copilots to unsupervised multi-agent workflows, AI Agent Insure
            turns complex technical failure modes into clear, underwritten coverage.
          </p>

          <div className="card-grid">
            <article className="card">
              <h3>Agentic AI Liability</h3>
              <p>
                Covers downstream harm from autonomous or semi-autonomous AI decisions, including hallucinations,
                misaligned actions, and faulty recommendations.
              </p>
              <ul>
                <li>Customer-facing and internal agents</li>
                <li>RAG-based copilots and assistants</li>
                <li>Regulatory & reputational protection</li>
              </ul>
            </article>

            <article className="card">
              <h3>Autonomous Systems & Robotics</h3>
              <p>
                Purpose-built coverage for AVs, drones, warehouse robotics, and industrial automation controlled by AI.
              </p>
              <ul>
                <li>Navigation & perception failures</li>
                <li>Hardware–software integration issues</li>
                <li>Operational downtime add-ons</li>
              </ul>
            </article>

            <article className="card">
              <h3>Model, Data & Infra Security</h3>
              <p>
                Protects your AI stack: training data, embeddings, vector stores, model endpoints, and orchestration layers.
              </p>
              <ul>
                <li>Prompt injection & data poisoning</li>
                <li>Model exfiltration and endpoint abuse</li>
                <li>Vector DB & RAG corruption incidents</li>
              </ul>
            </article>
          </div>
        </section>

        <section id="why" className="section section-muted">
          <div className="two-column">
            <div>
              <h2>Why AI-native insurance now?</h2>
              <p>
                Traditional cyber and E&O products were not built for agentic systems that act, learn,
                and route tasks autonomously. As your AI surface area grows, blind spots multiply.
              </p>
              <p>
                AI Agent Insure translates failure modes your engineers and risk teams talk about every day
                into an underwriting language your board and regulators understand.
              </p>
            </div>
            <div className="list-block">
              <h3>Built around how you ship AI</h3>
              <ul>
                <li>Underwriting aligned to your RAG & agent architecture</li>
                <li>Coverage that evolves with new models and tools</li>
                <li>Support for internal, customer-facing, and partner-facing agents</li>
              </ul>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="section">
          <h2>How it works</h2>
          <div className="steps">
            <div className="step">
              <span className="step-index">01</span>
              <h3>Map your agentic risk surface</h3>
              <p>
                We work with your engineering, security, and legal teams to inventory models, data flows,
                agent workflows, and critical dependencies.
              </p>
            </div>
            <div className="step">
              <span className="step-index">02</span>
              <h3>Design coverage around your stack</h3>
              <p>
                We align policy structure to how your systems actually behave: RAG pipelines, tool-calling agents,
                autonomous vehicles, and multi-agent orchestrators.
              </p>
            </div>
            <div className="step">
              <span className="step-index">03</span>
              <h3>Deploy & iterate with you</h3>
              <p>
                As you ship new agents, swap models, or expand into new geos, we revisit limits, exclusions,
                and incident playbooks with your team.
              </p>
            </div>
          </div>
        </section>

        <section id="contact" className="section section-accent">
          <div className="contact-card">
            <h2>Ready to insure your next generation of AI agents?</h2>
            <p>
              Share a brief snapshot of your AI footprint — models, agents, and infrastructure — and our team
              will respond with a tailored coverage outline.
            </p>
            <form
              className="contact-form"
              onSubmit={(e) => {
                e.preventDefault()
                alert('This demo form does not submit. In production, connect it to your backend or CRM.')
              }}
            >
              <div className="form-row">
                <div className="field">
                  <label htmlFor="name">Name</label>
                  <input id="name" placeholder="Your name" required />
                </div>
                <div className="field">
                  <label htmlFor="company">Company</label>
                  <input id="company" placeholder="Your company" required />
                </div>
              </div>
              <div className="form-row">
                <div className="field">
                  <label htmlFor="email">Work email</label>
                  <input id="email" type="email" placeholder="you@company.com" required />
                </div>
                <div className="field">
                  <label htmlFor="role">Role</label>
                  <input id="role" placeholder="e.g. Head of AI, CTO, CISO" />
                </div>
              </div>
              <div className="field">
                <label htmlFor="footprint">AI footprint</label>
                <textarea
                  id="footprint"
                  rows={4}
                  placeholder="Share a quick overview: agent types, RAG use cases, AV/robotics, key regions..."
                />
              </div>
              <button type="submit" className="btn btn-primary btn-full">
                Get a coverage outline
              </button>
            </form>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>© {new Date().getFullYear()} AI Agent Insure. All rights reserved.</span>
        <span className="footer-meta">Fictional company — demo landing page for agentic AI insurance.</span>
      </footer>
    </div>
  )
}

export default App
