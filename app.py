import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import (
    get_all_months,
    get_all_players,
    get_monthly_summary,
    get_player_history,
    get_matches_by_month
)

# Configuração da Página
st.set_page_config(
    page_title="CS2 - Gamers Club Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Moderna com tema Gamer
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff7700, #ffaa00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #9ca3af;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #1e222d;
        border: 1px solid #2e3546;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
    }
    .highlight-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-left: 4px solid #f97316;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Carrega jogadores e meses
players_df = get_all_players()
available_months = get_all_months()

if players_df.empty or not available_months:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados. Execute primeiro o coletor: `python collector.py`")
    st.stop()

# Jogador principal
main_player_row = players_df[players_df["is_main_user"] == 1]
main_nick = main_player_row.iloc[0]["nick"] if not main_player_row.empty else "KrannDy"
main_pid = int(main_player_row.iloc[0]["player_id"]) if not main_player_row.empty else 108698

# Sidebar
with st.sidebar:
    st.image("https://gcv1-assets.gamersclub.com.br/assets/images/perfil/icon-lobby.png", width=60)
    st.title("GC Analytics")
    st.caption(f"Painel de Estatísticas CS2 • **{main_nick}**")
    
    st.markdown("---")
    st.subheader("🗓️ Filtro de Período")
    
    selected_month = st.selectbox(
        "Selecione o Mês:",
        options=available_months,
        index=0 if len(available_months) > 0 else 0
    )
    
    st.markdown("---")
    st.markdown("### 👥 Squad Cadastrado")
    st.caption(f"Total de {len(players_df)} jogadores rastreados (você + {len(players_df)-1} companheiros).")
    
    with st.expander("Ver lista de jogadores"):
        for _, p in players_df.iterrows():
            tag = "🌟 (Você)" if p["is_main_user"] == 1 else ""
            st.write(f"- **{p['nick']}** (Lvl {p['level'] or '?'}) {tag}")

# Cabeçalho Principal
st.markdown(f"<div class='main-header'>Gamers Club Dashboard - CS2</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Análise mensal de desempenho individual e dos companheiros de equipe • Mês selecionado: <b>{selected_month}</b></div>", unsafe_allow_html=True)

# Abas do Dashboard
tab_overview, tab_squad, tab_maps, tab_history = st.tabs([
    "📊 Visão Geral do Jogador",
    "👥 Comparativo de Companheiros",
    "🗺️ Análise de Mapas",
    "📜 Partidas do Mês"
])

