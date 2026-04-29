#!/usr/bin/env python3
"""AI World Knowledge Graph v2 CLI Helper
Usage: python3 /opt/data/ai_world_helper.py [command]

Commands:
  list [type]           - List entities (optionally filter by type)
  get <name>            - Show entity details + relationships
  search <term>         - Search entities by name/description
  stats                 - Database statistics
  graph <name>          - Show entity's neighborhood graph
  models [family]       - List AI models (optionally filter by family)
  model <slug>          - Show model details with pricing + benchmarks
  bench [name]          - Show benchmark rankings (all or specific)
  prices [min_params]   - Show cheapest models (sort by price/quality)
  top [bench]           - Top models by a benchmark (default: Arena ELO)
  edge                  - Show small models suitable for homelab/edge (<10B params)
  timeline              - Show recent events (placeholder)
"""

import sqlite3, json, sys, os

DB = '/opt/data/ai_world.db'

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def print_table(rows, headers):
    """Simple table formatter"""
    if not rows:
        print("  No results.")
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val or '')) + 1)
    
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_widths)
    print()
    print(fmt.format(*headers))
    print("  " + "-" * (sum(col_widths) + len(col_widths) * 2 - 1))
    for row in rows:
        print(fmt.format(*(str(v or '') for v in row)))
    print(f"  Total: {len(rows)}")

def list_entities(entity_type=None):
    conn = connect()
    if entity_type:
        cur = conn.execute(
            "SELECT id, name, entity_type, status FROM entities WHERE entity_type=? ORDER BY name",
            (entity_type,)
        )
    else:
        cur = conn.execute(
            "SELECT id, name, entity_type, status FROM entities ORDER BY entity_type, name"
        )
    rows = [(r['id'], r['name'], r['entity_type'], r['status']) for r in cur.fetchall()]
    conn.close()
    print_table(rows, ['ID', 'Name', 'Type', 'Status'])

def get_entity(name):
    conn = connect()
    cur = conn.execute("SELECT * FROM entities WHERE name LIKE ? OR slug LIKE ? LIMIT 1", (f'%{name}%', f'%{name}%'))
    entity = cur.fetchone()
    if not entity:
        print(f"No entity found matching '{name}'")
        conn.close()
        return
    d = dict(entity)
    print(f"\n{'='*60}")
    print(f"  {d['name']} ({d['entity_type']})")
    print(f"{'='*60}")
    for k, v in d.items():
        if v and k not in ('id', 'name', 'entity_type', 'created_at', 'updated_at'):
            if k == 'attrs' and v != '{}':
                attrs = json.loads(v)
                for ak, av in attrs.items():
                    print(f"  {ak}: {av}")
            elif v:
                print(f"  {k}: {v}")
    
    # Categories
    cur = conn.execute("""
        SELECT c.display_name FROM categories c
        JOIN entity_categories ec ON ec.category_id = c.id
        WHERE ec.entity_id = ?
    """, (d['id'],))
    cats = [r[0] for r in cur.fetchall()]
    if cats:
        print(f"  categories: {', '.join(cats)}")
    
    # Relationships (outgoing)
    print(f"\n  --- Relationships ---")
    cur = conn.execute("""
        SELECT r.relation_type, e.name, e.entity_type, r.start_date, r.end_date, r.description
        FROM relationships r JOIN entities e ON r.target_id = e.id
        WHERE r.source_id = ?
        ORDER BY r.relation_type
    """, (d['id'],))
    for r in cur.fetchall():
        span = ""
        if r['start_date'] or r['end_date']:
            end = f" -> {r['end_date']}" if r['end_date'] else " -> present"
            span = f" ({r['start_date'] or '?'}{end})"
        desc = f" — {r['description']}" if r['description'] else ""
        print(f"    {r['relation_type']}: {r['name']} ({r['entity_type']}){span}{desc}")
    
    # Incoming
    cur = conn.execute("""
        SELECT r.relation_type, e.name, e.entity_type, r.start_date, r.end_date
        FROM relationships r JOIN entities e ON r.source_id = e.id
        WHERE r.target_id = ?
        ORDER BY r.relation_type
    """, (d['id'],))
    for r in cur.fetchall():
        span = ""
        if r['start_date'] or r['end_date']:
            end = f" -> {r['end_date']}" if r['end_date'] else " -> present"
            span = f" ({r['start_date'] or '?'}{end})"
        print(f"    (in) {r['relation_type']}: {r['name']} ({r['entity_type']}){span}")
    
    conn.close()

def search(term):
    conn = connect()
    cur = conn.execute("""
        SELECT id, name, entity_type, description FROM entities
        WHERE name LIKE ? OR description LIKE ? OR slug LIKE ?
        ORDER BY name LIMIT 30
    """, (f'%{term}%', f'%{term}%', f'%{term}%'))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print(f"No results for '{term}'")
        return
    for r in rows:
        desc = (r['description'][:80] + '...') if r['description'] and len(r['description']) > 80 else (r['description'] or '')
        print(f"  [{r['entity_type']}] {r['name']} — {desc}")

