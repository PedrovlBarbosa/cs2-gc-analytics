# 🎯 CS2 Gamers Club - Analytics & Dashboard

Sistema automatizado para coleta, armazenamento e visualização interativa das estatísticas de partidas de CS2 na **Gamers Club (GC)**, com foco no desempenho mês a mês seu e de todos os seus companheiros de equipe.

---

## 📁 Estrutura do Projeto

```text
estatisticas/
├── config.json          # Configuração do seu ID, Nick e Cookies de autenticação da GC
├── database.py          # Módulo de banco de dados SQLite (criação de tabelas, inserção e consultas)
├── collector.py         # Script de coleta da Gamers Club (perfil, amigos, dados mensais e partidas)
├── app.py               # Dashboard interativo em Streamlit com visual moderno e gráficos Plotly
├── gc_stats.db          # Banco de dados local SQLite gerado
└── requirements.txt     # Dependências do projeto (requests, pandas, plotly, streamlit)
```

---

## 🚀 Como Executar

### 1. Iniciar o Dashboard Interativo

Para abrir o painel web no navegador:

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente em `http://localhost:8501`.

### 2. Atualizar ou Coletar Mais Dados

Para sincronizar novas partidas e atualizar os últimos meses (padrão 12 meses):

```bash
python collector.py
```

Para coletar um número específico de meses recentes (ex: últimos 3 meses ou todos os 64 meses):

```bash
python collector.py 3
python collector.py 64
```

---

## 🔑 Como Renovar os Cookies no Futuro

Quando os cookies expirarem (caso a sessão na GC feche):
1. Acesse `https://gamersclub.com.br` logado com sua conta Steam.
2. Abra o Console do Navegador (**F12** ou botão direito $\rightarrow$ Inspecionar).
3. Vá na aba **Application (Armazenamento)** $\rightarrow$ **Cookies** $\rightarrow$ `gamersclub.com.br`.
4. Copie o valor de `gclubsess` e `cf_clearance`.
5. Cole-os no arquivo `config.json`.

---

## 📊 Recursos do Dashboard

1. **Visão Geral Mensal:**
   * Cards com **Partidas, Win Rate %, KDR, ADR Médio, Kills / Mortes e HS%**.
   * Gráfico de linha interativo da evolução mês a mês.
   * Gráfico de distribuição de acertos por parte do corpo (Hitbox: Cabeça, Peito, etc.).
2. **Comparativo de Companheiros (Squad):**
   * Destaques de **Top Fragger**, **Maior Dano (Top ADR)** e **Mais Jogos no Mês**.
   * Gráficos de barras horizontais comparativos de ADR e KDR.
   * Tabela consolidada com todas as métricas dos companheiros no mês selecionado.
3. **Análise de Mapas:**
   * Volume de vitórias e derrotas por mapa jogado.
   * Taxa de vitória (%) por mapa (Dust2, Mirage, Cache, etc.).
4. **Partidas do Mês:**
   * Tabela com placares, variação de rating (RP), adversários e resultados.
