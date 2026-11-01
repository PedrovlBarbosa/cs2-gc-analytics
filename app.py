import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import (
    CORE_PLAYERS,
    get_all_months,
    get_core_players_stats,
    get_core_squad_totals,
    get_player_history,
    get_matches_by_month
)

# Configuração da Página
st.set_page_config(
    page_title="CS2 - Squad Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Moderna com tema Gamer
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff7700, #ffaa00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #181d28;
        border: 1px solid #283144;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.85rem;
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
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .squad-badge {
        display: inline-block;
        background: rgba(255, 119, 0, 0.15);
        color: #ff9933;
        border: 1px solid rgba(255, 119, 0, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Lista de meses disponíveis
available_months = ["Todo o Histórico (Acumulado)"] + get_all_months()

# Sidebar
with st.sidebar:
    st.image("https://gcv1-assets.gamersclub.com.br/assets/images/perfil/icon-lobby.png", width=65)
    st.title("Squad Analytics")
    st.caption("Painel Exclusivo dos 7 Jogadores Principais")
    
    st.markdown("---")
    st.subheader("⚡ Sincronização")
    
    has_local_config = os.path.exists("config.json")
    has_cloud_secrets = False
    try:
        has_cloud_secrets = hasattr(st, "secrets") and ("GC_CONFIG" in st.secrets or "cookies" in st.secrets)
    except Exception:
        pass

    if has_local_config or has_cloud_secrets:
        if st.button("🔄 Sincronizar Jogos Agora", use_container_width=True, type="primary"):
            with st.spinner("Buscando partidas na Gamers Club e atualizando..."):
                try:
                    from sync_now import sync_recent
                    m_cnt, up_cnt, pushed = sync_recent(2, auto_push=has_local_config)
                    if pushed:
                        st.success(f"✅ Atualizado! {up_cnt} estatísticas sincronizadas e publicadas para os amigos!")
                    else:
                        st.success(f"✅ Atualizado! {up_cnt} estatísticas sincronizadas com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao sincronizar: {e}")
    else:
        st.info("💡 **Aviso:** Como este link está na nuvem pública (Streamlit Cloud), a sincronização é feita com 1 clique pelo seu computador (onde seus cookies estão salvos com segurança) ou configurando 'Secrets' nas opções do Streamlit.")

    st.markdown("---")
    st.subheader("🗓️ Filtro de Período")
    selected_period = st.selectbox(
        "Selecione o Período:",
        options=available_months,
        index=0
    )
    month_filter = None if selected_period == "Todo o Histórico (Acumulado)" else selected_period

    st.markdown("---")
    st.markdown("### 🏆 Core Squad (7 Jogadores)")
    for nick in CORE_PLAYERS:
        st.markdown(f"<span class='squad-badge'>🎮 {nick}</span>", unsafe_allow_html=True)

# Título Principal
period_label = "Todo o Histórico Consolidado" if not month_filter else f"Mês: {month_filter}"
st.markdown(f"<div class='main-title'>CS2 Squad Analytics • Core 7</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>Estatísticas individuais e consolidadas de <b>KrannDy, Aquarista, Art, Cherki, Death, Kinha e mch</b> • Período: <b>{period_label}</b></div>", unsafe_allow_html=True)

# Dados do Squad e Totais
squad_df = get_core_players_stats(month=month_filter)
squad_totals = get_core_squad_totals(month=month_filter)

if squad_df.empty or not squad_totals:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
    st.stop()

# Abas Principais
tab_squad_totals, tab_comparative, tab_individual, tab_maps, tab_matches = st.tabs([
    "🔥 Conjunto de Todos (Squad)",
    "⚔️ Comparativo dos 7",
    "👤 Perfil Individual",
    "🗺️ Análise de Mapas",
    "📜 Partidas Recentes"
])

# -----------------------------------------------------------------------------
# TAB 1: CONJUNTO DE TODOS (SQUAD COLETIVO)
# -----------------------------------------------------------------------------
with tab_squad_totals:
    st.subheader(f"📊 Totais Consolidados do Conjunto dos 7 Jogadores ({period_label})")
    st.caption("Soma e médias acumuladas de todas as partidas disputadas pelo grupo.")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Partidas do Time</div>
            <div class='metric-value'>{squad_totals['unique_matches']:,}</div>
            <div class='metric-sub'>{squad_totals['unique_wins']:,}V - {squad_totals['unique_loss']:,}D ({squad_totals['total_participations']:,} indiv.)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Win Rate do Time</div>
            <div class='metric-value'>{squad_totals['unique_win_rate']:.1f}%</div>
            <div class='metric-sub'>Taxa de Vitória Real</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>K/D Coletivo</div>
            <div class='metric-value'>{squad_totals['kdr']:.2f}</div>
            <div class='metric-sub'>{squad_totals['total_kills']:,} Kills / {squad_totals['total_deaths']:,} D</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>ADR Médio do Squad</div>
            <div class='metric-value'>{squad_totals['adr']:.1f}</div>
            <div class='metric-sub'>Dano Médio / Round</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>First Kills (Opening)</div>
            <div class='metric-value'>{squad_totals['first_kills']:,}</div>
            <div class='metric-sub'>Primeiras Kills</div>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Multi Kills</div>
            <div class='metric-value'>{squad_totals['multi_kills']:,}</div>
            <div class='metric-sub'>2k, 3k, 4k e Aces</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_obj1, col_obj2 = st.columns([1, 1])
    with col_obj1:
        st.markdown("#### 💣 Objetivos de C4 Coletivos")
        o1, o2 = st.columns(2)
        with o1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bombas Plantadas</div>
                <div class='metric-value' style='color:#f59e0b;'>{squad_totals['bomb_plants']:,}</div>
                <div class='metric-sub'>Plantadas pelo Squad</div>
            </div>
            """, unsafe_allow_html=True)
        with o2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bombas Defusadas</div>
                <div class='metric-value' style='color:#10b981;'>{squad_totals['bomb_defuses']:,}</div>
                <div class='metric-sub'>Defuses Realizados</div>
            </div>
            """, unsafe_allow_html=True)

    with col_obj2:
        st.markdown("#### 🎯 Distribuição de Tiros do Squad (Hitbox Total)")
        hit_data = {
            "Região": ["Cabeça", "Peito", "Estômago", "Braços", "Pernas"],
            "Tiros": [
                squad_totals['hitbox_head'],
                squad_totals['hitbox_chest'],
                squad_totals['hitbox_stomach'],
                squad_totals['hitbox_arms'],
                squad_totals['hitbox_legs']
            ]
        }
        hit_df = pd.DataFrame(hit_data)
        if hit_df["Tiros"].sum() > 0:
            fig_hit = px.pie(
                hit_df, values="Tiros", names="Região",
                hole=0.45,
                color_discrete_sequence=['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']
            )
            fig_hit.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=240, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_hit, use_container_width=True)
        else:
            st.info("Sem registro de Hitbox para este período.")

# -----------------------------------------------------------------------------
# TAB 2: COMPARATIVO DOS 7 JOGADORES
# -----------------------------------------------------------------------------
with tab_comparative:
    st.subheader(f"⚔️ Comparativo Direto entre os 7 Jogadores ({period_label})")

    top_kills = squad_df.loc[squad_df['kills'].idxmax()]
    top_adr = squad_df.loc[squad_df['adr'].idxmax()]
    top_kdr = squad_df.loc[squad_df['kdr'].idxmax()]
    top_first = squad_df.loc[squad_df['first_kills'].idxmax()]

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>👑 Top Fragger:</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#ff7700;'>{top_kills['nick']}</span> — <b>{top_kills['kills']:,}</b> Kills
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>🔥 Maior ADR (Dano Médio):</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#38bdf8;'>{top_adr['nick']}</span> — <b>{top_adr['adr']:.1f}</b> ADR
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>🎯 Maior K/D Ratio:</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#10b981;'>{top_kdr['nick']}</span> — <b>{top_kdr['kdr']:.2f}</b> KDR
        </div>
        """, unsafe_allow_html=True)
    with h4:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>⚡ Rei do First Kill:</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#a855f7;'>{top_first['nick']}</span> — <b>{top_first['first_kills']:,}</b> Aberturas
        </div>
        """, unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_adr = px.bar(
            squad_df.sort_values(by="adr", ascending=True),
            x="adr", y="nick", orientation='h',
            title="Dano Médio por Round (ADR)",
            color="adr", color_continuous_scale="Oranges", text="adr"
        )
        fig_adr.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_adr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_adr, use_container_width=True)

    with g_col2:
        fig_kdr = px.bar(
            squad_df.sort_values(by="kdr", ascending=True),
            x="kdr", y="nick", orientation='h',
            title="K/D Ratio (KDR Geral)",
            color="kdr", color_continuous_scale="Blues", text="kdr"
        )
        fig_kdr.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_kdr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_kdr, use_container_width=True)

    g_col3, g_col4 = st.columns(2)
    with g_col3:
        fig_kills = px.bar(
            squad_df.sort_values(by="kills", ascending=True),
            x="kills", y="nick", orientation='h',
            title="Total de Abates (Kills)",
            color="kills", color_continuous_scale="Viridis", text="kills"
        )
        fig_kills.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_kills.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_kills, use_container_width=True)

    with g_col4:
        fig_fk = px.bar(
            squad_df.sort_values(by="first_kills", ascending=True),
            x="first_kills", y="nick", orientation='h',
            title="Primeiras Kills (First Kills / Opening)",
            color="first_kills", color_continuous_scale="Sunsetdark", text="first_kills"
        )
        fig_fk.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_fk.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_fk, use_container_width=True)

    st.markdown("### 📋 Tabela Geral Comparativa dos 7 Jogadores")
    cols_display = [
        "nick", "matches", "wins", "loss", "win_rate", "kdr", "adr",
        "kills", "deaths", "first_kills", "multi_kills", "bomb_plants", "bomb_defuses", "hs_percent", "kast_percent"
    ]
    renamed = {
        "nick": "Jogador",
        "matches": "Partidas",
        "wins": "Vitórias",
        "loss": "Derrotas",
        "win_rate": "Win Rate (%)",
        "kdr": "K/D",
        "adr": "ADR",
        "kills": "Kills",
        "deaths": "Mortes",
        "first_kills": "First Kills",
        "multi_kills": "Multi Kills",
        "bomb_plants": "Plants",
        "bomb_defuses": "Defuses",
        "hs_percent": "HS %",
        "kast_percent": "KAST %"
    }
    styled_df = squad_df[cols_display].rename(columns=renamed).reset_index(drop=True)
    st.dataframe(styled_df, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: PERFIL INDIVIDUAL DETALHADO
# -----------------------------------------------------------------------------
with tab_individual:
    selected_player_nick = st.selectbox("Selecione o Jogador para ver o Perfil Detalhado:", options=CORE_PLAYERS, index=0)
    
    player_row = squad_df[squad_df["nick"] == selected_player_nick]
    if not player_row.empty:
        p = player_row.iloc[0]
        pid = int(p["player_id"])

        st.markdown(f"### Perfil de **{p['nick']}** ({period_label})")
        
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Partidas</div>
                <div class='metric-value'>{int(p['matches']):,}</div>
                <div class='metric-sub'>{int(p['wins']):,}V - {int(p['loss']):,}D</div>
            </div>
            """, unsafe_allow_html=True)
        with p2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Win Rate</div>
                <div class='metric-value'>{p['win_rate']:.1f}%</div>
                <div class='metric-sub'>Taxa de Vitória</div>
            </div>
            """, unsafe_allow_html=True)
        with p3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>K/D Ratio</div>
                <div class='metric-value'>{p['kdr']:.2f}</div>
                <div class='metric-sub'>{int(p['kills']):,}K / {int(p['deaths']):,}D</div>
            </div>
            """, unsafe_allow_html=True)
        with p4:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>ADR Médio</div>
                <div class='metric-value'>{p['adr']:.1f}</div>
                <div class='metric-sub'>Dano por Round</div>
            </div>
            """, unsafe_allow_html=True)
        with p5:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>First Kills</div>
                <div class='metric-value'>{int(p['first_kills']):,}</div>
                <div class='metric-sub'>Multi Kills: {int(p['multi_kills']):,}</div>
            </div>
            """, unsafe_allow_html=True)
        with p6:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>HS % / KAST</div>
                <div class='metric-value'>{p['hs_percent']:.0f}%</div>
                <div class='metric-sub'>KAST: {p['kast_percent']:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_hist, col_hit = st.columns([2, 1])
        with col_hist:
            st.subheader(f"📈 Evolução Mês a Mês de {p['nick']}")
            p_history = get_player_history(pid)
            if not p_history.empty:
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=p_history['month'], y=p_history['kdr'],
                    mode='lines+markers', name='KDR', line=dict(color='#ff7700', width=3)
                ))
                fig_timeline.add_trace(go.Scatter(
                    x=p_history['month'], y=p_history['adr'] / 100.0,
                    mode='lines+markers', name='ADR (/100)', line=dict(color='#38bdf8', width=2, dash='dot')
                ))
                fig_timeline.add_trace(go.Scatter(
                    x=p_history['month'], y=p_history['win_rate'] / 100.0,
                    mode='lines+markers', name='Win Rate (/100)', line=dict(color='#10b981', width=2)
                ))
                fig_timeline.update_layout(
                    template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("Sem histórico mensal disponível.")

        with col_hit:
            st.subheader(f"🎯 Hitbox de {p['nick']}")
            p_hit_data = {
                "Região": ["Cabeça", "Peito", "Estômago", "Braços", "Pernas"],
                "Tiros": [
                    p.get('hitbox_head', 0),
                    p.get('hitbox_chest', 0),
                    p.get('hitbox_stomach', 0),
                    p.get('hitbox_arms', 0),
                    p.get('hitbox_legs', 0)
                ]
            }
            p_hit_df = pd.DataFrame(p_hit_data)
            if p_hit_df["Tiros"].sum() > 0:
                fig_p_hit = px.pie(
                    p_hit_df, values="Tiros", names="Região", hole=0.45,
                    color_discrete_sequence=['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']
                )
                fig_p_hit.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_p_hit, use_container_width=True)
            else:
                st.info("Sem registro de Hitbox para este jogador.")

# Mapeamento de Nick para ID
PLAYER_NAME_TO_ID = {
    'KrannDy': 108698,
    'Aquarista': 87484,
    'Art': 108939,
    'Cherki': 540777,
    'Death': 318687,
    'Kinha': 108940,
    'mch': 89302
}

# -----------------------------------------------------------------------------
# TAB 4: ANÁLISE DE MAPAS
# -----------------------------------------------------------------------------
with tab_maps:
    st.subheader(f"🗺️ Desempenho por Mapa ({period_label})")
    
    col_map_sel, _ = st.columns([1, 2])
    with col_map_sel:
        selected_map_player = st.selectbox(
            "Filtrar Partidas por Jogador:",
            options=["Todos do Squad"] + CORE_PLAYERS,
            index=0,
            key="map_player_select"
        )
    target_map_pid = PLAYER_NAME_TO_ID.get(selected_map_player) if selected_map_player != "Todos do Squad" else None
    matches_df = get_matches_by_month(month_filter, target_map_pid)

    if matches_df.empty:
        st.info("Nenhuma partida com registro de mapa encontrada para este período/filtro.")
    else:
        # Se for squad geral, deduplica para não contar a mesma partida 5 vezes por mapa
        calc_map_df = matches_df.drop_duplicates(subset=["match_id"]) if target_map_pid is None else matches_df

        map_stats = calc_map_df.groupby("map").agg(
            total=('match_id', 'count'),
            wins=('win', 'sum')
        ).reset_index()
        map_stats['losses'] = map_stats['total'] - map_stats['wins']
        map_stats['win_rate'] = (map_stats['wins'] / map_stats['total'] * 100).round(1)
        map_stats = map_stats.sort_values(by="total", ascending=False)

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            fig_map_vol = px.bar(
                map_stats, x="map", y=["wins", "losses"],
                title=f"Vitórias e Derrotas por Mapa ({selected_map_player})",
                color_discrete_map={"wins": "#10b981", "losses": "#ef4444"},
                barmode="stack"
            )
            fig_map_vol.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827')
            st.plotly_chart(fig_map_vol, use_container_width=True)

        with m_col2:
            fig_map_wr = px.bar(
                map_stats, x="map", y="win_rate",
                title=f"Taxa de Vitória (%) por Mapa ({selected_map_player})",
                color="win_rate", color_continuous_scale="Tealgrn", text="win_rate"
            )
            fig_map_wr.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_map_wr.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', yaxis_range=[0, 105])
            st.plotly_chart(fig_map_wr, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: PARTIDAS RECENTES
# -----------------------------------------------------------------------------
with tab_matches:
    st.subheader(f"📜 Histórico de Partidas ({period_label})")
    
    col_p_match, _ = st.columns([1, 2])
    with col_p_match:
        selected_p_match = st.selectbox(
            "Filtrar Partidas por Jogador:",
            options=["Todos do Squad"] + CORE_PLAYERS,
            index=0,
            key="matches_player_select"
        )
    target_match_pid = PLAYER_NAME_TO_ID.get(selected_p_match) if selected_p_match != "Todos do Squad" else None
    matches_df = get_matches_by_month(month_filter, target_match_pid)
    
    if matches_df.empty:
        st.info("Nenhuma partida listada para este período/filtro.")
    else:
        if target_match_pid is None:
            # Agrupa partidas do time para não duplicar o mesmo jogo 5 vezes
            grouped_records = []
            for mid, grp in matches_df.groupby("match_id", sort=False):
                first = grp.iloc[0]
                nicks_in_match = ", ".join(grp["player_nick"].dropna().unique().tolist())
                grouped_records.append({
                    "match_id": mid,
                    "jogadores": nicks_in_match,
                    "resultado": "🏆 Vitória" if first["win"] == 1 else "❌ Derrota",
                    "map": first["map"],
                    "placar": f"{first['score_a']} x {first['score_b']}",
                    "team_name_a": first["team_name_a"],
                    "team_name_b": first["team_name_b"],
                    "qtd": len(grp)
                })
            m_display = pd.DataFrame(grouped_records)
            st.caption(f"Mostrando **{len(m_display)}** partidas disputadas pelo time no período.")
            cols = ["match_id", "resultado", "map", "placar", "jogadores", "team_name_a", "team_name_b"]
            renamed = {
                "match_id": "ID Partida",
                "resultado": "Resultado",
                "map": "Mapa",
                "placar": "Placar",
                "jogadores": "Jogadores Presentes",
                "team_name_a": "Time A",
                "team_name_b": "Time B"
            }
            st.dataframe(m_display[cols].rename(columns=renamed), use_container_width=True)
        else:
            st.caption(f"Mostrando **{len(matches_df)}** partidas registradas para {selected_p_match}.")
            m_display = matches_df.copy()
            m_display["resultado"] = m_display["win"].apply(lambda w: "🏆 Vitória" if w == 1 else "❌ Derrota")
            m_display["placar"] = m_display.apply(lambda r: f"{r['score_a']} x {r['score_b']}", axis=1)
            m_display["diff"] = m_display["rating_diff"].apply(lambda d: f"+{d}" if d > 0 else str(d))

            cols = ["match_id", "resultado", "map", "placar", "team_name_a", "team_name_b", "rating_player", "diff"]
            renamed = {
                "match_id": "ID Partida",
                "resultado": "Resultado",
                "map": "Mapa",
                "placar": "Placar",
                "team_name_a": "Time A",
                "team_name_b": "Time B",
                "rating_player": "Rating Final",
                "diff": "Pontos (RP)"
            }
            st.dataframe(m_display[cols].rename(columns=renamed), use_container_width=True)
