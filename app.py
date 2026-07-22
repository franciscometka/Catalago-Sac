"""Catálogo SAC — consulta rápida de vídeos de montagem, manuais e FAQ de produtos.

Design: dashboard claro (fonte Manrope), sidebar customizada, topbar com busca,
hero com gradiente azul, stat cards e cards de produto.
"""

import html
import re
from urllib.parse import urlparse, parse_qs

import psycopg2
from psycopg2.pool import SimpleConnectionPool
import streamlit as st

# --------------------------------------------------------------------------- #
# Configuração da página
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Catálogo SAC",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Conexão com o banco (padrão trayo-app: pool via @st.cache_resource)
# --------------------------------------------------------------------------- #
@st.cache_resource
def get_pool():
    """Cria um pool de conexões reutilizável durante toda a sessão do app."""
    database_url = st.secrets["connections"]["database_url"]
    return SimpleConnectionPool(minconn=1, maxconn=5, dsn=database_url)


def run_query(sql, params=None, fetch=True):
    """Executa uma query usando uma conexão do pool. Placeholder = %s."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch:
                rows = cur.fetchall()
                cols = [c.name for c in cur.description]
                conn.commit()
                return [dict(zip(cols, r)) for r in rows]
            conn.commit()
            return None
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# --------------------------------------------------------------------------- #
# Acesso a dados
# --------------------------------------------------------------------------- #
def buscar_produtos(termo=""):
    termo = (termo or "").strip()
    if termo:
        like = f"%{termo}%"
        return run_query(
            """
            SELECT id, nome, sku, video_url, manual_texto, criado_em
            FROM produtos
            WHERE nome ILIKE %s OR sku ILIKE %s
            ORDER BY nome
            """,
            (like, like),
        )
    return run_query(
        """
        SELECT id, nome, sku, video_url, manual_texto, criado_em
        FROM produtos
        ORDER BY nome
        """
    )


def buscar_faq(produto_id):
    return run_query(
        "SELECT id, pergunta, resposta FROM faq_produto WHERE produto_id = %s ORDER BY id",
        (produto_id,),
    )


def get_stats():
    """Contagens reais para os stat cards da Home."""
    row = run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM produtos) AS produtos,
            (SELECT COUNT(*) FROM produtos
                WHERE video_url IS NOT NULL AND btrim(video_url) <> '') AS videos,
            (SELECT COUNT(*) FROM faq_produto) AS faqs
        """
    )
    return row[0] if row else {"produtos": 0, "videos": 0, "faqs": 0}


def inserir_produto(nome, sku, video_url, manual_texto):
    run_query(
        """
        INSERT INTO produtos (nome, sku, video_url, manual_texto)
        VALUES (%s, %s, %s, %s)
        """,
        (nome, sku or None, video_url or None, manual_texto or None),
        fetch=False,
    )


def inserir_faq(produto_id, pergunta, resposta):
    run_query(
        "INSERT INTO faq_produto (produto_id, pergunta, resposta) VALUES (%s, %s, %s)",
        (produto_id, pergunta, resposta),
        fetch=False,
    )


def atualizar_produto(pid, nome, sku, video_url, manual_texto):
    run_query(
        """
        UPDATE produtos
        SET nome = %s, sku = %s, video_url = %s, manual_texto = %s
        WHERE id = %s
        """,
        (nome, sku or None, video_url or None, manual_texto or None, pid),
        fetch=False,
    )


def atualizar_faq(faq_id, pergunta, resposta):
    run_query(
        "UPDATE faq_produto SET pergunta = %s, resposta = %s WHERE id = %s",
        (pergunta, resposta, faq_id),
        fetch=False,
    )


def deletar_faq(faq_id):
    run_query("DELETE FROM faq_produto WHERE id = %s", (faq_id,), fetch=False)


# --------------------------------------------------------------------------- #
# Utilidades de vídeo
# --------------------------------------------------------------------------- #
def youtube_id(url):
    """Extrai o ID de um vídeo do YouTube. Retorna None se não for YouTube."""
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    vid = None
    if host == "youtu.be":
        vid = parsed.path.lstrip("/").split("/")[0]
    elif host in ("youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            vid = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/embed/"):
            vid = parsed.path.split("/embed/")[1].split("/")[0]
        elif parsed.path.startswith("/shorts/"):
            vid = parsed.path.split("/shorts/")[1].split("/")[0]
    if vid:
        return re.sub(r"[^\w-]", "", vid)
    return None


def youtube_thumbnail(url):
    vid = youtube_id(url)
    return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else None


