# AI Newsletter Sources Manifest

Reference document for the semi-weekly AI newsletter agent. All sources below are approved for ingestion. Each entry includes the fetch method, any filtering rules, and a short note on what signal it provides.

---

## Fetch Strategy Overview

| Method | Used For |
|---|---|
| RSS | Blogs, newsletters, subreddits, filtered HN |
| RSSHub | X/Twitter accounts (via `rsshub.app/twitter/user/{handle}`) |
| Scrape | GitHub Trending, Product Hunt, HN front page |
| Podcast RSS + transcript page | Latent Space, Lenny's |

Always prefer RSS over scraping when available. For X accounts, use RSSHub as primary; fall back to Nitter instances or cancelx.io if RSSHub is unavailable.

---

## Individual Writers & Thinkers

### Simon Willison
- **URL:** https://simonwillison.net
- **RSS:** https://simonwillison.net/atom/everything/
- **Signal:** Practical tool discovery, LLM technique shifts, early breakout detection. High post volume — filter by length; short link posts are still worth including.

### Kent Beck
- **URL:** https://tidyfirst.substack.com
- **RSS:** https://tidyfirst.substack.com/feed
- **Signal:** Mental model shifts around AI + software design. Lower volume, high signal — include all posts.

### Ethan Mollick (One Useful Thing)
- **URL:** https://www.oneusefulthing.org
- **RSS:** https://www.oneusefulthing.org/feed
- **Signal:** Practical AI use patterns, productivity mental models. Accessible framing useful for non-technical context.

### Nathan Lambert (Interconnects)
- **URL:** https://www.interconnects.ai
- **RSS:** https://www.interconnects.ai/feed
- **Signal:** RLHF, training dynamics, model behavior research. Best source for understanding what's happening inside model development.

### Sebastian Raschka (Ahead of AI)
- **URL:** https://magazine.sebastianraschka.com
- **RSS:** https://magazine.sebastianraschka.com/feed
- **Signal:** Deep paper synthesis, technical depth on architecture and training. Monthly cadence, always worth including in full.

### Zvi Mowshowitz
- **URL:** https://thezvi.substack.com
- **RSS:** https://thezvi.substack.com/feed
- **Signal:** Weekly roundup format; good counterweight on capability claims and safety framing. High volume — skim for AI-specific sections.

### Eugene Yan
- **URL:** https://eugeneyan.com
- **RSS:** https://eugeneyan.com/atom.xml
- **Signal:** Applied ML, real deployment patterns, system design. Infrequent but consistently practical.

### swyx (Shawn Wang)
- **URL:** https://www.swyx.io
- **RSS:** https://www.swyx.io/rss.xml
- **Signal:** Early tool trend barometer. Often first to write up what's quietly gaining traction.

---

## Newsletters & Publications

### Every
- **RSS:** https://every.to/feeds/58d892e7e1b77cde03cc.xml *(authenticated — use as-is)*
- **Signal:** AI strategy, product thinking, and business implications. Chain of Thought and Napkin Math are the highest-signal columns.

### Latent Space
- **URL:** https://www.latent.space
- **RSS:** https://www.latent.space/feed
- **Transcripts:** Published on the episode page; link from RSS item
- **Signal:** Deep technical interviews. Include episode summaries; transcripts only when the topic is directly relevant to tool trends or technique shifts.

### Lenny's Newsletter / Podcast
- **URL:** https://www.lennysnewsletter.com
- **RSS:** https://www.lennysnewsletter.com/feed
- **Podcast RSS:** https://feeds.simplecast.com/OGYgnd7v
- **Filter:** Only include items where title or description contains one or more of: `AI`, `LLM`, `agent`, `model`, `automation`, `copilot`, `artificial intelligence`. Skip general PM/growth content.
- **Signal:** When Lenny covers AI, it usually marks a topic reaching PM/operator mainstream — useful as a "crossing the chasm" indicator.

### Import AI (Jack Clark)
- **URL:** https://importai.substack.com
- **RSS:** https://importai.substack.com/feed
- **Signal:** Best weekly research digest. Strong on geopolitical and policy context alongside technical developments.

### The Batch (Andrew Ng / DeepLearning.AI)
- **URL:** https://www.deeplearning.ai/the-batch/
- **RSS:** https://www.deeplearning.ai/the-batch/feed/
- **Signal:** Reliable weekly overview; good for model announcements and applied research. More accessible framing than Interconnects.

---

## Lab & Company Blogs

### Anthropic
- **URL:** https://www.anthropic.com/news
- **RSS:** https://www.anthropic.com/rss.xml
- **Signal:** Claude releases, safety research, interpretability work. Include all posts.

### OpenAI
- **URL:** https://openai.com/blog
- **RSS:** https://openai.com/blog/rss.xml
- **Signal:** Model releases, API changes, product direction. Include all posts.

### Google DeepMind
- **URL:** https://deepmind.google/blog/
- **RSS:** https://deepmind.google/blog/rss/
- **Signal:** Research breakthroughs, Gemini updates, infrastructure papers.

### Meta AI
- **URL:** https://ai.meta.com/blog/
- **RSS:** https://ai.meta.com/blog/rss/
- **Signal:** Open-weight model releases (Llama lineage), research direction.

