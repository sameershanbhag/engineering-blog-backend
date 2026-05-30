"""Seed the database with the demo dataset (mirrors the frontend mock data)."""

from sqlmodel import Session, select

from .database import engine
from .models import Article, Author, Discipline

DISCIPLINES = [
    ("robotics", "Robotics", "Design, construction, operation, and use of robots and computer systems for control and sensory feedback.", "bot"),
    ("sustainability", "Sustainability", "Developing solutions that preserve natural resources and reduce the environmental footprint of engineering.", "leaf"),
    ("materials-science", "Materials Science", "Discovery and design of new solid materials for advanced and demanding applications.", "atom"),
    ("software", "Software", "Systematic application of engineering approaches to the development of resilient software systems.", "code"),
    ("hardware", "Hardware", "Physical components of technology systems and the boards, chips, and circuits that power them.", "cpu"),
    ("civil-systems", "Civil Systems", "Design and construction of infrastructure, bridges, and the systems that keep cities moving.", "building-2"),
    ("mechanical", "Mechanical", "Analysis, design, manufacturing, and maintenance of mechanical systems and machinery.", "cog"),
    ("electrical", "Electrical", "Study and application of electricity, electronics, and electromagnetism in modern systems.", "zap"),
]

AUTHORS = [
    dict(handle="aris_thorne", name="Dr. Aris Thorne", title="Staff Distributed Systems Engineer",
         bio="Specializing in high-throughput message queues and Byzantine fault tolerance. Ex-Cloudflare, current architecture lead at DataStream. Author of “Concurrency in Practice: Modern Patterns.”",
         avatar_url="https://i.pravatar.cc/160?img=12", avatar_color="bg-indigo-600", github="github.com/aristhorne",
         engagements=14200, followers=3100, following=143),
    dict(handle="sarah_jenkins", name="Sarah Jenkins", title="Principal Engineer, Data Infrastructure",
         bio="Building reliable streaming platforms at scale. Kafka contributor and event-driven architecture advocate.",
         avatar_url="https://i.pravatar.cc/160?img=5", avatar_color="bg-emerald-600", github="github.com/sjenkins",
         engagements=9800, followers=2400, following=210),
    dict(handle="david_chen", name="David Chen", title="Staff Software Engineer",
         bio="Systems programmer focused on compiler performance and developer tooling. Rust enthusiast.",
         avatar_url="https://i.pravatar.cc/160?img=13", avatar_color="bg-cyan-700", github="github.com/dchen",
         engagements=7600, followers=1800, following=96),
    dict(handle="elena_rodriguez", name="Elena Rodriguez", title="Principal Engineer, Data Infrastructure",
         bio="Distributed databases, consensus protocols, and the occasional foray into formal verification.",
         avatar_url="https://i.pravatar.cc/160?img=9", avatar_color="bg-violet-600", github=None,
         engagements=11300, followers=2900, following=120),
    dict(handle="marcus_johnson", name="Marcus Johnson", title="Staff Software Engineer",
         bio="Backend reliability, observability, and the art of the postmortem.",
         avatar_url=None, avatar_color="bg-slate-700", github=None,
         engagements=6400, followers=1500, following=88),
]