# ---------------------------------------------------------
# TAB 1: VISÃO GERAL DO JOGADOR PRINCIPAL
# ---------------------------------------------------------
with tab_overview:
    summary_df = get_monthly_summary(selected_month)
    user_row = summary_df[summary_df["player_id"] == main_pid]
    
    if user_row.empty:
        st.info(f"Sem partidas registradas para {main_nick} em {selected_month}.")
    else:
        u = user_row.iloc[0]
        
        # Cards de Métricas Principais
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Partidas</div>
                <div class='metric-value'>{int(u['matches'])}</div>
                <div class='metric-sub'>{int(u['wins'])}V - {int(u['loss'])}D</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Win Rate</div>
                <div class='metric-value'>{u['win_rate']:.1f}%</div>
                <div class='metric-sub'>Taxa de Vitória</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>KDR</div>
                <div class='metric-value'>{u['kdr']:.2f}</div>
                <div class='metric-sub'>Kills / Deaths</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>ADR Médio</div>
                <div class='metric-value'>{u['adr']:.1f}</div>
                <div class='metric-sub'>Dano por Round</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col5:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Kills / Mortes</div>
                <div class='metric-value'>{int(u['kills'])}</div>
                <div class='metric-sub'>{int(u['deaths'])} Mortes</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col6:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Headshot %</div>
                <div class='metric-value'>{u['hs_percent']:.0f}%</div>
                <div class='metric-sub'>KAST: {u['kast_percent']:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos de Evolução
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            st.subheader("📈 Evolução Histórica Mês a Mês")
            history_df = get_player_history(main_pid)
            
            if not history_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=history_df['month'], y=history_df['kdr'],
                    mode='lines+markers', name='KDR',
                    line=dict(color='#ff7700', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=history_df['month'], y=history_df['adr'] / 100.0,
                    mode='lines+markers', name='ADR (escala /100)',
                    line=dict(color='#38bdf8', width=2, dash='dot')
                ))
                fig.add_trace(go.Scatter(
                    x=history_df['month'], y=history_df['win_rate'] / 100.0,
                    mode='lines+markers', name='Win Rate % (/100)',
                    line=dict(color='#10b981', width=2)
                ))
                fig.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='#111827',
                    paper_bgcolor='#111827',
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados suficientes para histórico temporal.")

        with col_g2:
            st.subheader("🎯 Ocorrência de Tiros (Hitbox)")
            hitbox_data = {
                "Região": ["Cabeça", "Peito", "Estômago", "Braços", "Pernas"],
                "Tiros": [
                    u.get('hitbox_head', 0),
                    u.get('hitbox_chest', 0),
                    u.get('hitbox_stomach', 0),
                    u.get('hitbox_arms', 0),
                    u.get('hitbox_legs', 0)
                ]
            }
            hit_df = pd.DataFrame(hitbox_data)
            if hit_df["Tiros"].sum() > 0:
                fig_hit = px.pie(
                    hit_df, values="Tiros", names="Região",
                    hole=0.45,
                    color_discrete_sequence=['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']
                )
                fig_hit.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='#111827',
                    paper_bgcolor='#111827',
                    margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig_hit, use_container_width=True)
            else:
                st.info("Dados de Hitbox não disponíveis para este mês.")

