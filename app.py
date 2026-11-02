import os
import sys
import time
import importlib
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database
try:
    importlib.reload(database)
except Exception:
    pass
from database import (
    CORE_PLAYERS,
    get_all_months,
    get_core_players_stats,
    get_core_squad_totals,
    get_player_history,
    get_matches_by_month,
    get_telemetry_stats,
    get_gc_advanced_squad_stats,
    get_gc_match_scoreboard
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

# Sidebar
with st.sidebar:
    st.image("https://gcv1-assets.gamersclub.com.br/assets/images/perfil/icon-lobby.png", width=65)
    st.title("Squad Analytics")
    st.caption("Painel Exclusivo do Squad de Jogadores")
    
    st.markdown("---")
    st.subheader("⚡ Sincronização")
    
    has_local_config = os.path.exists("config.json")
    has_cloud_secrets = False
    try:
        has_cloud_secrets = hasattr(st, "secrets") and ("GC_CONFIG" in st.secrets or "cookies" in st.secrets)
    except Exception:
        pass

    if st.button("⚡ Atualizar Tudo (GC + Steam)", use_container_width=True, help="Sincroniza Gamers Club e Steam (Leetify) de uma vez só"):
        with st.spinner("Sincronizando Gamers Club e Steam..."):
            try:
                from sync_now import sync_recent
                m_cnt, up_cnt, pushed = sync_recent(auto_push=has_local_config, sync_steam=True)
                if up_cnt > 0:
                    st.success(f"🔥 {up_cnt} nova(s) partida(s) adicionada(s)!")
                else:
                    st.info("✅ Tudo 100% em dia!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro na sincronização: {e}")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 Apenas GC", use_container_width=True, help="Sincronizar apenas Gamers Club"):
            with st.spinner("Buscando Gamers Club..."):
                try:
                    from sync_now import sync_recent
                    m_cnt, up_cnt, pushed = sync_recent(auto_push=has_local_config, sync_steam=False)
                    if up_cnt > 0:
                        st.success(f"🔥 {up_cnt} novas na GC!")
                    else:
                        st.info("✅ GC em dia!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro GC: {e}")
    with col_s2:
        if st.button("🎯 Apenas Steam", use_container_width=True, help="Sincronizar apenas Steam via Leetify"):
            with st.spinner("Buscando Steam no Leetify..."):
                try:
                    from leetify_collector import sync_steam_matches
                    saved = sync_steam_matches()
                    if saved > 0:
                        st.success(f"🎯 {saved} nova(s) partida(s) Steam sincronizada(s)!")
                        if has_local_config:
                            from sync_now import push_to_github
                            push_to_github()
                    else:
                        st.info("✅ Steam em dia (0 partidas novas)!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro Steam: {e}")

    if st.button("🏅 Novas Stats GC (Entries, Trades...)", use_container_width=True, help="Enriquece partidas recentes com as novas estatísticas oficiais da GC"):
        with st.spinner("Buscando novas estatísticas na Gamers Club..."):
            try:
                from enrich_gc_stats import enrich_gc_matches
                cnt = enrich_gc_matches(limit=50, verbose=False)
                if cnt > 0:
                    st.success(f"🔥 {cnt} partida(s) enriquecida(s) com as novas estatísticas da GC!")
                else:
                    st.info("✅ Todas as partidas da GC já possuem as novas estatísticas!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao enriquecer GC: {e}")

    st.markdown("---")
    st.subheader("🎮 Plataforma")
    platform_option = st.radio(
        "Filtrar por Plataforma:",
        options=["🌐 Todas (Consolidado)", "🏅 Gamers Club (GC)", "🎯 Steam (Premier & MM)"],
        index=0
    )
    if "Gamers Club" in platform_option:
        platform_filter = "GC"
        platform_tag = "Gamers Club"
    elif "Steam" in platform_option:
        platform_filter = "STEAM"
        platform_tag = "Steam (Premier & MM)"
    else:
        platform_filter = "TODOS"
        platform_tag = "Todas as Plataformas (Geral)"

    st.markdown("---")
    st.subheader("🗓️ Filtro de Período")
    try:
        available_months = ["Todo o Histórico (Acumulado)"] + get_all_months(platform=platform_filter)
    except TypeError:
        available_months = ["Todo o Histórico (Acumulado)"] + get_all_months()
    selected_period = st.selectbox(
        "Selecione o Período:",
        options=available_months,
        index=0
    )
    month_filter = None if selected_period == "Todo o Histórico (Acumulado)" else selected_period

    st.markdown("---")
    st.markdown("### 🏆 Core Squad")
    for nick in CORE_PLAYERS:
        st.markdown(f"<span class='squad-badge'>🎮 {nick}</span>", unsafe_allow_html=True)

# Título Principal
period_label = "Todo o Histórico Consolidado" if not month_filter else f"Mês: {month_filter}"
st.markdown(f"<div class='main-title'>CS2 Squad Analytics • Squad</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>Estatísticas de <b>Todos os Jogadores do Squad</b> • Período: <b>{period_label}</b> • Plataforma: <b>{platform_tag}</b></div>", unsafe_allow_html=True)

# Dados do Squad e Totais
try:
    squad_df = get_core_players_stats(month=month_filter, platform=platform_filter)
    squad_totals = get_core_squad_totals(month=month_filter, platform=platform_filter)
except TypeError:
    squad_df = get_core_players_stats(month=month_filter)
    squad_totals = get_core_squad_totals(month=month_filter)

if squad_df.empty or not squad_totals:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
    st.stop()

# Cálculo de médias por partida para cada jogador
m_denom = squad_df["matches"].replace(0, 1)
squad_df["kills_per_match"] = (squad_df["kills"] / m_denom).round(1)
squad_df["deaths_per_match"] = (squad_df["deaths"] / m_denom).round(1)
squad_df["first_kills_per_match"] = (squad_df["first_kills"] / m_denom).round(2)
squad_df["multi_kills_per_match"] = (squad_df["multi_kills"] / m_denom).round(2)
squad_df["plants_per_match"] = (squad_df["bomb_plants"] / m_denom).round(2)
squad_df["defuses_per_match"] = (squad_df["bomb_defuses"] / m_denom).round(2)

# Abas Principais
tab_squad_totals, tab_comparative, tab_gc_advanced, tab_telemetry, tab_individual, tab_maps, tab_matches = st.tabs([
    "🔥 Conjunto de Todos (Squad)",
    "⚔️ Comparativo do Squad",
    "🏅 Novas Estatísticas GC",
    "🎯 Telemetria Avançada (Leetify)",
    "👤 Perfil Individual",
    "🗺️ Análise de Mapas",
    "📜 Partidas Recentes"
])

# -----------------------------------------------------------------------------
# TAB 1: CONJUNTO DE TODOS (SQUAD COLETIVO)
# -----------------------------------------------------------------------------
with tab_squad_totals:
    st.subheader(f"📊 Totais Consolidados do Conjunto de Todos os Jogadores ({period_label})")
    st.caption("Soma e médias acumuladas de todas as partidas disputadas pelo grupo.")
    
    # Extrai valores de forma segura protegida contra KeyError
    u_matches = squad_totals.get("unique_matches", squad_totals.get("total_matches", 0))
    u_wins = squad_totals.get("unique_wins", squad_totals.get("total_wins", 0))
    u_loss = squad_totals.get("unique_loss", squad_totals.get("total_loss", 0))
    u_wr = squad_totals.get("unique_win_rate", squad_totals.get("win_rate", 0.0))
    tot_part = squad_totals.get("total_participations", u_matches)
    tot_kills = squad_totals.get("total_kills", 0)
    tot_deaths = squad_totals.get("total_deaths", 0)
    s_kdr = squad_totals.get("kdr", 0.0)
    s_adr = squad_totals.get("adr", 0.0)
    s_first = squad_totals.get("first_kills", 0)
    s_multi = squad_totals.get("multi_kills", 0)
    s_plants = squad_totals.get("bomb_plants", 0)
    s_defuses = squad_totals.get("bomb_defuses", 0)

    # Médias coletivas por partida
    u_denom = max(1, u_matches)
    avg_team_kpm = round(tot_kills / u_denom, 1)
    avg_team_fk = round(s_first / u_denom, 1)
    avg_team_mk = round(s_multi / u_denom, 1)
    avg_team_plants = round(s_plants / u_denom, 1)
    avg_team_defuses = round(s_defuses / u_denom, 1)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Partidas do Time</div>
            <div class='metric-value'>{u_matches:,}</div>
            <div class='metric-sub'>{u_wins:,}V - {u_loss:,}D ({tot_part:,} indiv.)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Win Rate do Time</div>
            <div class='metric-value'>{u_wr:.1f}%</div>
            <div class='metric-sub'>Taxa de Vitória Real</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Kills Coletivas</div>
            <div class='metric-value'>{tot_kills:,}</div>
            <div class='metric-sub'>{s_kdr:.2f} K/D • Média: {avg_team_kpm:.1f} / jogo</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>ADR Médio do Squad</div>
            <div class='metric-value'>{s_adr:.1f}</div>
            <div class='metric-sub'>Dano Médio / Round</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>First Kills (Opening)</div>
            <div class='metric-value'>{s_first:,}</div>
            <div class='metric-sub'>Média: {avg_team_fk:.1f} por jogo</div>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Multi Kills</div>
            <div class='metric-value'>{s_multi:,}</div>
            <div class='metric-sub'>Média: {avg_team_mk:.1f} por jogo</div>
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
                <div class='metric-value' style='color:#f59e0b;'>{s_plants:,}</div>
                <div class='metric-sub'>Total Squad • Média: {avg_team_plants:.1f} / jogo</div>
            </div>
            """, unsafe_allow_html=True)
        with o2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bombas Defusadas</div>
                <div class='metric-value' style='color:#10b981;'>{s_defuses:,}</div>
                <div class='metric-sub'>Total Squad • Média: {avg_team_defuses:.1f} / jogo</div>
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
            <div style='font-size:0.8rem; color:#94a3b8;'>Média: <b>{top_kills['kills_per_match']:.1f}</b> kills / jogo</div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>🔥 Maior ADR (Dano Médio):</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#38bdf8;'>{top_adr['nick']}</span> — <b>{top_adr['adr']:.1f}</b> ADR
            <div style='font-size:0.8rem; color:#94a3b8;'>Dano causado a cada round</div>
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>🎯 Maior K/D Ratio:</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#10b981;'>{top_kdr['nick']}</span> — <b>{top_kdr['kdr']:.2f}</b> KDR
            <div style='font-size:0.8rem; color:#94a3b8;'>Kills / Mortes acumuladas</div>
        </div>
        """, unsafe_allow_html=True)
    with h4:
        st.markdown(f"""
        <div class='highlight-card'>
            <b>⚡ Rei do First Kill:</b><br>
            <span style='font-size:1.3rem; font-weight:700; color:#a855f7;'>{top_first['nick']}</span> — <b>{top_first['first_kills']:,}</b> Aberturas
            <div style='font-size:0.8rem; color:#94a3b8;'>Média: <b>{top_first['first_kills_per_match']:.2f}</b> por jogo</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    chart_view_mode = st.radio(
        "Modo de Exibição dos Gráficos Comparativos:",
        options=["📊 Médias por Partida (Performance / Jogo)", "🔢 Totais Absolutos (Volume Acumulado)"],
        horizontal=True,
        key="comparative_chart_view_mode"
    )

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
        if "Médias" in chart_view_mode:
            fig_kills = px.bar(
                squad_df.sort_values(by="kills_per_match", ascending=True),
                x="kills_per_match", y="nick", orientation='h',
                title="Média de Abates por Jogo (Kills / Jogo)",
                color="kills_per_match", color_continuous_scale="Viridis", text="kills_per_match"
            )
            fig_kills.update_traces(texttemplate='%{text:.1f} / j', textposition='outside')
        else:
            fig_kills = px.bar(
                squad_df.sort_values(by="kills", ascending=True),
                x="kills", y="nick", orientation='h',
                title="Total de Abates Acumulados (Kills)",
                color="kills", color_continuous_scale="Viridis", text="kills"
            )
            fig_kills.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_kills.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_kills, use_container_width=True)

    with g_col4:
        if "Médias" in chart_view_mode:
            fig_fk = px.bar(
                squad_df.sort_values(by="first_kills_per_match", ascending=True),
                x="first_kills_per_match", y="nick", orientation='h',
                title="Média de Aberturas por Jogo (First Kills / Jogo)",
                color="first_kills_per_match", color_continuous_scale="Sunsetdark", text="first_kills_per_match"
            )
            fig_fk.update_traces(texttemplate='%{text:.2f} / j', textposition='outside')
        else:
            fig_fk = px.bar(
                squad_df.sort_values(by="first_kills", ascending=True),
                x="first_kills", y="nick", orientation='h',
                title="Total de Primeiras Kills (First Kills / Opening)",
                color="first_kills", color_continuous_scale="Sunsetdark", text="first_kills"
            )
            fig_fk.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_fk.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
        st.plotly_chart(fig_fk, use_container_width=True)

    st.markdown("### 📋 Tabela Geral Comparativa do Squad")
    cols_display = [
        "nick", "matches", "wins", "loss", "win_rate", "kdr", "adr",
        "kills", "kills_per_match", "deaths", "deaths_per_match",
        "first_kills", "first_kills_per_match", "multi_kills", "multi_kills_per_match",
        "bomb_plants", "plants_per_match", "bomb_defuses", "defuses_per_match",
        "hs_percent", "kast_percent"
    ]
    renamed = {
        "nick": "Jogador",
        "matches": "Partidas",
        "wins": "Vitórias",
        "loss": "Derrotas",
        "win_rate": "Win Rate (%)",
        "kdr": "K/D",
        "adr": "ADR",
        "kills": "Kills (Total)",
        "kills_per_match": "Kills/Jogo",
        "deaths": "Mortes (Total)",
        "deaths_per_match": "Mortes/Jogo",
        "first_kills": "FK (Total)",
        "first_kills_per_match": "FK/Jogo",
        "multi_kills": "Multi (Total)",
        "multi_kills_per_match": "Multi/Jogo",
        "bomb_plants": "Plants (Total)",
        "plants_per_match": "Plants/Jogo",
        "bomb_defuses": "Defuses (Total)",
        "defuses_per_match": "Defuses/Jogo",
        "hs_percent": "HS %",
        "kast_percent": "KAST %"
    }
    styled_df = squad_df[cols_display].rename(columns=renamed).reset_index(drop=True)
    st.dataframe(styled_df, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: NOVAS ESTATÍSTICAS GAMERS CLUB (Entries, Trades, Clutch, Utilitárias e Mira)
# -----------------------------------------------------------------------------
with tab_gc_advanced:
    st.subheader(f"🏅 Novas Estatísticas Oficiais da Gamers Club ({period_label})")
    st.caption("Estatísticas nativas extraídas diretamente da Gamers Club: Duelos de Abertura (Entries), Trocas de Abate (Trades), Situações Decisivas (Clutch), Utilitárias e Precisão de Mira.")

    try:
        gc_squad_df = get_gc_advanced_squad_stats(month=month_filter)
    except Exception as e:
        gc_squad_df = pd.DataFrame()

    if gc_squad_df.empty:
        st.info("ℹ️ Nenhuma partida recente com as novas estatísticas da Gamers Club encontrada para o período selecionado. Use o botão '🏅 Novas Stats GC' na barra lateral para sincronizar!")
    else:
        # Destaques Rápidos
        best_entry = gc_squad_df.sort_values(by="entry_success_rate", ascending=False).iloc[0] if "entry_success_rate" in gc_squad_df.columns else None
        best_trader = gc_squad_df.sort_values(by="total_trades_made", ascending=False).iloc[0] if "total_trades_made" in gc_squad_df.columns else None
        best_clutch = gc_squad_df.sort_values(by="total_clutches_won", ascending=False).iloc[0] if "total_clutches_won" in gc_squad_df.columns else None
        best_util = gc_squad_df.sort_values(by="avg_util_damage", ascending=False).iloc[0] if "avg_util_damage" in gc_squad_df.columns else None
        best_aim = gc_squad_df.sort_values(by="avg_accuracy", ascending=False).iloc[0] if "avg_accuracy" in gc_squad_df.columns else None

        gc_h1, gc_h2, gc_h3, gc_h4, gc_h5 = st.columns(5)
        with gc_h1:
            if best_entry is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🚪 Melhor Entry Fragger:</b><br>
                    <span style='font-size:1.25rem; font-weight:700; color:#ff7700;'>{best_entry['nick']}</span> — <b>{best_entry['entry_success_rate']:.1f}%</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Sucesso ({int(best_entry['total_entry_won'])}/{int(best_entry['total_entry_duels'])} duelos)</div>
                </div>
                """, unsafe_allow_html=True)
        with gc_h2:
            if best_trader is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🔄 Rei dos Trades:</b><br>
                    <span style='font-size:1.25rem; font-weight:700; color:#38bdf8;'>{best_trader['nick']}</span> — <b>{int(best_trader['total_trades_made'])}</b> trades
                    <div style='font-size:0.8rem; color:#94a3b8;'>Tempo médio: {best_trader['avg_trade_time']:.1f}s</div>
                </div>
                """, unsafe_allow_html=True)
        with gc_h3:
            if best_clutch is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🏆 Rei do Clutch:</b><br>
                    <span style='font-size:1.25rem; font-weight:700; color:#10b981;'>{best_clutch['nick']}</span> — <b>{int(best_clutch['total_clutches_won'])}</b> vitórias
                    <div style='font-size:0.8rem; color:#94a3b8;'>Aproveitamento: {best_clutch['clutch_win_rate']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
        with gc_h4:
            if best_util is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>💣 Mestre Utilitário:</b><br>
                    <span style='font-size:1.25rem; font-weight:700; color:#f59e0b;'>{best_util['nick']}</span> — <b>{best_util['avg_util_damage']:.0f}</b> dmg/jogo
                    <div style='font-size:0.8rem; color:#94a3b8;'>{int(best_util['total_enemies_flashed'])} inimigos cegados</div>
                </div>
                """, unsafe_allow_html=True)
        with gc_h5:
            if best_aim is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🎯 Mira Mais Precisa:</b><br>
                    <span style='font-size:1.25rem; font-weight:700; color:#ec4899;'>{best_aim['nick']}</span> — <b>{best_aim['avg_accuracy']:.1f}%</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Head Acc: {best_aim['avg_head_acc']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 5 Sub-abas correspondentes às telas oficiais da Gamers Club
        sub_ent, sub_trd, sub_clt, sub_utl, sub_aim = st.tabs([
            "🚪 Entries (Duelos de Abertura)",
            "🔄 Trades (Trocas de Abate)",
            "🏆 Clutch (Situações Decisivas)",
            "💣 Utilitárias",
            "🎯 Mira & Armas"
        ])

        with sub_ent:
            st.markdown("#### 🚪 Duelos de Abertura de Round (Entries)")
            col_ent_tbl, col_ent_gra = st.columns([1.1, 0.9])
            with col_ent_tbl:
                e_df = gc_squad_df[["nick", "analyzed_matches", "total_entry_duels", "total_entry_won", "total_entry_lost", "entry_success_rate", "avg_entry_per_round"]].copy()
                e_df.columns = ["Jogador", "Jogos", "Duelos Totais", "Vencidos", "Perdidos", "Taxa Sucesso (%)", "Aberturas/Round"]
                e_df["Taxa Sucesso (%)"] = e_df["Taxa Sucesso (%)"].apply(lambda v: f"{v:.1f}%")
                e_df["Aberturas/Round"] = e_df["Aberturas/Round"].apply(lambda v: f"{v:.2f}")
                st.dataframe(e_df, use_container_width=True)
            with col_ent_gra:
                fig_e = px.bar(
                    gc_squad_df, x="nick", y=["total_entry_won", "total_entry_lost"],
                    title="Duelos de Abertura: Vencidos vs Perdidos",
                    color_discrete_map={"total_entry_won": "#10b981", "total_entry_lost": "#ef4444"},
                    barmode="stack", labels={"value": "Duelos", "nick": "Jogador", "variable": "Resultado"}
                )
                fig_e.update_layout(template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_e, use_container_width=True)

        with sub_trd:
            st.markdown("#### 🔄 Eficiência e Velocidade de Trade (Vingar Parceiro)")
            col_trd_tbl, col_trd_gra = st.columns([1.1, 0.9])
            with col_trd_tbl:
                t_df = gc_squad_df[["nick", "analyzed_matches", "total_trades_made", "total_traded_deaths", "avg_trade_rate", "avg_trade_time"]].copy()
                t_df.columns = ["Jogador", "Jogos", "Trades Feitos", "Mortes Trocadas", "Taxa de Troca (%)", "Tempo Médio (s)"]
                t_df["Taxa de Troca (%)"] = t_df["Taxa de Troca (%)"].apply(lambda v: f"{v:.1f}%")
                t_df["Tempo Médio (s)"] = t_df["Tempo Médio (s)"].apply(lambda v: f"{v:.1f}s")
                st.dataframe(t_df, use_container_width=True)
            with col_trd_gra:
                fig_t = px.bar(
                    gc_squad_df, x="nick", y="avg_trade_time",
                    title="Tempo Médio para Vingar o Aliado (Menor é Melhor)",
                    color="avg_trade_time", color_continuous_scale="Viridis_r", text="avg_trade_time"
                )
                fig_t.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
                fig_t.update_layout(template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_t, use_container_width=True)

        with sub_clt:
            st.markdown("#### 🏆 Desempenho em Situações de Clutch")
            col_clt_tbl, col_clt_gra = st.columns([1.1, 0.9])
            with col_clt_tbl:
                c_df = gc_squad_df[["nick", "total_clutches", "total_clutches_won", "clutch_win_rate", "total_1v1_won", "total_1v1_played", "total_1vn_won", "total_1vn_played"]].copy()
                c_df["1v1 (Venc/Total)"] = c_df.apply(lambda r: f"{int(r['total_1v1_won'])}/{int(r['total_1v1_played'])}", axis=1)
                c_df["1vN (Venc/Total)"] = c_df.apply(lambda r: f"{int(r['total_1vn_won'])}/{int(r['total_1vn_played'])}", axis=1)
                c_df = c_df[["nick", "total_clutches", "total_clutches_won", "clutch_win_rate", "1v1 (Venc/Total)", "1vN (Venc/Total)"]]
                c_df.columns = ["Jogador", "Situações", "Vencidos", "Aproveitamento (%)", "1v1 (Venc/Total)", "1vN (Venc/Total)"]
                c_df["Aproveitamento (%)"] = c_df["Aproveitamento (%)"].apply(lambda v: f"{v:.1f}%")
                st.dataframe(c_df, use_container_width=True)
            with col_clt_gra:
                fig_c = px.bar(
                    gc_squad_df, x="nick", y="total_clutches_won",
                    title="Total de Clutches Vencidos pelo Squad",
                    color="total_clutches_won", color_continuous_scale="Tealgrn", text="total_clutches_won"
                )
                fig_c.update_traces(textposition="outside")
                fig_c.update_layout(template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_c, use_container_width=True)

        with sub_utl:
            st.markdown("#### 💣 Utilitárias, Granadas e Assistências com Flash")
            col_utl_tbl, col_utl_gra = st.columns([1.1, 0.9])
            with col_utl_tbl:
                u_df = gc_squad_df[["nick", "total_util_damage", "avg_util_damage", "total_flash_assists", "total_enemies_flashed", "total_grenades", "avg_damage_per_grenade"]].copy()
                u_df.columns = ["Jogador", "Dano Total Util", "Dano Médio/Jogo", "Flash Assists", "Inimigos Cegados", "Granadas", "Dano/Granada"]
                st.dataframe(u_df, use_container_width=True)
            with col_utl_gra:
                fig_u = px.bar(
                    gc_squad_df, x="nick", y="total_enemies_flashed",
                    title="Total de Inimigos Cegados com Granadas de Luz",
                    color="total_enemies_flashed", color_continuous_scale="Sunset", text="total_enemies_flashed"
                )
                fig_u.update_traces(textposition="outside")
                fig_u.update_layout(template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_u, use_container_width=True)

        with sub_aim:
            st.markdown("#### 🎯 Precisão de Mira, Headshot e Arma Principal")
            col_aim_tbl, col_aim_gra = st.columns([1.1, 0.9])
            with col_aim_tbl:
                a_df = gc_squad_df[["nick", "avg_accuracy", "avg_hs_rate", "avg_head_acc", "avg_kpr", "avg_gc_rating"]].copy()
                a_df.columns = ["Jogador", "Precisão (%)", "HS (%)", "Head Acc (%)", "Abates/Round", "GC Rating Médio"]
                a_df["Precisão (%)"] = a_df["Precisão (%)"].apply(lambda v: f"{v:.1f}%")
                a_df["HS (%)"] = a_df["HS (%)"].apply(lambda v: f"{v:.1f}%")
                a_df["Head Acc (%)"] = a_df["Head Acc (%)"].apply(lambda v: f"{v:.1f}%")
                st.dataframe(a_df, use_container_width=True)
            with col_aim_gra:
                fig_a = px.bar(
                    gc_squad_df, x="nick", y=["avg_accuracy", "avg_head_acc"],
                    title="Precisão Geral (%) vs Head Accuracy (%)",
                    color_discrete_map={"avg_accuracy": "#38bdf8", "avg_head_acc": "#ec4899"},
                    barmode="group", labels={"value": "Porcentagem (%)", "nick": "Jogador", "variable": "Métrica"}
                )
                fig_a.update_layout(template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_a, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB: TELEMETRIA & MIRA (LEETIFY)
# -----------------------------------------------------------------------------
with tab_telemetry:
    st.subheader(f"🎯 Telemetria Avançada & Análise de Mira ({period_label})")
    st.caption("Métricas extraídas via processamento telemétrico de demos (Leetify) cobrindo tempo de reação, abertura de mira, counter-strafe, trocas e utilitários.")

    telemetry_df = get_telemetry_stats(month=month_filter, platform=platform_filter)

    if telemetry_df.empty:
        st.info("Nenhum dado telemétrico encontrado para o filtro selecionado. Experimente selecionar 'Todo o Histórico (Acumulado)' ou 'Todas as Plataformas'.")
    else:
        # Cards dos Especialistas do Squad
        st.markdown("### 🌟 Destaques & Especialistas do Squad")
        
        # Identifica líderes
        best_reaction = telemetry_df[telemetry_df["avg_reaction_time"] > 0].sort_values(by="avg_reaction_time", ascending=True).iloc[0] if not telemetry_df[telemetry_df["avg_reaction_time"] > 0].empty else None
        best_preaim = telemetry_df[telemetry_df["avg_preaim"] > 0].sort_values(by="avg_preaim", ascending=True).iloc[0] if not telemetry_df[telemetry_df["avg_preaim"] > 0].empty else None
        best_cs = telemetry_df.sort_values(by="avg_counter_strafe", ascending=False).iloc[0] if not telemetry_df.empty else None
        best_trades = telemetry_df.sort_values(by="avg_trade_kills", ascending=False).iloc[0] if not telemetry_df.empty else None
        best_leetify = telemetry_df.sort_values(by="avg_leetify_rating", ascending=False).iloc[0] if not telemetry_df.empty else None
        best_util = telemetry_df[telemetry_df["avg_utility_waste"] > 0].sort_values(by="avg_utility_waste", ascending=True).iloc[0] if not telemetry_df[telemetry_df["avg_utility_waste"] > 0].empty else None

        t1, t2, t3 = st.columns(3)
        with t1:
            if best_reaction is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>⚡ Gatilho Mais Rápido (Reação):</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#38bdf8;'>{best_reaction['nick']}</span> — <b>{best_reaction['avg_reaction_time']:.0f} ms</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Tempo médio até o primeiro dano causado</div>
                </div>
                """, unsafe_allow_html=True)
            if best_cs is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🛑 Rei do Counter-Strafe:</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#10b981;'>{best_cs['nick']}</span> — <b>{best_cs['avg_counter_strafe']:.1f}%</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Tiros efetuados 100% parado (precisão perfeita)</div>
                </div>
                """, unsafe_allow_html=True)

        with t2:
            if best_preaim is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🎯 Pixel Mais Afiado (Preaim):</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#f59e0b;'>{best_preaim['nick']}</span> — <b>{best_preaim['avg_preaim']:.1f}°</b> erro
                    <div style='font-size:0.8rem; color:#94a3b8;'>Menor desvio angular ao abrir o pixel</div>
                </div>
                """, unsafe_allow_html=True)
            if best_trades is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>🤝 Rei das Trocas (Trade Kills):</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#a855f7;'>{best_trades['nick']}</span> — <b>{best_trades['avg_trade_kills']:.1f}%</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Eficiência em vingar mortes de aliados</div>
                </div>
                """, unsafe_allow_html=True)

        with t3:
            if best_leetify is not None:
                prefix = "+" if best_leetify['avg_leetify_rating'] > 0 else ""
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>👑 Maior Leetify Rating:</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#ff7700;'>{best_leetify['nick']}</span> — <b>{prefix}{best_leetify['avg_leetify_rating']:.2f}%</b>
                    <div style='font-size:0.8rem; color:#94a3b8;'>Impacto geral nas vitórias de rounds</div>
                </div>
                """, unsafe_allow_html=True)
            if best_util is not None:
                st.markdown(f"""
                <div class='highlight-card'>
                    <b>💰 Menor Desperdício de Util:</b><br>
                    <span style='font-size:1.3rem; font-weight:700; color:#06b6d4;'>{best_util['nick']}</span> — <b>${best_util['avg_utility_waste']:.0f}</b> / morte
                    <div style='font-size:0.8rem; color:#94a3b8;'>Menor valor em granadas perdidas na morte</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico Radar de Habilidades (Spider Chart)
        st.subheader("🕸️ Radar de Habilidades Comparativo")
        st.caption("Selecione quais jogadores quer sobrepor no radar (dimensões normalizadas de 0 a 100).")
        
        selected_radar_players = st.multiselect(
            "Jogadores no Radar:",
            options=telemetry_df["nick"].tolist(),
            default=telemetry_df["nick"].tolist()[:3]
        )

        if selected_radar_players:
            categories = ['Tempo Reação', 'Mira / Preaim', 'Counter-Strafe', 'Spray Accuracy', 'Trade Kills', 'Dano HE']
            radar_fig = go.Figure()

            for p_nick in selected_radar_players:
                p_row = telemetry_df[telemetry_df["nick"] == p_nick].iloc[0]
                
                # Invertemos reação e preaim para que 'mais alto = melhor'
                rt_norm = max(0, min(100, 100 - (p_row['avg_reaction_time'] - 500) / 2.5))
                preaim_norm = max(0, min(100, 100 - (p_row['avg_preaim'] - 5.0) * 10))
                cs_norm = max(0, min(100, p_row['avg_counter_strafe']))
                spray_norm = max(0, min(100, p_row['avg_spray_accuracy'] * 2.2))
                trade_norm = max(0, min(100, p_row['avg_trade_kills'] * 1.5))
                he_norm = max(0, min(100, p_row['avg_he_damage'] * 5.0))

                values = [rt_norm, preaim_norm, cs_norm, spray_norm, trade_norm, he_norm, rt_norm]

                radar_fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=p_nick
                ))

            radar_fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], color="#94a3b8"),
                    bgcolor="#181d28"
                ),
                template='plotly_dark',
                plot_bgcolor='#111827',
                paper_bgcolor='#111827',
                height=450,
                margin=dict(l=40, r=40, t=30, b=30)
            )
            st.plotly_chart(radar_fig, use_container_width=True)

        # Gráfico CT vs TR
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🛡️ Lado Defensor (CT) vs ⚔️ Lado Atacante (TR)")
        st.caption("Comparativo de Rating Leetify de acordo com o lado jogado.")

        side_df = telemetry_df.melt(id_vars=["nick"], value_vars=["avg_ct_rating", "avg_t_rating"], var_name="Lado", value_name="Rating")
        side_df["Lado"] = side_df["Lado"].map({"avg_ct_rating": "Defensor (CT)", "avg_t_rating": "Atacante (TR)"})

        fig_sides = px.bar(
            side_df, x="nick", y="Rating", color="Lado", barmode="group",
            title="Impacto por Lado (CT Rating vs TR Rating)",
            color_discrete_map={"Defensor (CT)": "#38bdf8", "Atacante (TR)": "#f97316"},
            text="Rating"
        )
        fig_sides.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_sides.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=380)
        st.plotly_chart(fig_sides, use_container_width=True)

        # 4 Gráficos Técnicos
        tg1, tg2 = st.columns(2)
        with tg1:
            fig_rt = px.bar(
                telemetry_df.sort_values(by="avg_reaction_time", ascending=True),
                x="avg_reaction_time", y="nick", orientation='h',
                title="⚡ Tempo de Reação até o Dano (ms - Menor é Melhor)",
                color="avg_reaction_time", color_continuous_scale="Teal_r", text="avg_reaction_time"
            )
            fig_rt.update_traces(texttemplate='%{text:.0f} ms', textposition='outside')
            fig_rt.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
            st.plotly_chart(fig_rt, use_container_width=True)

        with tg2:
            fig_cs = px.bar(
                telemetry_df.sort_values(by="avg_counter_strafe", ascending=True),
                x="avg_counter_strafe", y="nick", orientation='h',
                title="🛑 Counter-Strafe (% Tiros Parado - Maior é Melhor)",
                color="avg_counter_strafe", color_continuous_scale="Purp", text="avg_counter_strafe"
            )
            fig_cs.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_cs.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350, xaxis_range=[60, 100])
            st.plotly_chart(fig_cs, use_container_width=True)

        tg3, tg4 = st.columns(2)
        with tg3:
            fig_flash = px.bar(
                telemetry_df.sort_values(by="avg_flash_duration", ascending=True),
                x="avg_flash_duration", y="nick", orientation='h',
                title="✨ Duração de Cegueira por Flashbang no Inimigo (segundos)",
                color="avg_flash_duration", color_continuous_scale="YlOrBr", text="avg_flash_duration"
            )
            fig_flash.update_traces(texttemplate='%{text:.2f}s', textposition='outside')
            fig_flash.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
            st.plotly_chart(fig_flash, use_container_width=True)

        with tg4:
            fig_waste = px.bar(
                telemetry_df.sort_values(by="avg_utility_waste", ascending=True),
                x="avg_utility_waste", y="nick", orientation='h',
                title="💸 Desperdício de Utilitários ao Morrer ($ - Menor é Melhor)",
                color="avg_utility_waste", color_continuous_scale="Reds_r", text="avg_utility_waste"
            )
            fig_waste.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
            fig_waste.update_layout(template='plotly_dark', plot_bgcolor='#111827', paper_bgcolor='#111827', height=350)
            st.plotly_chart(fig_waste, use_container_width=True)

        # Tabela Completa
        st.markdown("### 📋 Tabela Geral de Telemetria e Mira")
        t_cols = [
            "nick", "analyzed_matches", "avg_leetify_rating", "avg_reaction_time",
            "avg_preaim", "avg_spray_accuracy", "avg_counter_strafe", "avg_trade_kills",
            "avg_traded_deaths", "avg_flash_duration", "avg_he_damage", "avg_utility_waste"
        ]
        t_rename = {
            "nick": "Jogador",
            "analyzed_matches": "Partidas Analisadas",
            "avg_leetify_rating": "Leetify Rating (%)",
            "avg_reaction_time": "Tempo Reação (ms)",
            "avg_preaim": "Preaim (° erro)",
            "avg_spray_accuracy": "Spray Acc (%)",
            "avg_counter_strafe": "Counter-Strafe (%)",
            "avg_trade_kills": "Trade Kills (%)",
            "avg_traded_deaths": "Traded Deaths (%)",
            "avg_flash_duration": "Flash Inimigo (s)",
            "avg_he_damage": "Dano HE (HP)",
            "avg_utility_waste": "Desperdício Util ($)"
        }
        st.dataframe(telemetry_df[t_cols].rename(columns=t_rename).reset_index(drop=True), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: PERFIL INDIVIDUAL DETALHADO
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
                <div class='metric-sub'>{int(p['kills']):,} Kills / {int(p['deaths']):,} D</div>
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
                <div class='metric-title'>Abates / Jogo</div>
                <div class='metric-value'>{p['kills_per_match']:.1f}</div>
                <div class='metric-sub'>Total: {int(p['kills']):,} kills</div>
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
        st.markdown(f"#### 🎯 Volume Absoluto vs Médias por Partida de {p['nick']}")
        ip1, ip2, ip3, ip4 = st.columns(4)
        with ip1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>First Kills (Opening)</div>
                <div class='metric-value'>{int(p['first_kills']):,}</div>
                <div class='metric-sub'>Média: <b>{p['first_kills_per_match']:.2f}</b> por jogo</div>
            </div>
            """, unsafe_allow_html=True)
        with ip2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Multi Kills (2k+)</div>
                <div class='metric-value'>{int(p['multi_kills']):,}</div>
                <div class='metric-sub'>Média: <b>{p['multi_kills_per_match']:.2f}</b> por jogo</div>
            </div>
            """, unsafe_allow_html=True)
        with ip3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bombas Plantadas</div>
                <div class='metric-value' style='color:#f59e0b;'>{int(p['bomb_plants']):,}</div>
                <div class='metric-sub'>Média: <b>{p['plants_per_match']:.2f}</b> por jogo</div>
            </div>
            """, unsafe_allow_html=True)
        with ip4:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Bombas Defusadas</div>
                <div class='metric-value' style='color:#10b981;'>{int(p['bomb_defuses']):,}</div>
                <div class='metric-sub'>Média: <b>{p['defuses_per_match']:.2f}</b> por jogo</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_hist, col_hit = st.columns([2, 1])
        with col_hist:
            st.subheader(f"📈 Evolução Mês a Mês de {p['nick']}")
            try:
                p_history = get_player_history(pid, platform=platform_filter)
            except TypeError:
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

        # Telemetria Individual do Jogador
        try:
            p_tel_df = get_telemetry_stats(month=month_filter, platform=platform_filter)
            p_tel = p_tel_df[p_tel_df["nick"] == p['nick']]
        except Exception:
            p_tel = pd.DataFrame()

        if not p_tel.empty:
            pt = p_tel.iloc[0]
            st.markdown(f"#### 🎯 Telemetria Avançada & Mira de {p['nick']}")
            t_c1, t_c2, t_c3, t_c4, t_c5, t_c6 = st.columns(6)
            with t_c1:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Tempo Reação</div>
                    <div class='metric-value'>{pt['avg_reaction_time']:.0f} ms</div>
                    <div class='metric-sub'>Até causar dano</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c2:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Preaim (Mira)</div>
                    <div class='metric-value'>{pt['avg_preaim']:.1f}°</div>
                    <div class='metric-sub'>Erro de abertura</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c3:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Counter-Strafe</div>
                    <div class='metric-value'>{pt['avg_counter_strafe']:.1f}%</div>
                    <div class='metric-sub'>Tiros parado</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c4:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Trade Kills</div>
                    <div class='metric-value'>{pt['avg_trade_kills']:.1f}%</div>
                    <div class='metric-sub'>Vingou aliado</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c5:
                prefix = "+" if pt['avg_leetify_rating'] > 0 else ""
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Leetify Rating</div>
                    <div class='metric-value'>{prefix}{pt['avg_leetify_rating']:.2f}%</div>
                    <div class='metric-sub'>CT: {pt['avg_ct_rating']:.2f}% | TR: {pt['avg_t_rating']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c6:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Desperdício Util</div>
                    <div class='metric-value'>${pt['avg_utility_waste']:.0f}</div>
                    <div class='metric-sub'>Perdido na morte</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

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
    'mch': 89302,
    'The merdas': 2502581,
    'Coquinha': 2492447,
    'Allan Daniel': 2650509,
    'Daniel': 2734005
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
    try:
        matches_df = get_matches_by_month(month_filter, target_map_pid, platform=platform_filter)
    except TypeError:
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
    try:
        matches_df = get_matches_by_month(month_filter, target_match_pid, platform=platform_filter)
    except TypeError:
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
                plat = first.get("platform", "GC")
                mtype = first.get("match_type", "lobby")
                plat_badge = "🏅 GC" if plat == "GC" else ("🎯 Premier" if mtype == "premier" else "🎯 Steam MM")
                clean_id = str(mid).replace("steam_", "")[:10] + "..." if str(mid).startswith("steam_") else str(mid)
                grouped_records.append({
                    "match_id": clean_id,
                    "plataforma": plat_badge,
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
            cols = ["match_id", "plataforma", "resultado", "map", "placar", "jogadores"]
            renamed = {
                "match_id": "ID Partida",
                "plataforma": "Plataforma",
                "resultado": "Resultado",
                "map": "Mapa",
                "placar": "Placar",
                "jogadores": "Jogadores Presentes"
            }
            st.dataframe(m_display[cols].rename(columns=renamed), use_container_width=True)
        else:
            st.caption(f"Mostrando **{len(matches_df)}** partidas registradas para {selected_p_match}.")
            m_display = matches_df.copy()
            m_display["plataforma"] = m_display.apply(
                lambda r: "🏅 GC" if r.get("platform") == "GC" else ("🎯 Premier" if r.get("match_type") == "premier" else "🎯 Steam MM"),
                axis=1
            )
            m_display["clean_id"] = m_display["match_id"].apply(
                lambda x: str(x).replace("steam_", "")[:10] + "..." if str(x).startswith("steam_") else str(x)
            )
            m_display["resultado"] = m_display["win"].apply(lambda w: "🏆 Vitória" if w == 1 else "❌ Derrota")
            m_display["placar"] = m_display.apply(lambda r: f"{r['score_a']} x {r['score_b']}", axis=1)
            m_display["diff"] = m_display["rating_diff"].apply(lambda d: f"+{d}" if d > 0 else (str(d) if d != 0 else "-"))

            has_steam_stats = m_display["kills"].sum() > 0
            has_telemetry = "reaction_time" in m_display.columns and m_display["reaction_time"].sum() > 0
            if has_telemetry:
                m_display["rt_fmt"] = m_display["reaction_time"].apply(lambda v: f"{int(v)} ms" if v > 0 else "-")
                m_display["cs_fmt"] = m_display["counter_strafe_pct"].apply(lambda v: f"{v:.1f}%" if v > 0 else "-")
                m_display["lr_fmt"] = m_display["leetify_rating"].apply(lambda v: f"{'+' if v > 0 else ''}{v:.2f}%" if v != 0 else "-")
                cols = ["clean_id", "plataforma", "resultado", "map", "placar", "kills", "deaths", "adr", "lr_fmt", "rt_fmt", "cs_fmt"]
                renamed = {
                    "clean_id": "ID Partida",
                    "plataforma": "Plataforma",
                    "resultado": "Resultado",
                    "map": "Mapa",
                    "placar": "Placar",
                    "kills": "Kills",
                    "deaths": "Deaths",
                    "adr": "ADR",
                    "lr_fmt": "Leetify Rating",
                    "rt_fmt": "Reação",
                    "cs_fmt": "Counter-Strafe"
                }
            elif has_steam_stats:
                cols = ["clean_id", "plataforma", "resultado", "map", "placar", "kills", "deaths", "adr", "diff"]
                renamed = {
                    "clean_id": "ID Partida",
                    "plataforma": "Plataforma",
                    "resultado": "Resultado",
                    "map": "Mapa",
                    "placar": "Placar",
                    "kills": "Kills",
                    "deaths": "Deaths",
                    "adr": "ADR",
                    "diff": "Pontos (RP)"
                }
            else:
                cols = ["clean_id", "plataforma", "resultado", "map", "placar", "team_name_a", "team_name_b", "rating_player", "diff"]
                renamed = {
                    "clean_id": "ID Partida",
                    "plataforma": "Plataforma",
                    "resultado": "Resultado",
                    "map": "Mapa",
                    "placar": "Placar",
                    "team_name_a": "Time A",
                    "team_name_b": "Time B",
                    "rating_player": "Rating Final",
                    "diff": "Pontos (RP)"
                }
            st.dataframe(m_display[cols].rename(columns=renamed), use_container_width=True)


    # -------------------------------------------------------------------------
    # INSPECTOR DE PARTIDA: SCOREBOARD COMPLETO NO FORMATO OFICIAL GAMERS CLUB
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔍 Detalhes da Partida (Interface Oficial da Gamers Club)")
    st.caption("Selecione uma partida para ver o scoreboard completo com as abas idênticas à Gamers Club: Geral, Entries, Trades, Clutch, Utilitárias e Mira.")

    all_match_ids = matches_df["match_id"].dropna().unique().tolist()
    if all_match_ids:
        def format_match_label(mid):
            rows_m = matches_df[matches_df["match_id"] == mid]
            if rows_m.empty:
                return str(mid)
            r0 = rows_m.iloc[0]
            res_str = "🏆 Vitória" if r0.get("win") == 1 else "❌ Derrota"
            score_str = f"{r0.get('score_a', 0)} x {r0.get('score_b', 0)}"
            map_str = r0.get("map", "")
            plat_str = "🏅 GC" if r0.get("platform") == "GC" else "🎯 Steam"
            return f"{plat_str} • {map_str} ({score_str}) • {res_str} • ID: {mid}"

        c_sel_m, c_act_m = st.columns([3, 1])
        with c_sel_m:
            chosen_mid = st.selectbox(
                "Selecione uma partida para inspecionar:",
                options=all_match_ids[:30],
                format_func=format_match_label,
                key="gc_match_selector"
            )

        if chosen_mid:
            sb_data = get_gc_match_scoreboard(str(chosen_mid))
            with c_act_m:
                st.write("")
                st.write("")
                if st.button("🔄 Atualizar Stats Desta Partida", use_container_width=True, key=f"btn_rf_{chosen_mid}"):
                    with st.spinner("Buscando na Gamers Club..."):
                        from collector import load_config, GamersClubCollector
                        c_coll = GamersClubCollector(load_config())
                        ok_fetch = c_coll.fetch_and_save_gc_match_stats(str(chosen_mid))
                        if ok_fetch:
                            st.success("✅ Partida atualizada!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Estatísticas detalhadas indisponíveis para esta partida.")

            if sb_data.empty:
                st.info(f"ℹ️ As novas abas detalhadas da GC ainda não foram sincronizadas para a partida #{chosen_mid}. Clique no botão acima para sincronizar!")
            else:
                m_info_rows = matches_df[matches_df["match_id"] == chosen_mid]
                m_first = m_info_rows.iloc[0] if not m_info_rows.empty else None
                m_map = m_first.get("map", "") if m_first is not None else ""
                s_a = m_first.get("score_a", 0) if m_first is not None else 0
                s_b = m_first.get("score_b", 0) if m_first is not None else 0
                t_a_name = m_first.get("team_name_a", "Time A") if m_first is not None else "Time A"
                t_b_name = m_first.get("team_name_b", "Time B") if m_first is not None else "Time B"

                st.markdown(f"""
                <div style='background:linear-gradient(90deg, #181d28 0%, #1e293b 100%); border:1px solid #334155; border-radius:10px; padding:12px 18px; margin-bottom:12px;'>
                    <span style='font-size:1.3rem; font-weight:800; color:#f8fafc;'>{m_map}</span> &nbsp;•&nbsp; 
                    <span style='font-size:1.4rem; font-weight:800; color:#ff7700;'>{s_a}</span> <span style='color:#94a3b8;'>x</span> <span style='font-size:1.4rem; font-weight:800; color:#38bdf8;'>{s_b}</span> &nbsp;•&nbsp; 
                    <span style='color:#94a3b8;'>{t_a_name} vs {t_b_name}</span>
                </div>
                """, unsafe_allow_html=True)

                # 6 Abas idênticas à interface oficial da Gamers Club
                m_tab_geral, m_tab_entries, m_tab_trades, m_tab_clutch, m_tab_utility, m_tab_aim = st.tabs([
                    "📊 GERAL",
                    "🚪 ENTRIES",
                    "🔄 TRADES",
                    "🏆 CLUTCH",
                    "💣 UTILITÁRIAS",
                    "🎯 MIRA"
                ])

                for team_code in ["A", "B"]:
                    team_players = sb_data[sb_data["team"] == team_code].copy()
                    if team_players.empty:
                        continue
                    t_title = t_a_name if team_code == "A" else t_b_name
                    score_team = s_a if team_code == "A" else s_b
                    accent_color = "#ff7700" if team_code == "A" else "#38bdf8"

                    team_header_html = f"""
                    <div style='background:#111827; border-left:4px solid {accent_color}; padding:8px 14px; border-radius:6px; margin-top:14px; margin-bottom:8px; font-weight:700; font-size:1.05rem; color:#f8fafc;'>
                        {score_team} &nbsp; {t_title}
                    </div>
                    """

                    def prep_p(df_in):
                        p_df = df_in.copy()
                        p_df["Jogador"] = p_df.apply(lambda r: f"⭐ {r['nick']}" if r['is_core_squad'] == 1 else r['nick'], axis=1)
                        p_df["Nível"] = p_df["level"].apply(lambda l: f"Lv {int(l)}" if pd.notnull(l) else "-")
                        return p_df

                    with m_tab_geral:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        g_df = prep_p(team_players)
                        g_df["DIFF"] = g_df.apply(lambda r: f"+{r['kills'] - r['deaths']}" if (r['kills'] - r['deaths']) > 0 else str(r['kills'] - r['deaths']), axis=1)
                        g_df["KAST"] = g_df["kast"].apply(lambda v: f"{v:.0f}%")
                        g_df["GC RATING"] = g_df["gc_rating"].apply(lambda v: f"{v:.2f}")
                        cols_g = ["Jogador", "Nível", "kills", "assists", "deaths", "DIFF", "adr", "kdr", "KAST", "GC RATING"]
                        ren_g = {"kills": "K", "assists": "A", "deaths": "D", "adr": "ADR", "kdr": "KDR"}
                        st.dataframe(g_df[cols_g].rename(columns=ren_g).reset_index(drop=True), use_container_width=True)

                    with m_tab_entries:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        en_df = prep_p(team_players)
                        en_df["DUELOS DE ABERTURA"] = en_df["entry_duels"]
                        en_df["VENCIDOS"] = en_df["entry_won"]
                        en_df["PERDIDOS"] = en_df["entry_lost"]
                        en_df["SUCESSO"] = en_df["entry_success_rate"].apply(lambda v: f"{v:.0f}%")
                        en_df["ABERTURAS/ROUND"] = en_df["entry_per_round"].apply(lambda v: f"{v:.2f}")
                        cols_en = ["Jogador", "Nível", "DUELOS DE ABERTURA", "VENCIDOS", "PERDIDOS", "SUCESSO", "ABERTURAS/ROUND"]
                        st.dataframe(en_df[cols_en].reset_index(drop=True), use_container_width=True)

                    with m_tab_trades:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        tr_df = prep_p(team_players)
                        tr_df["TRADES FEITOS"] = tr_df["trades_made"]
                        tr_df["MORTES TROCADAS"] = tr_df["traded_deaths"]
                        tr_df["TAXA DE TROCA"] = tr_df["trade_rate"].apply(lambda v: f"{v:.0f}%")
                        tr_df["TEMPO MÉDIO"] = tr_df["trade_avg_time"].apply(lambda v: f"{v:.1f}s")
                        cols_tr = ["Jogador", "Nível", "TRADES FEITOS", "MORTES TROCADAS", "TAXA DE TROCA", "TEMPO MÉDIO"]
                        st.dataframe(tr_df[cols_tr].reset_index(drop=True), use_container_width=True)

                    with m_tab_clutch:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        cl_df = prep_p(team_players)
                        cl_df["SITUAÇÕES"] = cl_df["clutch_situations"]
                        cl_df["VENCIDOS"] = cl_df["clutch_won"]
                        cl_df["APROVEITAMENTO"] = cl_df["clutch_rate"].apply(lambda v: f"{v:.0f}%")
                        cl_df["1V1"] = cl_df.apply(lambda r: f"{int(r['clutch_1v1_won'])}/{int(r['clutch_1v1_total'])}", axis=1)
                        cl_df["1VN"] = cl_df.apply(lambda r: f"{int(r['clutch_1vn_won'])}/{int(r['clutch_1vn_total'])}", axis=1)
                        cl_df["MAIOR VIRADA"] = cl_df["clutch_biggest"].fillna("-")
                        cols_cl = ["Jogador", "Nível", "SITUAÇÕES", "VENCIDOS", "APROVEITAMENTO", "1V1", "1VN", "MAIOR VIRADA"]
                        st.dataframe(cl_df[cols_cl].reset_index(drop=True), use_container_width=True)

                    with m_tab_utility:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        ut_df = prep_p(team_players)
                        ut_df["DANO DE UTILITÁRIA"] = ut_df["utility_damage"]
                        ut_df["FLASH ASSIST"] = ut_df["flash_assists"]
                        ut_df["INIMIGOS CEGADOS"] = ut_df["enemies_flashed"]
                        ut_df["GRANADAS"] = ut_df["grenades_thrown"]
                        ut_df["DANO POR GRANADA"] = ut_df["damage_per_grenade"].apply(lambda v: f"{v:.1f}")
                        cols_ut = ["Jogador", "Nível", "DANO DE UTILITÁRIA", "FLASH ASSIST", "INIMIGOS CEGADOS", "GRANADAS", "DANO POR GRANADA"]
                        st.dataframe(ut_df[cols_ut].reset_index(drop=True), use_container_width=True)

                    with m_tab_aim:
                        st.markdown(team_header_html, unsafe_allow_html=True)
                        ai_df = prep_p(team_players)
                        ai_df["PRECISÃO"] = ai_df["aim_accuracy"].apply(lambda v: f"{v:.0f}%")
                        ai_df["HS%"] = ai_df["aim_hs_rate"].apply(lambda v: f"{v:.0f}%")
                        ai_df["HEAD ACC."] = ai_df["aim_head_acc"].apply(lambda v: f"{v:.0f}%")
                        ai_df["ABATES/ROUND"] = ai_df["aim_kpr"].apply(lambda v: f"{v:.2f}")
                        ai_df["ARMA PRINCIPAL"] = ai_df["main_weapon"].fillna("-")
                        cols_ai = ["Jogador", "Nível", "PRECISÃO", "HS%", "HEAD ACC.", "ABATES/ROUND", "ARMA PRINCIPAL"]
                        st.dataframe(ai_df[cols_ai].reset_index(drop=True), use_container_width=True)