### Hugging Face
- **URL:** https://huggingface.co/blog
- **RSS:** https://huggingface.co/blog/feed.xml
- **Signal:** Open-source ecosystem, new model releases, tooling launches. High volume — prioritize posts with >100 likes or that introduce new models/datasets.

### Mistral
- **URL:** https://mistral.ai/news/
- **Signal:** Scrape or check manually; no reliable RSS. Include model releases and API announcements.

---

## X / Twitter Accounts

Fetch via RSSHub: `https://rsshub.app/twitter/user/{handle}`
Fall back to Nitter or cancelx.io if RSSHub is rate-limited.

Filter all X sources by engagement: only surface posts with meaningful signal (replies/retweets suggest resonance). Exclude pure reposts unless the commentary is substantive.

### Individual Researchers & Builders
| Handle | Name | Signal |
|---|---|---|
| @bcherny | Brian Cherny (Anthropic) | TypeScript, Claude tooling, agentic patterns |
| @karpathy | Andrej Karpathy | Architecture intuition, training mental models |
| @alexalbert__ | Alex Albert (Anthropic) | Prompting practice, Claude capabilities |
| @_jasonwei | Jason Wei | Chain-of-thought, reasoning research |
| @fchollet | François Chollet | Capability skepticism; useful counterweight |
| @jeremyphoward | Jeremy Howard | Practical deep learning, fast.ai ecosystem |
| @rasbt | Sebastian Raschka | Mirrors his blog; quick-hit paper takes |
| @swyx | Shawn Wang | Tool trend barometer |
| @natfriedman | Nat Friedman | Infra and tooling investment signals |
| @danielgross | Daniel Gross | What's actually gaining traction via investor lens |

### Lab Executives (lower volume, higher macro signal)
| Handle | Name | Signal |
|---|---|---|
| @samaltman | Sam Altman (OpenAI) | Release hints, macro direction |
| @gdb | Greg Brockman (OpenAI) | Infrequent, high signal |
| @miramurati | Mira Murati | Now independent; still influential on product direction |
| @karinanguyen_ | Karina Nguyen (Anthropic) | Practical Claude use patterns |

---

## Trend Detection Sources

These are not editorial sources — they are signals for breakout tool and technique discovery. Treat as raw data to be filtered and synthesized, not as content to summarize directly.

### Hugging Face Papers
- **URL:** https://huggingface.co/papers
- **RSS:** https://huggingface.co/papers/rss
- **Signal:** What researchers are reading and upvoting daily. Breakout papers appear here 1–2 weeks before mainstream coverage. Sort by likes; include top 3–5 per cycle.

### Hacker News (AI-filtered)
- **RSS:** https://hnrss.org/newest?q=AI&points=100
- **Signal:** Community-vetted breakouts. Raise the points threshold (100+) to cut noise. A tool hitting HN front page with 200+ points is a reliable early signal.
- **Alternate:** https://hnrss.org/frontpage for broader front page monitoring.

### GitHub Trending (Python + TypeScript)
- **URL:** https://github.com/trending/python?since=weekly and https://github.com/trending/typescript?since=weekly
- **Signal:** Repos blowing up. Scan for AI/ML repos with >500 stars in the week. This is where tools like Cursor, Open Interpreter, and similar surfaced before mainstream coverage.
- **Method:** Scrape weekly; no RSS available.

### Product Hunt (AI category)
- **URL:** https://www.producthunt.com/topics/artificial-intelligence
- **RSS:** https://www.producthunt.com/feed?category=artificial-intelligence
- **Signal:** Consumer-facing AI tool launches. Filter for products with >200 upvotes. Useful for tracking what non-technical users are actually adopting.

### r/LocalLLaMA
- **RSS:** https://www.reddit.com/r/LocalLLaMA/.rss
- **Signal:** Open-weight model adoption, fine-tuning techniques, inference tooling. Community notices capability shifts and new models very early.

### r/MachineLearning
- **RSS:** https://www.reddit.com/r/MachineLearning/.rss
- **Filter:** Hot posts only; minimum score threshold of 200.
- **Signal:** Research community consensus on important papers and results.

---

## Content Categories & Tagging

When processing sources, tag each item with one or more of the following categories. These map to newsletter sections:

| Tag | Description |
|---|---|
| `model-release` | New model or significant version update from any lab |
| `tool-breakout` | Tool or repo gaining rapid adoption (GitHub stars, HN, PH signals) |
| `technique-shift` | New prompting method, architecture pattern, or training approach |
| `mental-model` | New framing or way of thinking about AI capabilities or limitations |
| `research` | Academic or lab paper with practical implications |
| `ecosystem` | Tooling, infrastructure, standards, integrations |
| `industry` | Business, investment, policy, or market signals |

Items may carry multiple tags. Prioritize `tool-breakout` and `model-release` for the opening section; `mental-model` and `technique-shift` for depth sections.

---

## Exclusion Rules

- Skip press releases, earnings reports, and marketing announcements with no technical substance
- Skip Lenny's Newsletter/Podcast items that do not match the AI keyword filter
- Skip X posts that are purely promotional or event announcements without substantive content
- Skip Hugging Face blog posts that are purely dataset releases with no model or technique relevance
- Do not duplicate items already covered in the previous newsletter cycle