ARTICLES = [
    dict(slug="architecting-for-resilience",
         title="Architecting for Resilience: A Deep Dive into Distributed Systems",
         excerpt="Building scalable systems is rarely about chasing the latest technology. It is about navigating a series of complex trade-offs in latency, consistency, and the inevitability of partial failure.",
         content_html="""
      <p>Building scalable systems is rarely about chasing the latest technology. It is about navigating a series of complex trade-offs. When we talk about resilience, we are really asking a single question: <em>what happens when a part of the system fails?</em></p>
      <h2>The Fallacy of the Perfect Network</h2>
      <p>One of the classic distributed computing fallacies is assuming that the network is reliable. When services communicate over a network, failure is not a possibility, it is a statistical certainty.</p>
      <pre><code>async function processOrder(order) {
  const payment = await paymentGateway.charge(order);
  if (!payment.ok) return { status: "failed" };
  await inventory.reserve(order.items);
  return { status: "confirmed", id: order.id };
}</code></pre>
      <h2>Implementing the Circuit Breaker Pattern</h2>
      <p>The circuit breaker pattern wraps a fragile call in an object that monitors for failures. Once failures cross a threshold, the breaker trips and calls fail fast.</p>
      <blockquote>This provides a crucial "fail fast" mechanism, allowing the struggling downstream service to recover rather than overwhelming it with retry storms.</blockquote>
      <p>The result is a system that degrades gracefully under load instead of collapsing entirely.</p>
    """,
         discipline_slug="software", category="Software Architecture", author_handle="aris_thorne",
         published_at="2024-10-24", reading_minutes=12, likes=1200,
         cover_icon="server", cover_tone="dark", cover_image_url="https://picsum.photos/seed/resilience/640/420",
         tags=["distributed-systems", "resilience", "system-design"]),
    dict(slug="event-driven-microservices",
         title="Event-Driven Microservices: Managing Eventual Consistency at Scale",
         excerpt="When migrating to an event-driven architecture, eventual consistency becomes the default state. We explore practical patterns using Kafka and transactional outboxes to ensure data integrity across bounded contexts.",
         content_html="""
      <p>When migrating to an event-driven architecture, eventual consistency becomes the default state rather than the exception.</p>
      <h2>The Transactional Outbox</h2>
      <p>The transactional outbox pattern writes the event to an outbox table within the same database transaction as the state change.</p>
      <pre><code>BEGIN;
  INSERT INTO orders (id, status) VALUES ($1, 'created');
  INSERT INTO outbox (topic, payload) VALUES ('orders', $2);
COMMIT;</code></pre>
      <p>A relay process then publishes to Kafka, guaranteeing at-least-once delivery without distributed transactions.</p>
    """,
         discipline_slug="software", category="Software Architecture", author_handle="sarah_jenkins",
         published_at="2024-10-24", reading_minutes=12, likes=980,
         cover_icon="network", cover_tone="dark", cover_image_url="https://picsum.photos/seed/eventdriven/640/420",
         tags=["kafka", "microservices", "event-sourcing"]),
    dict(slug="optimizing-rust-compiler-performance",
         title="Optimizing Rust Compiler Performance in Large Workspaces",
         excerpt="Long compile times in massive Rust projects can severely impact developer velocity. This article details a systematic approach to profiling build times, utilizing cargo-llvm-lines and restructuring crates.",
         content_html="""
      <p>Long compile times in massive Rust projects can severely impact developer velocity.</p>
      <h2>Measure First</h2>
      <p>Before restructuring anything, capture a timing baseline with <code>cargo build --timings</code>.</p>
      <pre><code>$ cargo build --timings
$ cargo llvm-lines --bin app | head -20</code></pre>
      <p>Generic-heavy crates often generate enormous amounts of monomorphized code; splitting them along trait boundaries reduces codegen time.</p>
    """,
         discipline_slug="software", category="Systems Engineering", author_handle="david_chen",
         published_at="2024-10-22", reading_minutes=8, likes=760,
         cover_icon="terminal", cover_tone="dark", cover_image_url="https://picsum.photos/seed/rustcompiler/640/420",
         tags=["rust", "compilers", "performance"]),
    dict(slug="raft-log-replication",
         title="Optimizing Raft Log Replication for High-Latency Networks",
         excerpt="A deep dive into reducing tail latency in geographically distributed clusters. We explore pipelining techniques and optimistic append operations.",
         content_html="""
      <p>A deep dive into reducing tail latency in geographically distributed clusters.</p>
      <h2>Pipelining AppendEntries</h2>
      <p>Vanilla Raft waits for each AppendEntries round-trip before sending the next. Over a 150ms link, that serialization destroys throughput.</p>
    """,
         discipline_slug="software", category="Distributed Systems", author_handle="aris_thorne",
         published_at="2024-10-12", reading_minutes=18, likes=1200,
         cover_icon="git-branch", cover_tone="indigo", cover_image_url="https://picsum.photos/seed/raftlog/640/420",
         tags=["raft", "consensus", "distributed-systems"]),
    dict(slug="go-122-garbage-collector",
         title="Anatomy of the Go 1.22 Garbage Collector",
         excerpt="Breaking down the recent pacer improvements and memory arena changes. The article relies heavily on trace analysis to demonstrate how the new heuristics affect large-heap microservices.",
         content_html="""
      <p>Breaking down the recent pacer improvements and memory arena changes.</p>
      <h2>The Pacer's New Heuristics</h2>
      <p>The GC pacer decides when to start a collection cycle. Go 1.22 refines its model to reduce overshoot on rapidly growing heaps.</p>
    """,
         discipline_slug="software", category="Runtime Internals", author_handle="aris_thorne",
         published_at="2024-09-18", reading_minutes=14, likes=800,
         cover_icon="recycle", cover_tone="emerald", cover_image_url="https://picsum.photos/seed/gogc/640/420",
         tags=["go", "garbage-collection", "performance"]),
    dict(slug="robust-event-sourcing",
         title="Beyond CRUD: Implementing Robust Event Sourcing in Financial Systems",
         excerpt="Transitioning from state-based to event-based persistence requires a fundamental shift in how we model business domains. In this comprehensive guide, we examine the practical challenges of implementing CQRS and Event Sourcing using Apache Kafka.",
         content_html="""
      <p>Transitioning from state-based to event-based persistence requires a fundamental shift in how we model business domains.</p>
      <h2>Modeling Events</h2>
      <pre><code>type Event struct {
    ID        UUID
    Type      string
    Payload   []byte
    Timestamp time.Time
}</code></pre>
      <p>Events are immutable facts. The current state is a left-fold over the event stream.</p>
    """,
         discipline_slug="software", category="Data Engineering", author_handle="aris_thorne",
         published_at="2024-08-05", reading_minutes=12, likes=1100,
         cover_icon="database", cover_tone="dark", cover_image_url=None,
         tags=["event-sourcing", "cqrs", "kafka"]),
]


def seed() -> None:
    with Session(engine) as session:
        if session.exec(select(Discipline)).first():
            return  # already seeded

        for slug, name, desc, icon in DISCIPLINES:
            session.add(Discipline(slug=slug, name=name, description=desc, icon=icon))
        for a in AUTHORS:
            session.add(Author(**a))
        # Flush (not commit) so the parents exist for FK checks (Postgres enforces
        # them), while keeping a single atomic commit: if any article insert fails,
        # the whole seed rolls back rather than leaving a permanent partial state.
        session.flush()

        for art in ARTICLES:
            session.add(Article(**art, created_at=art["published_at"]))
        session.commit()