def graph(name):
    conn = connect()
    cur = conn.execute("SELECT id, name, entity_type FROM entities WHERE name LIKE ?", (f'%{name}%',))
    entity = cur.fetchone()
    if not entity:
        print(f"No entity for '{name}'")
        conn.close()
        return
    print(f"\n  Graph: {entity['name']} [{entity['entity_type']}]")
    print(f"  {'='*50}")
    cur = conn.execute("""
        SELECT r.relation_type, e.name, e.entity_type
        FROM relationships r JOIN entities e ON r.target_id = e.id
        WHERE r.source_id = ?
        ORDER BY r.relation_type
    """, (entity['id'],))
    for r in cur.fetchall():
        print(f"  {entity['name']} --[{r['relation_type']}]--> {r['name']} ({r['entity_type']})")
    cur = conn.execute("""
        SELECT r.relation_type, e.name, e.entity_type
        FROM relationships r JOIN entities e ON r.source_id = e.id
        WHERE r.target_id = ?
        ORDER BY r.relation_type
    """, (entity['id'],))
    for r in cur.fetchall():
        print(f"  {r['name']} ({r['entity_type']}) --[{r['relation_type']}]--> {entity['name']}")
    conn.close()

def stats():
    conn = connect()
    tables = ['entities', 'relationships', 'models', 'model_pricing', 'model_benchmarks', 'events', 'categories']
    print(f"\n  Database Statistics:")
    print(f"  {'='*40}")
    for t in tables:
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {c}")
    
    print(f"\n  Entity types:")
    cur = conn.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type ORDER BY COUNT(*) DESC")
    for r in cur.fetchall():
        print(f"    {r['entity_type']}: {r[1]}")
    
    print(f"\n  Model families:")
    cur = conn.execute("SELECT model_family, COUNT(*) FROM models GROUP BY model_family ORDER BY COUNT(*) DESC")
    for r in cur.fetchall():
        print(f"    {r['model_family']}: {r[1]}")
    
    conn.close()

def list_models(family=None):
    conn = connect()
    if family:
        cur = conn.execute("""
            SELECT m.slug, m.name, m.model_family, m.parameter_count, m.status, e.name as provider
            FROM models m JOIN entities e ON m.provider_id = e.id
            WHERE m.model_family LIKE ?
            ORDER BY m.parameter_count DESC
        """, (f'%{family}%',))
    else:
        cur = conn.execute("""
            SELECT m.slug, m.name, m.model_family, m.parameter_count, m.status, e.name as provider
            FROM models m JOIN entities e ON m.provider_id = e.id
            ORDER BY m.model_family, m.release_date DESC
        """)
    rows = [(r['slug'], r['name'], r['provider'], r['model_family'], f"{r['parameter_count'] or '?'}B", r['status']) for r in cur.fetchall()]
    conn.close()
    print_table(rows, ['Slug', 'Name', 'Provider', 'Family', 'Params', 'Status'])

def show_model(slug):
    conn = connect()
    cur = conn.execute("""
        SELECT m.*, e.name as provider
        FROM models m JOIN entities e ON m.provider_id = e.id
        WHERE m.slug LIKE ? OR m.name LIKE ?
        LIMIT 1
    """, (f'%{slug}%', f'%{slug}%'))
    m = cur.fetchone()
    if not m:
        print(f"No model found for '{slug}'")
        conn.close()
        return
    d = dict(m)
    print(f"\n{'='*60}")
    print(f"  {d['name']} — {d['provider']}")
    print(f"{'='*60}")
    for k in ['slug', 'model_family', 'release_date', 'architecture', 'parameter_count', 'context_window', 'max_output_tokens', 'modalities', 'status']:
        if d.get(k):
            v = d[k]
            if k == 'parameter_count': v = f"{v}B"
            elif k == 'context_window': v = f"{v:,} tokens"
            elif k == 'max_output_tokens': v = f"{v:,} tokens"
            print(f"  {k}: {v}")
    
    # Pricing
    print(f"\n  --- Pricing (per 1M tokens, USD) ---")
    cur = conn.execute("SELECT tier, input_price, output_price, source, effective_date FROM model_pricing WHERE model_id=? ORDER BY input_price", (d['id'],))
    for r in cur.fetchall():
        print(f"  ${r['input_price']:>7.3f} in / ${r['output_price']:>7.3f} out  ({r['tier']}) [{r['source']}]")
    
    # Benchmarks
    print(f"\n  --- Benchmark Scores ---")
    cur = conn.execute("""
        SELECT b.name, mb.score, mb.score_max, mb.source, mb.eval_date
        FROM model_benchmarks mb JOIN benchmarks b ON mb.benchmark_id = b.id
        WHERE mb.model_id = ?
        ORDER BY b.name
    """, (d['id'],))
    for r in cur.fetchall():
        max_str = f" / {r['score_max']}" if r['score_max'] else ""
        src_str = f" [{r['source']}]" if r['source'] else ""
        print(f"  {r['name']}: {r['score']}{max_str}{src_str}")
    
    if not cur.fetchall() and True:  # dummy check
        pass
    
    conn.close()

