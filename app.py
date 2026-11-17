import streamlit as st
import json
import os
import requests
from streamlit_searchbox import st_searchbox
import stripe
import spotipy
from spotipy.oauth2 import SpotifyOAuth

st.set_page_config(page_title="Jukebox | Apple Experience", page_icon="🎵", layout="centered")

# Configurações seguras via Streamlit Secrets
SPOTIFY_CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_REDIRECT_URI = "https://jukebox.streamlit.app/" # Substitui pelo teu URL final do Streamlit se necessário

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #f5f5f7;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    h1, h2, h3 {
        color: #f5f5f7 !important;
        font-weight: 600;
        letter-spacing: -0.022em;
    }

    div.stTabs [data-baseweb="tab-panel"] {
        background: rgba(28, 28, 30, 0.75);
        padding: 32px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(40px);
        -webkit-backdrop-filter: blur(40px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        margin-top: 12px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #121214;
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 10px;
        color: #86868b;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.25s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c2c2e !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .stButton button {
        background: linear-gradient(180deg, #007aff 0%, #0062cc 100%);
        color: white;
        border-radius: 980px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        font-weight: 500;
        letter-spacing: -0.01em;
        padding: 0.65rem 1.4rem;
        transition: all 0.25s cubic-bezier(0.25, 1, 0.5, 1);
        box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
    }
    .stButton button:hover {
        background: linear-gradient(180deg, #1a88ff 0%, #007aff 100%);
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.5);
        transform: translateY(-1px);
    }

    .stTextInput input, .stSelectbox select {
        background-color: #1c1c1e !important;
        color: #f5f5f7 !important;
        border-radius: 12px !important;
        border: 1px solid #38383a !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s ease;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #007aff !important;
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.25);
    }
    </style>
""", unsafe_allow_html=True)

FICHEIRO_DADOS = "dados_jukebox.json"

def carregar_dados():
    if os.path.exists(FICHEIRO_DADOS):
        with open(FICHEIRO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"votos": [], "pedidos_premium": [], "dedicatorias": []}

def guardar_dados(dados):
    with open(FICHEIRO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

dados = carregar_dados()
if "dedicatorias" not in dados:
    dados["dedicatorias"] = []

# Chave do Stripe carregada de forma segura
stripe.api_key = st.secrets["STRIPE_API_KEY"]

def pesquisar_artistas_itunes(termo: str):
    if not termo or len(termo.strip()) < 2:
        return []
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": termo, "entity": "musicArtist", "limit": 6}
        resposta = requests.get(url, params=params, timeout=3).json()
        sugestoes = []
        for item in resposta.get("results", []):
            nome = item.get("artistName")
            if nome and nome not in sugestoes:
                sugestoes.append(nome)
        return sugestoes
    except Exception:
        return []

def pesquisar_musicas_itunes(termo: str):
    if not termo or len(termo.strip()) < 2:
        return []
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": termo, "entity": "song", "limit": 8}
        resposta = requests.get(url, params=params, timeout=3).json()
        sugestoes = []
        for item in resposta.get("results", []):
            nome_musica = item.get("trackName")
            nome_artista = item.get("artistName")
            if nome_musica and nome_artista:
                formatado = f"{nome_musica} — {nome_artista}"
                if formatado not in sugestoes:
                    sugestoes.append(formatado)
        return sugestoes
    except Exception:
        return []

def adicionar_ao_spotify(termo_musica):
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-modify-playback-state user-read-playback-state",
            cache_path=".spotify_tokenache"
        ))
        
        resultado = sp.search(q=termo_musica, type='track', limit=1)
        tracks = resultado.get('tracks', {}).get('items', [])
        
        if tracks:
            track_uri = tracks[0]['uri']
            sp.add_to_queue(track_uri)
            return True
    except Exception as e:
        print(f"Erro Spotify: {e}")
    return False

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 2.5rem; font-weight: 700; letter-spacing: -0.03em;'>Jukebox.</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #86868b; font-size: 1.15rem; margin-bottom: 35px; font-weight: 400;'>A atmosfera sonora perfeita para a tua noite.</p>", unsafe_allow_html=True)

bar_selecionado = st.selectbox("📍 Estabelecimento Ativo:", ["Bar Central - Lisboa", "Discoteca 404 - Porto"])

base_url_app = "https://jukebox.streamlit.app/"

query_params = st.query_params
if query_params.get("pagamento") == "sucesso":
    nome_retorno = query_params.get("nome", "Cliente")
    musica_retorno = query_params.get("musica", "Música Pedida")
    dedicatoria_retorno = query_params.get("dedicatoria", "")
    bar_retorno = query_params.get("bar", bar_selecionado)
    
    ja_existe = any(p["nome"] == nome_retorno and p["musica"] == musica_retorno for p in dados["pedidos_premium"])
    if not ja_existe:
        dados["pedidos_premium"].append({"bar": bar_retorno, "nome": nome_retorno, "musica": musica_retorno})
        if dedicatoria_retorno:
            dados["dedicatorias"].append({"bar": bar_retorno, "remetente": nome_retorno, "destinatario": dedicatoria_retorno, "musica": musica_retorno})
        guardar_dados(dados)
        
        adicionar_ao_spotify(musica_retorno)
    
    st.balloons()
    st.success(f"Pagamento processado! '{musica_retorno}' foi integrada na fila do Spotify e do bar.")
    
    if dedicatoria_retorno:
        texto_voz = f"Esta música é dedicada a {dedicatoria_retorno}!"
        st.markdown(f"""
            <script>
                const synth = window.speechSynthesis;
                const utterance = new SpeechSynthesisUtterance("{texto_voz}");
                utterance.lang = 'pt-PT';
                utterance.rate = 1.0;
                synth.speak(utterance);
            </script>
        """, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🎤 O que queres ouvir hoje?", "⚡ Prioritário (1,00€)", "💌 Dedicatórias", "🎛️ Consola do Bar"])

with tab1:
    st.subheader("O que queres ouvir hoje?")
    st.markdown("<p style='color: #86868b; font-size: 0.95rem; margin-bottom: 20px;'>Indica até 3 artistas que gostarias de ouvir no espaço.</p>", unsafe_allow_html=True)
    nome_utilizador = st.text_input("O teu nome:")
    st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
    
    artista_1 = st_searchbox(pesquisar_artistas_itunes, key="art_1", placeholder="Primeiro artista...")
    artista_2 = st_searchbox(pesquisar_artistas_itunes, key="art_2", placeholder="Segundo artista...")
    artista_3 = st_searchbox(pesquisar_artistas_itunes, key="art_3", placeholder="Terceiro artista...")
    
    st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
    if st.button("Submeter Preferências", type="primary"):
        artistas_escolhidos = [a for a in [artista_1, artista_2, artista_3] if a]
        if nome_utilizador and artistas_escolhidos:
            dados["votos"].append({"bar": bar_selecionado, "nome": nome_utilizador, "artistas": artistas_escolhidos})
            guardar_dados(dados)
            st.success("Preferências musicais registadas com sucesso.")
        else:
            st.warning("Insere o teu nome e seleciona pelo menos 1 artista.")

with tab2:
    st.subheader("Reprodução Imediata")
    st.markdown("<p style='color: #86868b; font-size: 0.95rem; margin-bottom: 20px;'>Salta diretamente para o topo da fila de reprodução através de pagamento seguro.</p>", unsafe_allow_html=True)
    nome_premium = st.text_input("O teu nome:", key="p_nome")
    
    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
    musica_premium = st_searchbox(
        pesquisar_musicas_itunes, 
        key="p_musica_search", 
        placeholder="Escreve o nome da música ou artista..."
    )
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    if st.button("💳 Continuar para Checkout Seguro (1,00€)", type="primary"):
        if nome_premium and musica_premium:
            try:
                from urllib.parse import quote
                url_sucesso = f"{base_url_app}?pagamento=sucesso&nome={quote(nome_premium)}&musica={quote(musica_premium)}&bar={quote(bar_selecionado)}"
                
                checkout_session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': f'Furar Fila: {musica_premium} (por {nome_premium})',
                                'tax_code': 'txcd_10000000',
                            },
                            'unit_amount': 100,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=url_sucesso,
                    cancel_url=f"{base_url_app}?pagamento=cancelado",
                    managed_payments={'enabled': False},
                )
                link_url = checkout_session.url
                st.markdown(f"### [👉 Abrir Sessão de Pagamento Seguro]({link_url})", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao comunicar com o Stripe: {e}")
        else:
            st.warning("Preenche o teu nome e seleciona a música pretendida.")

with tab3:
    st.subheader("💌 Enviar Dedicatória Musical")
    st.markdown("<p style='color: #86868b; font-size: 0.95rem; margin-bottom: 20px;'>Surpreende alguém especial! Paga 1,00€ para furar a fila e faz com que o sistema anuncie a tua dedicatória em voz alta no bar.</p>", unsafe_allow_html=True)
    
    nome_ded = st.text_input("O teu nome:", key="d_nome")
    destinatario_ded = st.text_input("Nome de quem vai receber a dedicatória:", key="d_dest")
    
    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
    musica_ded = st_searchbox(
        pesquisar_musicas_itunes, 
        key="d_musica_search", 
        placeholder="Escreve a música da dedicatória..."
    )
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    if st.button("💳 Pagar 1,00€ e Enviar Dedicatória", type="primary"):
        if nome_ded and destinatario_ded and musica_ded:
            try:
                from urllib.parse import quote
                url_sucesso = f"{base_url_app}?pagamento=sucesso&nome={quote(nome_ded)}&musica={quote(musica_ded)}&dedicatoria={quote(destinatario_ded)}&bar={quote(bar_selecionado)}"
                
                checkout_session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': f'Dedicatória para {destinatario_ded}: {musica_ded}',
                                'tax_code': 'txcd_10000000',
                            },
                            'unit_amount': 100,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=url_sucesso,
                    cancel_url=f"{base_url_app}?pagamento=cancelado",
                    managed_payments={'enabled': False},
                )
                link_url = checkout_session.url
                st.markdown(f"### [👉 Abrir Sessão de Pagamento da Dedicatória]({link_url})", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao comunicar com o Stripe: {e}")
        else:
            st.warning("Preenche o teu nome, o destinatário e escolhe a música.")

with tab4:
    st.subheader("Painel de Controlo Restrito")
    st.markdown("<p style='color: #86868b; font-size: 0.95rem; margin-bottom: 20px;'>Área exclusiva para gestão de sala e DJ residentes.</p>", unsafe_allow_html=True)
    palavra_passe = st.text_input("Código de Acesso:", type="password")
    if palavra_passe == "admin123":
        st.success("Sessão de administração autenticada.")
        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ⚡ Pedidos e Dedicatórias")
            pedidos_bar = [p for p in dados["pedidos_premium"] if p["bar"] == bar_selecionado]
            if pedidos_bar:
                for p in pedidos_bar:
                    st.info(f"{p['musica']} — *{p['nome']}*")
            else:
                st.write("Nenhum pedido prioritário ativo.")
        with col2:
            st.markdown("#### 🤖 Tendências da Sala")
            votos_bar = [v for v in dados["votos"] if v["bar"] == bar_selecionado]
            if votos_bar:
                todos = [a for v in votos_bar for a in v["artistas"]]
                contagem = {art: todos.count(art) for art in set(todos)}
                for art, total in sorted(contagem.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{art}** — {total} voto(s)")
            else:
                st.write("Sem dados analíticos recolhidos.")
    elif palavra_passe:
        st.error("Código de acesso incorreto.")
