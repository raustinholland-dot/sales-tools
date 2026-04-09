# Wiki Schema Generation Prompt

Give this entire prompt to Claude Opus to generate the schema document for your LLM knowledge base.

---

## Step 1: Analyze the Current Environment

Before designing anything, read and understand the following files. These represent the current system, its strengths, and its limitations. The schema you generate should be grounded in this reality — not in theory.

**Current system architecture (read these):**
- `system-context.md` — Telegram channel architecture, environment, feed processing rules
- `johnny-rebuild-2026-04-06.md` — The current pipeline architecture, what works, what breaks
- `meta-harness.md` — Skill evolution system, artifact capture, weekly improvement loop

**Current knowledge structure (read these):**
- `clearwater/knowledge/index.md` — Current master navigation (deals, projects, people, knowledge docs)
- `clearwater/knowledge/hot.md` — Current priorities cache
- 3-4 deal-state files from `clearwater/deals/` — See how deal knowledge is currently structured

**The user's actual communication style (read these):**
- Messages Austin sent in the Email Feed channel from the audit files in `audits/` — These are his ACTUAL sent emails. Study his voice, structure, tone, and patterns.
- `Gemini Gem Description and Instructions.txt` — A proven analysis tool Austin uses. Study its 5-phase process and the outputs it produces. This is the kind of analysis the query layer should support.

**How Austin actually works (read his DM messages from the audit):**
- Look at what Austin asks Johnny for in `audits/audit-2026-04-08.json` — the Johnny DM channel messages from Austin. These show his real workflow: what he needs, how he asks for it, what frustrates him, what he iterates on.

Understand all of this before generating the schema. The schema should make Austin's actual workflow dramatically simpler and more powerful — not impose a new workflow on top of it.

## Step 2: Design the Schema

Now generate a complete schema document based on what you've learned and the requirements below.

### What This System Is

A personal knowledge base for a B2B sales executive at a cybersecurity, compliance, and risk management company serving healthcare organizations. The user manages a $12-16M pipeline against a $4.5M quota, working 25-30 active deals simultaneously alongside outreach campaigns, internal projects, colleague relationships, competitive intelligence, and professional development.

This is NOT just a deal tracker. It captures everything the user encounters in their professional life — deal intelligence, people dynamics, market knowledge, internal operations, methodology insights, strategic patterns. The wiki is the user's institutional memory.

### How Information Flows In

Raw inputs arrive through 4 channels and are captured verbatim in daily log files (`raw/YYYY-MM-DD.md`):

- **Email threads** — inbound and outbound. Often multi-message threads with signatures and forwarded context.
- **Teams messages** — internal chat with colleagues. Quick exchanges about deals, pricing, strategy.
- **Call transcripts** — voice-to-text from sales calls, discovery meetings, internal 1:1s, pipeline reviews. Multi-speaker, often messy. Some cover multiple topics in one conversation.
- **Calendar events** — meeting confirmations, reschedules, invitations with attendees and agendas.

Currently these are manually forwarded by the user. In the near future, they will flow automatically via Microsoft Graph API, which will significantly increase volume and make batch compilation even more important.

Each raw input is timestamped, tagged with its channel, and stored verbatim. The compiler reads these and extracts knowledge into the wiki.

### Core Principles

1. **The wiki stores knowledge. Methodology is applied at the query layer.** No sales methodology, scoring framework, or analytical process should be embedded into the article structure. The wiki captures what happened, who was involved, what it means, and how it connects. Scoring, formatting for Salesforce, drafting emails — these are analysis functions that READ from the wiki.

2. **The compiler decides what matters.** Don't prescribe what kinds of articles must exist. The compiler reads raw inputs and the current wiki, then uses judgment to create, update, or connect articles. If a new type of knowledge emerges that doesn't fit any existing pattern, the compiler creates whatever structure makes sense.

3. **Connections are the most valuable layer.** Cross-cutting insights — patterns across deals, coaching themes from leadership, pricing behaviors of colleagues, industry playbooks that emerge from experience — these are what make the wiki more powerful than any single-deal analysis tool. The compiler should actively look for and surface these.

4. **Knowledge compounds.** Every question the user asks can produce an answer worth filing back into the wiki. Every won or lost deal teaches patterns. Every interaction with a colleague reveals how they work. The wiki should grow smarter over time with minimal manual maintenance.

5. **Raw inputs are never modified or truncated.** The `raw/` directory is the source of truth. Wiki articles are the compiler's synthesis — richer and more connected, but always traceable back to sources.

6. **Less structure is an advantage.** The more rigid the schema, the more it breaks when reality doesn't fit the template. Define conventions (frontmatter, wikilinks, index format) and quality standards, but give the compiler freedom to organize knowledge however makes sense for the domain.

### The Compiler's Job

The compiler runs periodically (every 30 minutes during business hours, or on-demand). It:

1. Reads all new raw inputs since last compile
2. Reads the current wiki index to understand what exists
3. Reads existing wiki articles relevant to the new inputs
4. For each meaningful piece of new information, decides: update an existing article, create a new one, or create/update a connection between articles
5. Updates the index
6. Logs what it did

The compiler sees the ENTIRE wiki on every pass. This enables cross-referencing — connecting a pricing confirmation from Teams to a budget discussion from a transcript to a coaching note from an internal 1:1, because it processes them all together.

### The Query/Analysis Layer (Separate from Compilation)

When the user needs outputs, analysis prompts read from the wiki. Examples:

- Score a deal against a methodology based on cited evidence from the wiki
- Draft an email matching the user's actual communication style (studied from their real sent emails)
- Prepare for a call by synthesizing deal + people + context articles
- Review the pipeline by reading across multiple deal articles and connection articles
- Update Salesforce by extracting structured data from wiki articles

These are separate processes from compilation. They apply methodology and produce outputs; the compiler builds and maintains knowledge.

### Knowledge Lifecycle

- Knowledge that's actively being updated stays current
- Deals that close (won or lost) transition to historical knowledge — patterns, lessons, what worked or didn't
- The lint process flags stale articles, broken links, orphaned pages, contradictions, and sparse articles
- People and concepts evolve over time — articles get updated, not deleted

### Technical Constraints

- Flat directory of markdown files (no required folder hierarchy — the compiler can create subdirectories if it makes sense, but isn't required to)
- YAML frontmatter for metadata
- `[[wikilinks]]` for cross-references (Obsidian-compatible)
- `index.md` as master catalog — the compiler reads this first on every pass
- `log.md` as append-only chronological record
- At current scale (~30 deals, ~100 people/concepts), the full wiki fits in context. Search tooling may be added later at scale.

### What the Schema Document Should Contain

Generate a schema document that covers:

1. **System overview** — what this is, the compiler analogy, how the layers work
2. **Wiki conventions** — file format, frontmatter fields, wikilink style, quality bar
3. **Index and log format** — how the catalog and build log are structured
4. **Compilation instructions** — what the compiler does on each pass, how it decides what to create/update/connect
5. **Quality standards** — minimum bar for article creation, when to merge vs. create new, how to handle contradictions
6. **Lifecycle rules** — how knowledge ages, what gets flagged, archival conventions

The schema should be comprehensive enough that a new LLM instance, reading only this document and the index, can immediately understand the system and begin compiling, querying, or linting effectively.

Keep it as simple and non-prescriptive as possible while still being clear enough to produce consistent, high-quality results.
