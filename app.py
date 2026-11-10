import streamlit as st
import json
import os

# --- CONFIGURAÇÃO DA PÁGINA (Otimizada para Telemóvel) ---
st.set_page_config(
    page_title="Jukebox do Bar 🎵",
    page_icon="🎶",
    layout="centered"
)

# Estilo CSS para otimizar o visual no telemóvel
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

FICHEIRO_DADOS = "dados_jukebox.json"

# Carregar dados locais (votos e pedidos pagos)
if os.path.exists(FICHEIRO_DADOS):
    with open(FICHEIRO_DADOS, "r", encoding="utf-8") as f:
        dados = json.load(f)
else:
    dados = {"votos": [], "pedidos_premium": []}

# --- CABEÇALHO DA APP ---
st.title("🎶 Jukebox Digital")
st.markdown("### Escolhe os teus artistas ou pede uma música já!")

# Seleção do Bar
bar_selecionado = st.selectbox("📍 Estabelecimento:", ["Bar Central - Lisboa", "Discoteca 404 - Porto"])

tab1, tab2, tab3 = st.tabs(["🎤 Escolher 5 Artistas", "⚡ Furar Fila (1€)", "🎛️ Painel do Bar"])

# --- TAB 1: ESCOLHER 5 ARTISTAS ---
with tab1:
    st.subheader("Indica até 5 artistas que gostarias de ouvir hoje:")
    
    with st.form("form_escolha_5"):
        nome_utilizador = st.text_input("O teu nome:")
        
        st.markdown("---")
        artista_1 = st.text_input("Artista 1:", placeholder="Ex: Daft Punk")
        artista_2 = st.text_input("Artista 2:", placeholder="Ex: The Weeknd")
        artista_3 = st.text_input("Artista 3:", placeholder="Ex: Arctic Monkeys")
        artista_4 = st.text_input("Artista 4:", placeholder="Ex: David Guetta")
        artista_5 = st.text_input("Artista 5:", placeholder="Ex: Rihanna")
        
        submeter_escolha = st.form_submit_button("Submeter os meus 5 Artistas")
        
        if submeter_escolha:
            artistas_escolhidos = [a.strip() for a in [artista_1, artista_2, artista_3, artista_4, artista_5] if a.strip()]
            
            if nome_utilizador and artistas_escolhidos:
                dados["votos"].append({
                    "bar": bar_selecionado,
                    "nome": nome_utilizador,
                    "artistas": artistas_escolhidos
                })
                with open(FICHEIRO_DADOS, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=4)
                
                st.success(f"Obrigado {nome_utilizador}! Os teus {len(artistas_escolhidos)} artistas foram registados.")
            else:
                st.warning("Preenche o teu nome e pelo menos 1 artista.")

# --- TAB 2: PEDIDO PREMIUM (Furar Fila por 1€) ---
with tab2:
    st.subheader("⚡ Queres que a tua música toque JÁ?")
    st.markdown("Paga **1,00€** para saltar para o topo da fila de reprodução.")
    
    with st.form("form_premium"):
        nome_premium = st.text_input("O teu nome:", key="p_nome")
        musica_premium = st.text_input("Música exata (Nome + Artista):", key="p_musica", placeholder="Ex: Daft Punk - Get Lucky")
        
        pagar_e_tocar = st.form_submit_button("💳 Pagar 1,00€ e Tocar Já")
        
        if pagar_e_tocar:
            if nome_premium and musica_premium:
                dados["pedidos_premium"].append({
                    "bar": bar_selecionado, 
                    "nome": nome_premium, 
                    "musica": musica_premium,
                    "status": "A tocar em breve"
                })
                with open(FICHEIRO_DADOS, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=4)
                
                st.balloons()
                st.success(f"Pagamento simulado! A música **'{musica_premium}'** entrou na fila prioritária.")
            else:
                st.warning("Indica o teu nome e a música que queres ouvir.")

# --- TAB 3: PAINEL DO BAR / DJ (COM CURADORIA DE IA) ---
with tab3:
    st.subheader("🎛️ Gestão de Fila (Visão do DJ / Bar)")
    palavra_passe = st.text_input("Código de Acesso do Bar:", type="password")
    
    if palavra_passe == "admin123":
        st.success("Acesso autorizado.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ⚡ Pedidos Pagos (Fila Prioritária)")
            pedidos_bar = [p for p in dados["pedidos_premium"] if p["bar"] == bar_selecionado]
            if pedidos_bar:
                for idx, p in enumerate(pedidos_bar):
                    st.info(f"**{idx+1}.** {p['musica']} *(Pedida por: {p['nome']})*")
            else:
                st.write("Sem pedidos pagos no momento.")
                
        with col2:
            st.markdown("#### 🤖 Curadoria IA (Consenso da Sala)")
            votos_bar = [v for v in dados["votos"] if v["bar"] == bar_selecionado]
            
            if votos_bar:
                todos_artistas = []
                for v in votos_bar:
                    todos_artistas.extend(v["artistas"])
                
                contagem_artistas = {}
                for art in todos_artistas:
                    art_normalizado = art.title()
                    contagem_artistas[art_normalizado] = contagem_artistas.get(art_normalizado, 0) + 1
                
                artistas_ordenados = sorted(contagem_artistas.items(), key=lambda x: x[1], reverse=True)
                
                st.caption("Playlist de fundo gerada ao cruzar os gostos de todos os clientes:")
                for idx, (artista, total_votos) in enumerate(artistas_ordenados):
                    st.write(f"**{idx+1}. {artista}** — *(Preferência de {total_votos} cliente(s))*")
            else:
                st.write("Ainda não há dados suficientes para a IA calcular o consenso.")
    elif palavra_passe:
        st.error("Código incorreto.")
