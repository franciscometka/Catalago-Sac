"""
Gera seed.sql com tudo que está no banco local (catalogo.db), pronto para
rodar no SQL Editor do Supabase.

Uso:
    python exportar_para_supabase.py

Passo a passo da migração:
    1. Rode schema.sql no SQL Editor do Supabase (cria as tabelas).
    2. Rode este script e cole o conteúdo de seed.sql no SQL Editor.
    3. Preencha .streamlit/secrets.toml com a connection string.
       O app passa a usar o Supabase automaticamente.
"""

import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "catalogo.db")
OUT = os.path.join(BASE, "seed.sql")


def esc(valor):
    if valor is None:
        return "NULL"
    return "'" + str(valor).replace("'", "''") + "'"


def esc_bytes(valor):
    """Literal bytea do Postgres a partir de bytes (formato hex '\\x...')."""
    if valor is None:
        return "NULL"
    return "'\\x" + bytes(valor).hex() + "'::bytea"


def main():
    if not os.path.exists(DB):
        print("catalogo.db não encontrado — cadastre produtos no app primeiro.")
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    produtos = conn.execute(
        "SELECT id, nome, sku, video_url, manual_texto, foto, foto_thumb FROM produtos ORDER BY id"
    ).fetchall()
    faqs = conn.execute(
        "SELECT produto_id, pergunta, resposta FROM faq_produto ORDER BY id"
    ).fetchall()
    conn.close()

    linhas = [
        "-- Seed gerado a partir do banco local do Catálogo SAC (catalogo.db).",
        "-- Cole no SQL Editor do Supabase e execute.",
        "-- Os IDs originais são preservados para manter os vínculos do FAQ.",
        "",
    ]

    for p in produtos:
        linhas.append(
            "INSERT INTO produtos (id, nome, sku, video_url, manual_texto, foto, foto_thumb) VALUES "
            f"({p['id']}, {esc(p['nome'])}, {esc(p['sku'])}, "
            f"{esc(p['video_url'])}, {esc(p['manual_texto'])}, {esc_bytes(p['foto'])}, "
            f"{esc_bytes(p['foto_thumb'])});"
        )

    linhas.append("")

    for f in faqs:
        linhas.append(
            "INSERT INTO faq_produto (produto_id, pergunta, resposta) VALUES "
            f"({f['produto_id']}, {esc(f['pergunta'])}, {esc(f['resposta'])});"
        )

    # Reajusta as sequências para os próximos inserts não colidirem.
    linhas += [
        "",
        "SELECT setval(pg_get_serial_sequence('produtos', 'id'), "
        "COALESCE((SELECT MAX(id) FROM produtos), 1));",
        "SELECT setval(pg_get_serial_sequence('faq_produto', 'id'), "
        "COALESCE((SELECT MAX(id) FROM faq_produto), 1));",
    ]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas) + "\n")

    print(f"Gerado: {OUT}")
    print(f"{len(produtos)} produto(s) e {len(faqs)} pergunta(s) exportados.")


if __name__ == "__main__":
    main()