# --------------------------------------------------------------------------- #
# Tema / CSS
# --------------------------------------------------------------------------- #
def inject_css():
    # IMPORTANTE: usar st.html (não st.markdown) para o CSS. O st.markdown passa o
    # conteúdo por um processador de Markdown que encerra o bloco HTML na primeira
    # linha em branco, fazendo o CSS "vazar" como texto na página.
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
        :root {
            --blue:#3B82F6; --blue-h:#2563eb; --blue-soft:#e0edff;
            --bg:#F7F8FA; --card:#ffffff; --border:#eef1f5;
            --ink:#0f172a; --ink2:#1e293b; --muted:#64748b; --muted2:#94a3b8;
            --radius:14px; --shadow:0 1px 3px rgba(0,0,0,0.08);
        }

        /* ---- Base ---- */
        /* Força Manrope sobre o tema padrão do Streamlit, sem afetar fontes de ícone. */
        .stApp, section[data-testid="stSidebar"],
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp li, .stApp label,
        .stApp button, .stApp input, .stApp textarea, .stApp select,
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {
            font-family: 'Manrope', system-ui, -apple-system, sans-serif !important;
        }
        .stApp { background: var(--bg); }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1180px; }
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        div[data-testid="stAppViewContainer"] p,
        div[data-testid="stAppViewContainer"] li,
        div[data-testid="stMarkdownContainer"] { color: var(--ink2); }

        /* ---- Esconde chrome do Streamlit (menu, deploy, footer) ---- */
        #MainMenu {visibility: hidden;}
        [data-testid="stMainMenuButton"] {display:none !important;}
        [data-testid="stAppDeployButton"] {display:none !important;}
        [data-testid="stStatusWidget"] {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background: transparent; }
        /* Barra lateral FIXA: esconde o controle de recolher/expandir para que
           ela fique sempre aberta e no lugar. */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"] { display: none !important; }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            background: var(--card); border-right: 1px solid var(--border); width: 264px !important;
        }
        section[data-testid="stSidebar"] > div { padding-top: .5rem; }
        .sb-brand { display:flex; align-items:center; gap:12px; padding: 6px 8px 4px 8px; }
        .sb-logo {
            width:36px; height:36px; border-radius:9px; background:var(--blue);
            display:flex; align-items:center; justify-content:center;
            color:#fff; font-weight:800; font-size:18px; flex-shrink:0;
        }
        .sb-brand .t { font-weight:800; font-size:15px; color:var(--ink); line-height:1.2; }
        .sb-brand .s { font-weight:500; font-size:12px; color:var(--muted2); line-height:1.2; }
        .sb-caption {
            font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
            color:var(--muted2); padding: 14px 10px 4px 10px;
        }
        .sb-help {
            background:var(--bg); border-radius:12px; padding:16px; margin: 10px 6px 4px 6px;
            display:flex; flex-direction:column; gap:6px;
        }
        .sb-help .h { font-weight:700; font-size:13px; color:var(--ink); }
        .sb-help .p { font-weight:400; font-size:12px; line-height:1.5; color:var(--muted); }
        .sb-help a { font-weight:600; font-size:13px; color:var(--blue); margin-top:2px; }

        /* Botões de navegação (sidebar) */
        section[data-testid="stSidebar"] .stButton > button {
            width:100%; text-align:left; justify-content:flex-start;
            border:none; background:transparent; color:var(--muted);
            font-weight:600; font-size:14px; padding:.6rem .75rem;
            border-radius:10px; margin-bottom:2px; transition:all .18s ease;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background:var(--bg); color:var(--ink2);
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--blue-soft) !important; color: var(--blue) !important;
            box-shadow:none !important;
        }

        /* ---- Botões azuis (corpo) ---- */
        div[data-testid="stAppViewContainer"] .stButton > button[kind="primary"],
        .stFormSubmitButton > button {
            background: var(--blue); color:#fff; border:none; border-radius:10px;
            font-weight:700; box-shadow:none;
        }
        div[data-testid="stAppViewContainer"] .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button:hover { background: var(--blue-h); color:#fff; }

        /* ---- Topbar ---- */
        .st-key-topbar_search div[data-testid="stTextInputRootElement"] { border:none; }
        .st-key-topbar_search input {
            border-radius:10px; border:1px solid var(--border) !important; background:#fff;
            padding:11px 14px 11px 42px !important; font-size:14px; font-weight:500;
            box-shadow: var(--shadow);
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E");
            background-repeat:no-repeat; background-position:14px center;
        }
        .st-key-topbar_search input:focus {
            border:1px solid var(--blue) !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
        }
        .topbar-user { display:flex; align-items:center; justify-content:flex-end; gap:14px; height:44px; }
        .tb-bell {
            width:40px; height:40px; border-radius:10px; border:1px solid var(--border);
            background:#fff; display:flex; align-items:center; justify-content:center;
            color:#334155; box-shadow:var(--shadow);
        }
        .tb-avatar {
            width:40px; height:40px; border-radius:50%; background:var(--blue-soft);
            color:var(--blue); display:flex; align-items:center; justify-content:center;
            font-weight:700; font-size:14px; flex-shrink:0;
        }
        .tb-name { font-weight:700; font-size:13px; color:var(--ink); line-height:1.3; }
        .tb-role { font-weight:500; font-size:12px; color:var(--muted2); line-height:1.3; }

        /* ---- Hero (container st-key-hero_box) ---- */
        .st-key-hero_box {
            background: linear-gradient(120deg,#3B82F6,#1E40AF);
            border: 1px dashed rgba(255,255,255,0.35); border-radius:16px;
            padding:36px 40px; box-shadow:var(--shadow); margin-bottom:8px;
        }
        .hero-txt .badge {
            display:inline-block; background:rgba(255,255,255,0.18); color:#fff;
            font-weight:600; font-size:12px; padding:6px 12px; border-radius:999px;
        }
        .hero-txt h1 { margin:14px 0 10px 0; font-weight:800; font-size:34px; line-height:1.2; color:#fff !important; }
        .hero-txt p { margin:0; font-weight:400; font-size:15px; line-height:1.6; color:rgba(255,255,255,0.9) !important; max-width:560px; }
        .hero-art {
            width:180px; height:140px; margin-left:auto; border-radius:14px;
            background:rgba(255,255,255,0.14); display:flex; align-items:center; justify-content:center;
            color:rgba(255,255,255,0.8);
        }
        /* Botão escuro do hero, dentro do card */
        .st-key-hero_cta button {
            background:#0f172a !important; border:none !important;
            border-radius:10px !important; margin-top:14px; box-shadow:none !important;
        }
        .st-key-hero_cta button:hover { background:#020617 !important; }
        /* Texto do botão branco e bold (sobrepõe a cor global de markdown) */
        .st-key-hero_cta button, .st-key-hero_cta button * {
            color:#fff !important; font-weight:700 !important;
        }

        /* ---- Stat cards ---- */
        .stat { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            padding:22px 24px; box-shadow:var(--shadow); }
        .stat .l { font-weight:500; font-size:13px; color:var(--muted); }
        .stat .v { font-weight:800; font-size:28px; color:var(--ink); margin-top:6px; }

        /* ---- Seções ---- */
        .sec-title { font-weight:700; font-size:20px; color:var(--ink); margin:6px 0 2px 0; }
        .sec-sub { font-weight:400; font-size:14px; color:var(--muted); margin-bottom:10px; }
        .page-title { font-weight:800; font-size:26px; color:var(--ink); margin:0; }
        .page-sub { font-weight:400; font-size:14px; color:var(--muted); margin:2px 0 0 0; }

        /* ---- Step cards ---- */
        .step { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            padding:24px; box-shadow:var(--shadow); height:100%; }
        .step .n { width:40px; height:40px; border-radius:10px; background:var(--blue-soft);
            color:var(--blue); display:flex; align-items:center; justify-content:center;
            font-weight:800; font-size:16px; margin-bottom:12px; }
        .step .t { font-weight:700; font-size:16px; color:var(--ink); margin-bottom:6px; }
        .step .b { font-weight:400; font-size:14px; line-height:1.6; color:var(--muted); }

        /* ---- Product cards ---- */
        .pcard-link { text-decoration:none !important; color:inherit; display:block; }
        .pcard-link:hover { color:inherit; }
        .pcard { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            overflow:hidden; box-shadow:var(--shadow); transition:all .18s ease; margin-bottom:10px; }
        .pcard-link:hover .pcard { border-color:var(--blue); box-shadow:0 6px 18px rgba(59,130,246,0.15); transform:translateY(-3px); }
        .pcard .photo { height:150px; background:#f1f5f9 center/cover no-repeat;
            display:flex; align-items:center; justify-content:center; color:#cbd5e1;
            font-family:monospace; font-size:12px; }
        .pcard .body { padding:16px; display:flex; flex-direction:column; gap:8px; }
        .pcard .row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
        .pcard .cat { font-weight:600; font-size:11px; color:var(--blue); background:var(--blue-soft);
            padding:4px 8px; border-radius:6px; }
        .pcard .chip { font-weight:600; font-size:12px; }
        .pcard .name { font-weight:700; font-size:16px; line-height:1.4; color:var(--ink) !important; margin:0; }
        .pcard .desc { font-weight:400; font-size:13px; line-height:1.5; color:var(--muted) !important; margin:0;
            display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
        .pcard .price { font-weight:800; font-size:18px; color:var(--ink) !important; }
        .pcard .foot { font-weight:600; font-size:13px; color:var(--blue) !important; }

        /* ---- Detalhe / FAQ ---- */
        .detail-label { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em;
            color:var(--muted2); margin:18px 0 6px 0; }
        .faq-q { font-weight:700; font-size:15px; color:var(--ink); margin-bottom:2px; }
        .faq-a { color:#374151; font-size:14px; line-height:1.6; margin-bottom:14px; }

        /* ---- Cards da página Sobre ---- */
        .about-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            padding:28px 32px; box-shadow:var(--shadow); }
        .about-row { padding-bottom:18px; margin-bottom:18px; border-bottom:1px solid #f1f5f9; }
        .about-row:last-child { border-bottom:none; padding-bottom:0; margin-bottom:0; }
        .about-row .t { font-weight:700; font-size:16px; color:var(--ink); }
        .about-row .b { font-weight:400; font-size:14px; line-height:1.6; color:var(--muted); }
        </style>
        """
    )


# --------------------------------------------------------------------------- #
# Navegação (sidebar)
# --------------------------------------------------------------------------- #
# (rótulo, ícone Material line-style) — renderizado via parâmetro `icon` do st.button.
PAGES = [
    ("Home", ":material/home:"),
    ("Produtos", ":material/inventory_2:"),
    ("Sobre", ":material/info:"),
]


def sidebar_nav():
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    with st.sidebar:
        st.markdown(
            """
            <div class="sb-brand">
              <div class="sb-logo">S</div>
              <div>
                <div class="t">Catálogo SAC</div>
                <div class="s">Central de produtos</div>
              </div>
            </div>
            <div class="sb-caption">Navegação</div>
            """,
            unsafe_allow_html=True,
        )
        for nome, icone in PAGES:
            ativo = st.session_state.page == nome
            if st.button(
                nome,
                icon=icone,
                key=f"nav_{nome}",
                type="primary" if ativo else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = nome
                st.rerun()

        st.markdown(
            """
            <div class="sb-help">
              <div class="h">Precisa de ajuda?</div>
              <div class="p">Fale com o suporte para tirar dúvidas sobre produtos.</div>
              <a href="#">Abrir chamado →</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------- #
# Topbar (busca + sino + avatar)
# --------------------------------------------------------------------------- #
def topbar():
    col_search, col_user = st.columns([5, 4])
    with col_search:
        termo = st.text_input(
            "Buscar",
            key="topbar_search",
            placeholder="Buscar produtos por nome ou SKU…",
            label_visibility="collapsed",
        )
    with col_user:
        st.markdown(
            """
            <div class="topbar-user">
              <div class="tb-bell">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
                  <path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
              </div>
              <div class="tb-avatar">SA</div>
              <div>
                <div class="tb-name">Equipe SAC</div>
                <div class="tb-role">Atendimento</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # "Ao digitar, já leva pro resultado": se buscar a partir da Home, vai pra Produtos.
    if termo and termo.strip() and st.session_state.get("page") == "Home":
        st.session_state.page = "Produtos"
        st.rerun()
    return (termo or "").strip()


# --------------------------------------------------------------------------- #
# Detalhe de produto
# --------------------------------------------------------------------------- #
def render_detalhe(det):
    """Página de detalhe. `det`: {nome, sku, sku_raw, video_url, descricao,
    faqs:[{id,pergunta,resposta}], id, editable}."""
    col_back, col_edit = st.columns([3, 1])
    with col_back:
        if st.button("← Voltar para a lista", key="det_back"):
            st.session_state.pop("sel", None)
            st.session_state.pop("edit_mode", None)
            st.rerun()
    with col_edit:
        em = st.session_state.get("edit_mode", False)
        if st.button("Fechar edição" if em else "✏️ Editar", key="det_edit",
                     type="primary" if not em else "secondary", use_container_width=True):
            st.session_state.edit_mode = not em
            st.rerun()

    st.markdown(f"<div class='page-title'>{html.escape(det.get('nome') or '')}</div>", unsafe_allow_html=True)
    if det.get("sku"):
        st.markdown(f"<div class='page-sub'>{html.escape(det['sku'])}</div>", unsafe_allow_html=True)

    if st.session_state.get("edit_mode"):
        _render_edicao(det)
        return

    video_url = det.get("video_url")
    if video_url:
        st.markdown("<div class='detail-label'>Vídeo do produto</div>", unsafe_allow_html=True)
        if youtube_id(video_url) or video_url.startswith("http"):
            st.video(video_url)
        else:
            st.markdown(f"[Abrir vídeo]({video_url})")

    if det.get("descricao"):
        st.markdown("<div class='detail-label'>Descrição do produto</div>", unsafe_allow_html=True)
        st.markdown(det["descricao"])

    faqs = det.get("faqs") or []
    if faqs:
        st.markdown("<div class='detail-label'>Perguntas frequentes</div>", unsafe_allow_html=True)
        for f in faqs:
            st.markdown(
                f"<div class='faq-q'>{html.escape(f['pergunta'])}</div>"
                f"<div class='faq-a'>{html.escape(f['resposta'])}</div>",
                unsafe_allow_html=True,
            )


def _render_edicao(det):
    """Formulário de edição do produto + gerenciamento do FAQ."""
    editable = det.get("editable", False)
    pid = det.get("id")
    if not editable:
        st.info("Este é um produto de exemplo. Conecte o banco para editar produtos reais — "
                "o formulário abaixo é apenas uma prévia.")

    # ---- Dados do produto ----
    st.markdown("<div class='detail-label'>Editar produto</div>", unsafe_allow_html=True)
    with st.form(f"edit_prod_{pid or 'demo'}"):
        nome = st.text_input("Nome", value=det.get("nome") or "")
        sku = st.text_input("SKU", value=det.get("sku_raw") or "")
        video_url = st.text_input("Link do vídeo (YouTube)", value=det.get("video_url") or "")
        descricao = st.text_area("Descrição do produto", value=det.get("descricao") or "", height=140)
        if st.form_submit_button("Salvar alterações", type="primary"):
            if not nome.strip():
                st.warning("O nome é obrigatório.")
            elif not editable:
                st.info("Prévia — conecte o banco para salvar.")
            else:
                try:
                    atualizar_produto(pid, nome.strip(), sku.strip(), video_url.strip(), descricao.strip())
                    st.success("Produto atualizado.")
                    st.session_state.edit_mode = False
                    st.rerun()
                except psycopg2.errors.UniqueViolation:
                    st.error("Já existe um produto com esse SKU.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ---- Perguntas do FAQ ----
    st.markdown("<div class='detail-label'>Perguntas do FAQ</div>", unsafe_allow_html=True)
    faqs = det.get("faqs") or []
    if not faqs:
        st.caption("Nenhuma pergunta cadastrada ainda.")
    for i, f in enumerate(faqs):
        fid = f.get("id")
        with st.form(f"edit_faq_{fid or i}"):
            pergunta = st.text_input("Pergunta", value=f.get("pergunta", ""), key=f"q_{fid or i}")
            resposta = st.text_area("Resposta", value=f.get("resposta", ""), key=f"a_{fid or i}", height=90)
            c_save, c_del = st.columns(2)
            salvar = c_save.form_submit_button("Salvar", type="primary")
            excluir = c_del.form_submit_button("Excluir")
            if salvar:
                if not editable:
                    st.info("Prévia — conecte o banco para salvar.")
                elif not pergunta.strip() or not resposta.strip():
                    st.warning("Preencha pergunta e resposta.")
                else:
                    try:
                        atualizar_faq(fid, pergunta.strip(), resposta.strip())
                        st.success("Pergunta atualizada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
            if excluir:
                if not editable:
                    st.info("Prévia — conecte o banco para excluir.")
                else:
                    try:
                        deletar_faq(fid)
                        st.success("Pergunta excluída.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

    # ---- Nova pergunta ----
    with st.form(f"add_faq_{pid or 'demo'}", clear_on_submit=True):
        st.caption("Adicionar pergunta")
        nova_q = st.text_input("Pergunta", key=f"newq_{pid or 'demo'}")
        nova_a = st.text_area("Resposta", key=f"newa_{pid or 'demo'}", height=90)
        if st.form_submit_button("Adicionar pergunta", type="primary"):
            if not editable:
                st.info("Prévia — conecte o banco para adicionar.")
            elif not nova_q.strip() or not nova_a.strip():
                st.warning("Preencha pergunta e resposta.")
            else:
                try:
                    inserir_faq(pid, nova_q.strip(), nova_a.strip())
                    st.success("Pergunta adicionada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar: {e}")


# Produtos de exemplo — usados para visualizar o layout e a página de detalhe
# quando o banco não está conectado ou o catálogo está vazio. "depois mudamos".
_DEMO_VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
SAMPLE_PRODUCTS = [
    {"category": "Eletroportáteis", "name": "Cafeteira Prime X200",
     "desc": "Cafeteira automática com moedor integrado.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Cafeteira automática com moedor de grãos integrado, reservatório de 1,8 L "
                  "e painel digital. Prepara espresso, cappuccino e café coado.",
     "faqs": [
         {"pergunta": "Como faço a primeira limpeza?", "resposta": "Rode dois ciclos só com água antes do primeiro café."},
         {"pergunta": "Posso usar café já moído?", "resposta": "Sim, use o compartimento de pó e desative o moedor no painel."},
     ]},
    {"category": "Áudio", "name": "Fone NoiseZero Pro",
     "desc": "Cancelamento ativo e 30h de bateria.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Fone over-ear com cancelamento ativo de ruído, até 30h de bateria e "
                  "conexão Bluetooth 5.3 com multiponto.",
     "faqs": [
         {"pergunta": "Conecta em dois aparelhos ao mesmo tempo?", "resposta": "Sim, o multiponto permite dois dispositivos simultâneos."},
         {"pergunta": "Quanto tempo para carregar?", "resposta": "Cerca de 2 horas; 10 min dão ~4h de uso."},
     ]},
    {"category": "Casa", "name": "Aspirador Robô Aria",
     "desc": "Mapeamento a laser e esvaziamento automático.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Robô aspirador com mapeamento a laser (LiDAR), base de esvaziamento "
                  "automático e controle pelo aplicativo.",
     "faqs": [
         {"pergunta": "Ele sobe em tapetes?", "resposta": "Sim, identifica tapetes e aumenta a sucção automaticamente."},
         {"pergunta": "Preciso de wi-fi?", "resposta": "Só para o app; a limpeza funciona pelo botão sem internet."},
     ]},
    {"category": "Informática", "name": 'Monitor UltraView 27"',
     "desc": "Painel IPS 2K com 165Hz.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Monitor de 27\" com painel IPS 2K (2560×1440), 165Hz e suporte "
                  "ajustável em altura e inclinação.",
     "faqs": [
         {"pergunta": "Tem entrada HDMI 2.1?", "resposta": "Possui HDMI 2.0 e DisplayPort 1.4."},
         {"pergunta": "O suporte é VESA?", "resposta": "Sim, compatível com suporte VESA 100×100."},
     ]},
    {"category": "Wearables", "name": "Smartwatch Pulse 5",
     "desc": "GPS, oximetria e resistência à água.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Smartwatch com GPS integrado, medição de oxigenação (SpO2), "
                  "monitor de sono e resistência à água 5ATM.",
     "faqs": [
         {"pergunta": "Posso nadar com ele?", "resposta": "Sim, resiste a 5ATM (piscina). Evite mergulho."},
         {"pergunta": "Funciona com iPhone?", "resposta": "Sim, com Android e iOS pelo aplicativo."},
     ]},
    {"category": "Informática", "name": "Teclado Mecânico Lumen",
     "desc": "Switches silenciosos e RGB por tecla.",
     "video_url": _DEMO_VIDEO,
     "descricao": "Teclado mecânico com switches silenciosos, iluminação RGB por tecla "
                  "e estrutura em alumínio.",
     "faqs": [
         {"pergunta": "Dá para trocar os switches?", "resposta": "Sim, é hot-swap: troque sem solda."},
         {"pergunta": "Como mudo a cor do RGB?", "resposta": "Use Fn + as teclas de seta ou o software."},
     ]},
]


def produto_display(prod):
    """Mapeia um produto real do banco para os campos visuais do card."""
    manual = (prod.get("manual_texto") or "").strip()
    return {
        "href": f"?produto={prod['id']}",
        "photo": youtube_thumbnail(prod.get("video_url")),
        "category": prod.get("sku") or "Catálogo",
        "name": prod.get("nome") or "",
        "desc": manual[:110] if manual else "Consulte vídeo e FAQ nos detalhes.",
    }


def product_card(d):
    """Card de produto. Todo o card é um link que abre a página de detalhe."""
    href = d.get("href") or "#"
    photo = d.get("photo")
    if photo:
        photo_html = f"<div class='photo' style=\"background-image:url('{html.escape(photo)}')\"></div>"
    else:
        photo_html = "<div class='photo'>foto do produto</div>"

    cat = html.escape(d.get("category") or "")
    nome = html.escape(d.get("name") or "")
    desc = html.escape(d.get("desc") or "")

    st.markdown(
        f"""
        <a href="{href}" target="_self" class="pcard-link">
          <div class="pcard">
            {photo_html}
            <div class="body">
              <div class="row">
                <span class="cat">{cat}</span>
              </div>
              <p class="name">{nome}</p>
              <p class="desc">{desc}</p>
              <div class="row" style="margin-top:8px; justify-content:flex-end;">
                <span class="foot">Detalhes →</span>
              </div>
            </div>
          </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def grid_produtos(produtos, db_error, termo):
    # Sem banco ou catálogo vazio (sem busca): mostra o layout com exemplos.
    if db_error or (not produtos and not termo):
        st.caption("Exibindo produtos de exemplo — conecte o banco (`.streamlit/secrets.toml`) "
                   "e cadastre produtos para ver os reais.")
        displays = [
            {"href": f"?demo={i}", "photo": None, "category": s["category"],
             "name": s["name"], "desc": s["desc"]}
            for i, s in enumerate(SAMPLE_PRODUCTS)
        ]
    elif not produtos:
        st.info(f"Nenhum produto encontrado para “{termo}”.")
        return
    else:
        displays = [produto_display(p) for p in produtos]

    cols = st.columns(3)
    for i, d in enumerate(displays):
        with cols[i % 3]:
            product_card(d)


# --------------------------------------------------------------------------- #
# Páginas
# --------------------------------------------------------------------------- #
def page_home():
    # Container estilizado como o card com gradiente (permite pôr o botão DENTRO).
    with st.container(key="hero_box"):
        c_txt, c_art = st.columns([2, 1], vertical_alignment="center")
        with c_txt:
            st.html(
                """
                <div class="hero-txt">
                  <span class="badge">Central de Atendimento</span>
                  <h1>Encontre qualquer produto em segundos</h1>
                  <p>Consulte vídeos de montagem, manuais e dúvidas frequentes de
                  todo o catálogo em um só lugar.</p>
                </div>
                """
            )
            if st.button("Ver catálogo completo", key="hero_cta"):
                st.session_state.page = "Produtos"
                st.rerun()
        with c_art:
            # st.markdown (não st.html) porque o st.html remove o <svg> na sanitização.
            st.markdown(
                """
                <div class="hero-art">
                  <svg width="76" height="76" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="1.3" stroke-linecap="round"
                    stroke-linejoin="round">
                    <path d="M21 8 12 3 3 8v8l9 5 9-5Z"/>
                    <path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>
                  </svg>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Stat cards (contagens reais)
    try:
        s = get_stats()
        stats = [
            ("Produtos cadastrados", s["produtos"]),
            ("Vídeos disponíveis", s["videos"]),
            ("Perguntas no FAQ", s["faqs"]),
        ]
    except Exception:
        stats = [("Produtos cadastrados", "–"), ("Vídeos disponíveis", "–"), ("Perguntas no FAQ", "–")]

    st.write("")
    cols = st.columns(3)
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(
                f"<div class='stat'><div class='l'>{label}</div><div class='v'>{value}</div></div>",
                unsafe_allow_html=True,
            )

    # Como funciona
    st.write("")
    st.markdown("<div class='sec-title'>Como funciona</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Três passos para atender qualquer solicitação.</div>", unsafe_allow_html=True)
    steps = [
        ("1", "Busque o produto", "Use a busca no topo para localizar o item por nome ou SKU."),
        ("2", "Veja vídeo e manual", "Abra o produto e consulte o vídeo de montagem e o manual."),
        ("3", "Consulte o FAQ", "Encontre respostas prontas para as dúvidas mais comuns."),
    ]
    cols = st.columns(3)
    for col, (n, t, b) in zip(cols, steps):
        with col:
            st.markdown(
                f"<div class='step'><div class='n'>{n}</div><div class='t'>{t}</div><div class='b'>{b}</div></div>",
                unsafe_allow_html=True,
            )


def page_produtos(termo):
    # Se um produto está selecionado, mostra a página de detalhe.
    if st.session_state.get("sel"):
        kind, ref = st.session_state.sel
        if kind == "demo":
            if 0 <= ref < len(SAMPLE_PRODUCTS):
                s = SAMPLE_PRODUCTS[ref]
                render_detalhe({
                    "id": None, "editable": False,
                    "nome": s["name"], "sku": s["category"], "sku_raw": s["category"],
                    "video_url": s["video_url"], "descricao": s["descricao"], "faqs": s["faqs"],
                })
                return
            st.session_state.pop("sel", None)
        else:
            try:
                produtos = buscar_produtos("")
            except Exception as e:
                st.error(f"Erro ao consultar o banco: {e}")
                return
            prod = next((p for p in produtos if p["id"] == ref), None)
            if prod:
                render_detalhe({
                    "id": prod["id"], "editable": True,
                    "nome": prod.get("nome"),
                    "sku": f"SKU: {prod['sku']}" if prod.get("sku") else "",
                    "sku_raw": prod.get("sku") or "",
                    "video_url": prod.get("video_url"),
                    "descricao": prod.get("manual_texto"),
                    "faqs": buscar_faq(prod["id"]),
                })
                return
            st.session_state.pop("sel", None)

    # Busca única (usada no header e no grid).
    db_error = False
    try:
        produtos = buscar_produtos(termo)
    except Exception:
        produtos, db_error = None, True

    if db_error:
        sub = f"{len(SAMPLE_PRODUCTS)} itens no catálogo (exemplo)."
    else:
        n = len(produtos)
        sub = f"{n} {'item' if n == 1 else 'itens'} no catálogo."

    head_l, head_r = st.columns([4, 1])
    with head_l:
        st.markdown("<div class='page-title'>Produtos</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='page-sub'>{sub}</div>", unsafe_allow_html=True)
    with head_r:
        st.write("")
        if st.button("＋ Novo produto", key="toggle_cad", type="primary", use_container_width=True):
            st.session_state.show_cad = not st.session_state.get("show_cad", False)

    if st.session_state.get("show_cad", False):
        _render_cadastro()

    st.write("")
    grid_produtos(produtos, db_error, termo)


def _render_cadastro():
    with st.expander("Novo produto", expanded=True):
        with st.form("form_produto", clear_on_submit=True):
            nome = st.text_input("Nome *")
            sku = st.text_input("SKU")
            video_url = st.text_input("Link do vídeo (YouTube)")
            manual_texto = st.text_area("Descrição do produto", height=140)
            if st.form_submit_button("Salvar produto", type="primary"):
                if not nome.strip():
                    st.warning("O nome é obrigatório.")
                else:
                    try:
                        inserir_produto(nome.strip(), sku.strip(), video_url.strip(), manual_texto.strip())
                        st.success(f"Produto “{nome.strip()}” cadastrado.")
                    except psycopg2.errors.UniqueViolation:
                        st.error("Já existe um produto com esse SKU.")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    with st.expander("Adicionar pergunta/resposta a um produto"):
        try:
            produtos = buscar_produtos("")
        except Exception as e:
            st.error(f"Erro ao carregar produtos: {e}")
            produtos = []

        if not produtos:
            st.caption("Cadastre um produto primeiro.")
        else:
            opcoes = {f"{p['nome']} ({p['sku'] or 'sem SKU'})": p["id"] for p in produtos}
            with st.form("form_faq", clear_on_submit=True):
                escolha = st.selectbox("Produto", list(opcoes.keys()))
                pergunta = st.text_input("Pergunta")
                resposta = st.text_area("Resposta", height=100)
                if st.form_submit_button("Adicionar ao FAQ", type="primary"):
                    if not pergunta.strip() or not resposta.strip():
                        st.warning("Preencha pergunta e resposta.")
                    else:
                        try:
                            inserir_faq(opcoes[escolha], pergunta.strip(), resposta.strip())
                            st.success("Pergunta adicionada ao FAQ.")
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")


def page_sobre():
    st.markdown("<div class='page-title'>Sobre o Catálogo SAC</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-sub'>Central única para a equipe de atendimento consultar vídeos, "
        "manuais e dúvidas frequentes dos produtos sem sair do fluxo de trabalho.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    rows = [
        ("O que é", "O Catálogo SAC centraliza vídeos de montagem, manuais e FAQ de todos os "
                    "produtos, eliminando planilhas e consultas dispersas durante o atendimento."),
        ("Para quem", "Atendentes e o time de pós-venda que precisam de informação confiável e "
                      "rápida enquanto falam com o cliente."),
        ("Como cadastrar um produto", "Na página Produtos, clique em ＋ Novo produto e preencha nome, "
                                      "SKU, link do vídeo e o manual. Use o expander de FAQ para adicionar "
                                      "perguntas e respostas a um produto existente."),
    ]
    inner = "".join(
        f"<div class='about-row'><div class='t'>{t}</div><div class='b'>{b}</div></div>"
        for t, b in rows
    )
    inner += "<div class='about-row'><div class='b'>Dúvidas? Fale com <b>[seu nome / contato]</b>.</div></div>"
    st.markdown(f"<div class='about-card'>{inner}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def _handle_query_params():
    """Clique num card recarrega a página com ?produto=ID ou ?demo=INDEX.
    Como o reload zera o session_state, lemos o parâmetro aqui (antes do roteamento)
    para reabrir a página de detalhe correta."""
    qp = st.query_params
    if "produto" in qp:
        try:
            st.session_state.sel = ("real", int(qp["produto"]))
            st.session_state.page = "Produtos"
        except (ValueError, TypeError):
            pass
        st.query_params.clear()
    elif "demo" in qp:
        try:
            st.session_state.sel = ("demo", int(qp["demo"]))
            st.session_state.page = "Produtos"
        except (ValueError, TypeError):
            pass
        st.query_params.clear()


def main():
    inject_css()
    _handle_query_params()
    sidebar_nav()
    termo = topbar()

    page = st.session_state.get("page", "Home")
    if page == "Home":
        page_home()
    elif page == "Produtos":
        page_produtos(termo)
    elif page == "Sobre":
        page_sobre()


if __name__ == "__main__":
    main()
