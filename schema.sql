-- Catálogo SAC — esquema inicial
-- Rode uma vez no SQL Editor do Supabase (ou via psql) para criar as tabelas.

CREATE TABLE produtos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    sku TEXT UNIQUE,
    video_url TEXT,
    manual_texto TEXT,
    foto BYTEA,
    foto_thumb BYTEA,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE faq_produto (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL
);