# ---------------------------------------------------------
# TAB 2: COMPARATIVO DO SQUAD (COMPANHEIROS DE EQUIPE)
# ---------------------------------------------------------
with tab_squad:
    st.subheader(f"👥 Comparativo de Desempenho no Mês: {selected_month}")
    
    squad_df = summary_df[summary_df["matches"] > 0].copy()
    
    if squad_df.empty:
        st.info("Nenhum companheiro possui partidas registradas neste mês.")
    else:
        # Destaques do Mês
        best_adr = squad_df.loc[squad_df['adr'].idxmax()]
        best_kdr = squad_df.loc[squad_df['kdr'].idxmax()]
        most_matches = squad_df.loc[squad_df['matches'].idxmax()]
        
        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown(f"""
            <div class='highlight-card'>
                <b>🔥 Maior Dano (Top ADR):</b><br>
                <span style='font-size:1.3rem; font-weight:700; color:#ff7700;'>{best_adr['nick']}</span> — <b>{best_adr['adr']:.1f}</b> ADR ({int(best_adr['matches'])} partidas)
            </div>
            """, unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class='highlight-card'>
                <b>🎯 Maior K/D Ratio:</b><br>
                <span style='font-size:1.3rem; font-weight:700; color:#38bdf8;'>{best_kdr['nick']}</span> — <b>{best_kdr['kdr']:.2f}</b> KDR
            </div>
            """, unsafe_allow_html=True)
        with d3:
            st.markdown(f"""
            <div class='highlight-card'>
                <b>🎮 Mais Jogos no Mês:</b><br>
                <span style='font-size:1.3rem; font-weight:700; color:#10b981;'>{most_matches['nick']}</span> — <b>{int(most_matches['matches'])}</b> jogos ({most_matches['win_rate']:.1f}% Winrate)
            </div>
            """, unsafe_allow_html=True)
            
        # Gráficos Comparativos
        c_bar1, c_bar2 = st.columns(2)
        with c_bar1:
            fig_adr = px.bar(
                squad_df.sort_values(by="adr", ascending=True),
                x="adr", y="nick",
                orientation='h',
                title="Dano Médio por Round (ADR)",
                color="adr",
                color_continuous_scale="Oranges",
                text="adr"
            )
            fig_adr.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_adr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827')
            st.plotly_chart(fig_adr, use_container_width=True)
            
        with c_bar2:
            fig_kdr = px.bar(
                squad_df.sort_values(by="kdr", ascending=True),
                x="kdr", y="nick",
                orientation='h',
                title="Kill / Death Ratio (KDR)",
                color="kdr",
                color_continuous_scale="Blues",
                text="kdr"
            )
            fig_kdr.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_kdr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827')
            st.plotly_chart(fig_kdr, use_container_width=True)

        # Tabela Detalhada
        st.markdown("### 📋 Tabela Geral de Estatísticas do Squad")
        display_cols = ["nick", "matches", "wins", "loss", "win_rate", "kdr", "adr", "kills", "deaths", "hs_percent", "kast_percent"]
        renamed_cols = {
            "nick": "Jogador",
            "matches": "Partidas",
            "wins": "Vitórias",
            "loss": "Derrotas",
            "win_rate": "Win Rate (%)",
            "kdr": "K/D",
            "adr": "ADR",
            "kills": "Kills",
            "deaths": "Mortes",
            "hs_percent": "HS %",
            "kast_percent": "KAST %"
        }
        styled_table = squad_df[display_cols].rename(columns=renamed_cols).reset_index(drop=True)
        st.dataframe(styled_table, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: ANÁLISE DE MAPAS
# ---------------------------------------------------------
with tab_maps:
    st.subheader(f"🗺️ Desempenho por Mapa ({selected_month})")
    matches_df = get_matches_by_month(selected_month, main_pid)
    
    if matches_df.empty:
        st.info("Nenhuma partida com detalhes de mapa encontrada para este mês.")
    else:
        map_stats = matches_df.groupby("map").agg(
            total=('match_id', 'count'),
            wins=('win', 'sum')
        ).reset_index()
        map_stats['losses'] = map_stats['total'] - map_stats['wins']
        map_stats['win_rate'] = (map_stats['wins'] / map_stats['total'] * 100).round(1)
        map_stats = map_stats.sort_values(by="total", ascending=False)
        
        m_col1, m_col2 = st.columns([1, 1])
        with m_col1:
            fig_map_vol = px.bar(
                map_stats, x="map", y=["wins", "losses"],
                title="Vitórias e Derrotas por Mapa",
                color_discrete_map={"wins": "#10b981", "losses": "#ef4444"},
                barmode="stack"
            )
            fig_map_vol.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827')
            st.plotly_chart(fig_map_vol, use_container_width=True)
            
        with m_col2:
            fig_map_wr = px.bar(
                map_stats, x="map", y="win_rate",
                title="Taxa de Vitória (%) por Mapa",
                color="win_rate",
                color_continuous_scale="Tealgrn",
                text="win_rate"
            )
            fig_map_wr.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_map_wr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', yaxis_range=[0, 105])
            st.plotly_chart(fig_map_wr, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: PARTIDAS DO MÊS
# ---------------------------------------------------------
with tab_history:
    st.subheader(f"📜 Histórico de Jogos do Mês ({selected_month})")
    
    matches_df = get_matches_by_month(selected_month, main_pid)
    if matches_df.empty:
        st.info(f"Nenhuma partida listada para {selected_month}.")
    else:
        # Formata resultado
        matches_display = matches_df.copy()
        matches_display["resultado"] = matches_display["win"].apply(lambda w: "🏆 Vitória" if w == 1 else "❌ Derrota")
        matches_display["placar"] = matches_display.apply(lambda r: f"{r['score_a']} x {r['score_b']}", axis=1)
        matches_display["diff"] = matches_display["rating_diff"].apply(lambda d: f"+{d}" if d > 0 else str(d))
        
        cols = ["match_id", "resultado", "map", "placar", "team_name_a", "team_name_b", "rating_player", "diff"]
        rename_dict = {
            "match_id": "ID Partida",
            "resultado": "Resultado",
            "map": "Mapa",
            "placar": "Placar",
            "team_name_a": "Time A",
            "team_name_b": "Time B",
            "rating_player": "Rating Final",
            "diff": "Pontos (RP)"
        }
        st.dataframe(matches_display[cols].rename(columns=rename_dict), use_container_width=True)
