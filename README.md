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

Python · Streamlit · SQLite (local) / PostgreSQL — Supabase (produção) · psycopg2
(pool de conexão via `@st.cache_resource`).

## Dois modos de banco (automático)

O app detecta sozinho onde salvar, sem trocar nenhuma linha de código:

| Situação | Banco usado | Indicador na sidebar |
|---|---|---|
| Sem `.streamlit/secrets.toml` | **SQLite local** (`catalogo.db`) | 🟠 Banco local (catalogo.db) |
| Com `database_url` preenchida | **Supabase (Postgres)** | 🟢 Supabase conectado |

As queries são escritas no dialeto Postgres (`%s`, `ILIKE`, `btrim`) e traduzidas
para SQLite em tempo de execução. As tabelas são criadas automaticamente na
primeira execução, nos dois modos.

## Rodar localmente (sem Supabase)

É o modo recomendado para montar o catálogo antes de publicar.

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

3. **Rode o app** — não precisa configurar nada
   ```bash
   streamlit run app.py
   ```

No Windows, basta dar duplo clique em `run.bat` (cria a venv e sobe o app).

Tudo que você cadastrar fica em `catalogo.db`, na própria pasta do projeto.
Esse arquivo está no `.gitignore` — é seu banco de trabalho, não vai pro repositório.

## Cadastro inicial

O app começa vazio (enquanto não houver produtos, a grade mostra itens de
exemplo só para você ver o layout).

1. Vá em **Produtos** → **＋ Novo produto**.
2. Preencha nome, SKU, link do vídeo (YouTube) e a descrição, e salve.
3. Abra o produto → **✏️ Editar** → **Adicionar pergunta** para montar o FAQ.

## Migrar para o Supabase (quando estiver pronto)

1. No Supabase, abra o **SQL Editor** e rode [`schema.sql`](schema.sql) (cria as tabelas).
2. Gere o seed com os dados que você cadastrou localmente:
   ```bash
   python exportar_para_supabase.py
   ```
   Isso cria `seed.sql` com todos os produtos e FAQs, preservando os IDs e os vínculos.
3. Cole o conteúdo de `seed.sql` no SQL Editor e execute.
4. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha
   `database_url` (Project Settings → Database → Connection string / URI).
5. Suba o app de novo — a sidebar deve mostrar **🟢 Supabase conectado**.

## Estrutura

```
.
├── app.py                          # aplicação Streamlit (navegação + páginas + acesso ao banco)
├── exportar_para_supabase.py       # gera seed.sql a partir do banco local
├── schema.sql                      # DDL das tabelas (produtos, faq_produto)
├── run.bat                         # inicializador local (Windows)
├── catalogo.db                     # banco local — criado na 1ª execução (ignorado no git)
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml                 # tema claro
│   └── secrets.toml.example        # modelo da connection string (copie para secrets.toml)
└── README.md
```

## Deploy (depois)

- **Streamlit Community Cloud**: conecte o repositório e cole a connection string em
  *App settings → Secrets* (mesmo formato do `secrets.toml`).
- Nesse caso, prefira a porta **6543** (Connection Pooler) na connection string do Supabase.
