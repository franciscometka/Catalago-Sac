# Catálogo SAC

Ferramenta interna para o time de atendimento consultar, de forma rápida, **vídeos de
montagem**, **manuais** e **dúvidas frequentes (FAQ)** de cada produto durante o
atendimento ao cliente.

MVP simples, sem login — pensado para uso interno de poucas pessoas.

## O que faz

- Busca de produtos por **nome** ou **SKU** (parcial, sem diferenciar maiúsculas/minúsculas).
- Visualização detalhada com **vídeo embedado do YouTube**, **manual em texto** e **lista de FAQ**.
- Cadastro rápido de novos produtos e de perguntas/respostas, direto na interface.

## Páginas

- **Home** — landing com busca central e um resumo de "como funciona".
- **Produtos** — busca em grade de cards, detalhe do produto e cadastro (produto + FAQ).
- **Sobre** — o que é a ferramenta, como cadastrar e contato.

## Stack

Python · Streamlit · PostgreSQL (Supabase) · psycopg2 (pool de conexão via `@st.cache_resource`).

## Rodar localmente

1. **Crie e ative um ambiente virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   # source venv/bin/activate # macOS/Linux
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o acesso ao banco**
   - Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
   - Preencha `database_url` com a connection string do seu projeto Supabase
     (Project Settings → Database → Connection string / URI).

4. **Crie as tabelas** (uma vez)
   - Abra o **SQL Editor** do Supabase e rode o conteúdo de [`schema.sql`](schema.sql).

5. **Rode o app**
   ```bash
   streamlit run app.py
   ```

## Cadastro inicial

Depois de criar as tabelas, o app começa vazio. Para popular:

1. Vá em **Produtos** → **＋ Cadastrar produto**.
2. Preencha nome, SKU, link do vídeo (YouTube) e o manual, e salve.
3. Use **Adicionar pergunta/resposta** para montar o FAQ de cada produto.

## Estrutura

```
.
├── app.py                          # aplicação Streamlit (navegação + páginas + acesso ao banco)
├── schema.sql                      # DDL das tabelas (produtos, faq_produto)
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example        # modelo da connection string (copie para secrets.toml)
└── README.md
```

## Deploy (depois)

Roda local por enquanto. Para publicar depois:
- **Streamlit Community Cloud**: conecte o repositório e cole a connection string em *App settings → Secrets* (mesmo formato do `secrets.toml`).
- Nesse caso, prefira a porta **6543** (Connection Pooler) na connection string do Supabase.
