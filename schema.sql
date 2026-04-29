CREATE TABLE benchmarks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,        -- 'MMLU', 'HumanEval', 'Chatbot Arena ELO', etc.
    slug            TEXT UNIQUE,
    description     TEXT,
    metric_type     TEXT,                 -- 'accuracy', 'pass_rate', 'elo', 'perplexity', etc.
    higher_is_better INTEGER DEFAULT 1,   -- 1=yes, 0=lower is better
    source          TEXT,                 -- where benchmark is hosted/standard
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE TABLE blog_topic_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        tags TEXT,
        angle TEXT,
        relevance_score INTEGER DEFAULT 5,
        suggested_date TEXT,
        status TEXT DEFAULT 'suggested',
        created_at TEXT DEFAULT (datetime('now'))
    );
CREATE TABLE categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    parent_id   INTEGER REFERENCES categories(id),
    description TEXT,
    sort_order  INTEGER DEFAULT 0
);
CREATE TABLE entities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,   -- no CHECK constraint — blow it open
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE,     -- url-friendly unique key: 'openai', 'nvidia'
    aliases     TEXT,            -- JSON array: ["Open AI", "OpenAI LP", "OpenAI Inc."]
    description TEXT,
    founded     TEXT,            -- freeform: '2015-12-11', '2015', '1998'
    hq          TEXT,
    website     TEXT,
    x_handle    TEXT,
    wikilink    TEXT,
    logo_url    TEXT,
    status      TEXT DEFAULT 'active',  -- active, acquired, merged, closed, dormant
    attrs       TEXT DEFAULT '{}',       -- JSON blob for any extra fields
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE entity_categories (
    entity_id    INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, category_id)
);
CREATE TABLE entity_tags (
    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    tag_id    INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, tag_id)
);
CREATE TABLE event_entities (
    event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    entity_id  INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role       TEXT,  -- subject, target, participant, etc.
    PRIMARY KEY (event_id, entity_id)
);
CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    date        TEXT NOT NULL,
    end_date    TEXT,
    description TEXT,
    category    TEXT,    -- funding, acquisition, product_launch, research, regulation, hiring, partnership, other
    attrs       TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE model_benchmarks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    benchmark_id    INTEGER NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
    score           REAL NOT NULL,
    score_max       REAL,                 -- for normalized scores (e.g. 80/100)
    eval_date       TEXT,                 -- when this score was measured
    eval_method     TEXT,                 -- 'official', 'community', 'self-reported'
    source          TEXT,                 -- URL or reference
    attrs           TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(model_id, benchmark_id, eval_date)
);
CREATE TABLE model_performance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    provider_id     INTEGER REFERENCES entities(id),  -- who serves it (could differ from creator)
    endpoint_type   TEXT DEFAULT 'chat',   -- 'chat', 'completion', 'embedding', 'image'
    latency_p50     REAL,                  -- median latency in seconds
    latency_p99     REAL,                  -- p99 latency in seconds
    throughput      REAL,                  -- tokens per second (output)
    input_cost_per_m NUMERIC,             -- may differ from standard pricing
    output_cost_per_m NUMERIC,
    measurement_date TEXT,
    source          TEXT,
    attrs           TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
, pricing_unit TEXT);
CREATE TABLE model_pricing (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id    INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tier        TEXT DEFAULT 'standard',  -- standard, batch, fine-tuned, etc.
    input_price NUMERIC,                  -- per 1M tokens (USD)
    output_price NUMERIC,                 -- per 1M tokens (USD)
    currency    TEXT DEFAULT 'USD',
    effective_date TEXT,
    source      TEXT,                     -- where we got this price
    attrs       TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now'))
, pricing_unit TEXT DEFAULT 'per_1M_tokens');
CREATE TABLE models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE,          -- 'gpt-4o', 'claude-3-opus'
    provider_id     INTEGER REFERENCES entities(id),  -- who makes it (OpenAI, Anthropic)
    model_family    TEXT,                 -- 'GPT-4', 'Claude 3', 'Gemini 1.5'
    release_date    TEXT,
    architecture    TEXT,                 -- 'transformer-decoder', 'MoE', 'diffusion'
    parameter_count INTEGER,             -- in billions (NULL if unknown)
    context_window  INTEGER,             -- max tokens
    max_output_tokens INTEGER,
    modalities      TEXT,                 -- JSON: ['text','image','code','audio','video']
    status          TEXT DEFAULT 'active', -- active, deprecated, upcoming
    description     TEXT,
    attrs           TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE TABLE popular_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        date TEXT NOT NULL DEFAULT (date('now')),
        source TEXT,
        count INTEGER DEFAULT 1,
        category TEXT,
        UNIQUE(query, date)
    );
CREATE TABLE relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_id       INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,   -- founded_by, ceo_of, acquired, invested_in, etc.
    start_date      TEXT,
    end_date        TEXT,
    description     TEXT,
    confidence      INTEGER DEFAULT 3 CHECK(confidence BETWEEN 1 AND 5),
    attrs           TEXT DEFAULT '{}',  -- JSON for extra metadata (amount, shares, etc.)
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE TABLE tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE trending_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT NOT NULL UNIQUE,
        category TEXT,
        first_seen TEXT DEFAULT (datetime('now')),
        last_seen TEXT DEFAULT (datetime('now')),
        mention_count INTEGER DEFAULT 1,
        peak_date TEXT,
        source TEXT,
        notes TEXT
    );
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_rel_source ON relationships(source_id);
CREATE INDEX idx_rel_target ON relationships(target_id);
CREATE INDEX idx_rel_type ON relationships(relation_type);
CREATE UNIQUE INDEX idx_rel_unique ON relationships(source_id, target_id, relation_type, COALESCE(start_date, ''));
CREATE INDEX idx_events_date ON events(date);
CREATE INDEX idx_models_provider ON models(provider_id);
CREATE INDEX idx_models_family ON models(model_family);