def bench_rankings(bench_name=None):
    conn = connect()
    if bench_name:
        where = "AND b.name LIKE ?"
        params = (f'%{bench_name}%',)
    else:
        where = ""
        params = ()
    
    cur = conn.execute(f"""
        SELECT b.name as bench, m.name as model, mb.score, mb.score_max, mb.source
        FROM model_benchmarks mb
        JOIN benchmarks b ON mb.benchmark_id = b.id
        JOIN models m ON mb.model_id = m.id
        {where}
        ORDER BY b.name, mb.score DESC
        LIMIT 40
    """, params)
    rows = [(r['bench'], r['model'], r['score'], f"/{r['score_max']}" if r['score_max'] else "", r['source'] or '') for r in cur.fetchall()]
    conn.close()
    print_table(rows, ['Benchmark', 'Model', 'Score', 'Max', 'Source'])

def top_by_bench(bench_name='Chatbot Arena ELO', limit=15):
    conn = connect()
    cur = conn.execute("""
        SELECT m.name, mb.score, e.name as provider
        FROM model_benchmarks mb
        JOIN benchmarks b ON mb.benchmark_id = b.id
        JOIN models m ON mb.model_id = m.id
        JOIN entities e ON m.provider_id = e.id
        WHERE b.name LIKE ?
        ORDER BY mb.score DESC
        LIMIT ?
    """, (f'%{bench_name}%', limit))
    rows = [(r['name'], r['provider'], r['score']) for r in cur.fetchall()]
    conn.close()
    print_table(rows, ['Model', 'Provider', f'{bench_name} Score'])

def edge_models():
    """List small models suitable for homelab/edge (<10B params)"""
    conn = connect()
    cur = conn.execute("""
        SELECT m.name, m.slug, m.parameter_count, m.context_window, m.architecture, e.name as provider
        FROM models m JOIN entities e ON m.provider_id = e.id
        WHERE m.parameter_count < 10 AND m.status = 'active'
        ORDER BY m.parameter_count DESC
    """)
    rows = [(r['name'], r['slug'], f"{r['parameter_count']}B", f"{r['context_window']:,}", r['provider'], r['architecture'][:30] or '') for r in cur.fetchall()]
    conn.close()
    print_table(rows, ['Name', 'Slug', 'Params', 'Context', 'Provider', 'Arch'])

def prices_ranking(min_params=0):
    """Cheapest models by output price with quality indicators"""
    conn = connect()
    cur = conn.execute("""
        SELECT m.name, e.name as provider, m.parameter_count,
               p.input_price, p.output_price,
               mb.score as mmlu
        FROM model_pricing p
        JOIN models m ON p.model_id = m.id
        JOIN entities e ON m.provider_id = e.id
        LEFT JOIN model_benchmarks mb ON mb.model_id = m.id AND mb.benchmark_id = (SELECT id FROM benchmarks WHERE name = 'MMLU')
        WHERE m.parameter_count >= ? OR m.parameter_count IS NULL
        ORDER BY p.output_price ASC
        LIMIT 25
    """, (min_params,))
    rows = []
    seen = set()
    for r in cur.fetchall():
        key = r['name']
        if key in seen: continue
        seen.add(key)
        params = f"{r['parameter_count']}B" if r['parameter_count'] else "?"
        mmlu = f"MMLU:{r['mmlu']}" if r['mmlu'] else ""
        rows.append((r['name'], r['provider'], params, f"${r['input_price']:.3f}", f"${r['output_price']:.3f}", mmlu))
    conn.close()
    print_table(rows, ['Model', 'Provider', 'Params', 'Input $/1M', 'Output $/1M', 'Quality'])

def timeline(limit=15):
    conn = connect()
    cur = conn.execute("""
        SELECT date, title, category FROM events ORDER BY date DESC LIMIT ?
    """, (limit,))
    rows = [(r['date'], r['title'], r['category'] or '') for r in cur.fetchall()]
    conn.close()
    if not rows:
        print("\n  No events yet — will populate via daily updates.")
        return
    print_table(rows, ['Date', 'Event', 'Category'])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'list':
        list_entities(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == 'get':
        get_entity(' '.join(sys.argv[2:]))
    elif cmd == 'search':
        search(' '.join(sys.argv[2:]))
    elif cmd == 'stats':
        stats()
    elif cmd == 'graph':
        graph(' '.join(sys.argv[2:]))
    elif cmd == 'models':
        list_models(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == 'model':
        show_model(' '.join(sys.argv[2:]))
    elif cmd == 'bench':
        bench_rankings(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == 'top':
        top_by_bench(' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Chatbot Arena ELO')
    elif cmd == 'prices':
        min_p = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        prices_ranking(min_p)
    elif cmd == 'edge':
        edge_models()
    elif cmd == 'timeline':
        timeline()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
