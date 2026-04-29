# AI World Knowledge Graph

Comprehensive SQLite database tracking the AI industry: entities (companies, people, products, institutions), relationships, models with pricing and benchmarks, news, and market data.

**Updated daily** via Hermes Agent cron job.

## Stats (Apr 29, 2026)

| Metric | Count |
|--------|-------|
| Entities | 316 |
| People (with X handles) | 70 |
| Relationships | 305 |
| Models | 52 |
| Model families | 23 |
| Pricing entries | 33 |
| Benchmark scores | 52 |
| Events | 84 |
| Categories | 34 |
| Blogs/Newsletters | 10 |
| Podcasts | 5 |
| Institutions | 10 |

## What's Tracked

### Companies
OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft AI, xAI, NVIDIA, AMD, Intel, TSMC, ASML, Broadcom, DeepSeek, Baidu, Alibaba, ByteDance, Zhipu AI, MiniMax, Moonshot AI, Mistral AI, Cohere, and 70+ more.

### People (70 researchers + executives)
- **OpenAI:** Sam Altman, Greg Brockman, Sarah Friar, Mira Murati, Alec Radford, John Schulman, Ilya Sutskever (now SSI), Andrej Karpathy
- **Anthropic:** Dario Amodei, Daniela Amodei, Rahul Patil, Amanda Askell, Chris Olah
- **NVIDIA:** Jensen Huang, Colette Kress
- **Google DeepMind:** Demis Hassabis, Jeff Dean, Oriol Vinyals, David Silver, John Jumper
- **Meta FAIR:** Yann LeCun, Kaiming He, Ross Girshick
- **Academia:** Yoshua Bengio (Mila), Geoffrey Hinton (UofT/Vector), Fei-Fei Li (Stanford), Stuart Russell (Berkeley)
- **Chinese AI:** Liang Wenfeng (DeepSeek), Yang Zhilin (Moonshot), Kai-Fu Lee (01.AI), Tang Jie (Zhipu)

### Models (52)
Full model cards with specs, pricing tiers ($/1M tokens), and benchmark scores (MMLU, HumanEval, GSM8K, MATH, Arena ELO).

### Relationships
CEO/founder connections, investment flows, hardware dependencies, academic lineages (Hinton→Sutskever, Fei-Fei→Karpathy), competition links.

### News + Market Data
Daily news aggregation + stock price snapshots for AI companies.

## Schema

```sql
-- Core entities (companies, people, products, institutions)
entities(id, name, entity_type, slug, description, founded, hq, wikilink, x_handle, website, blog_url, status)

-- Entity interconnections
relationships(source_id, target_id, relation_type, start_date, end_date, description, confidence)

-- Categories (hierarchical)
categories(id, name, display_name, parent_id)
entity_categories(entity_id, category_id)

-- AI Models
models(id, name, slug, provider_id, model_family, parameter_count, context_window, ...)
model_pricing(model_id, tier, input_price, output_price, pricing_unit, source)
model_benchmarks(model_id, benchmark_id, score, score_max, eval_date)
benchmarks(id, name)

-- Timeline
events(id, date, title, category, description)
event_entities(event_id, entity_id)

-- Trending
trending_tags(tag, category, mention_count, last_seen)
blog_topic_suggestions(title, tags, angle, relevance_score)
popular_searches(term, count, last_searched)
```

## CLI Tool

```bash
python3 /opt/data/ai_world_helper.py stats     # Full stats
python3 /opt/data/ai_world_helper.py list       # List all entities
python3 /opt/data/ai_world_helper.py get "OpenAI"  # Entity details + relationships
python3 /opt/data/ai_world_helper.py search "Musk"  # Search entities
python3 /opt/data/ai_world_helper.py graph "NVIDIA"  # Relationship neighborhood
python3 /opt/data/ai_world_helper.py top            # Arena ELO leaderboard
python3 /opt/data/ai_world_helper.py prices 70      # Cheapest frontier models
python3 /opt/data/ai_world_helper.py bench "MMLU"   # MMLU rankings
python3 /opt/data/ai_world_helper.py edge           # Homelab models <10B params
```

## Daily Update Pipeline

1. **News fetch** — Brave Search API + HackerNews → top AI stories
2. **Report generation** — Markdown with clickable source links
3. **Market snapshot** — Yahoo Finance stock prices for AI companies
4. **Email delivery** — SMTP to subscribers with unsubscribe support
5. **Database growth** — New entities discovered from news

## Data Sources

- Brave Search API (news, web, entity research)
- HackerNews Algolia API
- Yahoo Finance (market data)
- SEC EDGAR (company financials)
- OpenRouter (model pricing)
- LM Arena (benchmark data)

## License

MIT
