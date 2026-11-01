// =====================================================================
// ROBO DE AUTO-CARREGAMENTO E EXTRAÇÃO - STEAM GCPD (CS2)
// =====================================================================
// COMO USAR:
// 1. Abra no navegador: https://steamcommunity.com/my/gcpd/730/?tab=matchhistorypremier
// 2. Abra o Console (F12 ou Ctrl+Shift+I -> aba 'Console').
// 3. Cole todo este código e aperte ENTER.
// 4. O robô vai CLICAR SOZINHO repetidamente até carregar todo o histórico
//    (ou até 2023) e vai BAIXAR o arquivo 'steam_matches.json' automaticamente!
// =====================================================================

(async function autoExtractSteamHistory() {
    console.log("🚀 Iniciando Robô de Auto-Carregamento da Steam...");

    // Cria um painel visual flutuante na tela para você acompanhar
    let overlay = document.getElementById("steam_auto_extract_overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "steam_auto_extract_overlay";
        overlay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(15, 23, 42, 0.95);
            color: #f8fafc;
            border: 2px solid #38bdf8;
            padding: 16px 20px;
            border-radius: 12px;
            z-index: 999999;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            min-width: 280px;
        `;
        document.body.appendChild(overlay);
    }

    let shouldStop = false;

    overlay.innerHTML = `
        <div style="font-weight: bold; font-size: 15px; margin-bottom: 8px; color: #38bdf8;">
            🤖 Robô Steam Auto-Clicker
        </div>
        <div id="steam_auto_status" style="margin-bottom: 12px; color: #94a3b8;">
            Iniciando auto-cliques...
        </div>
        <button id="steam_stop_btn" style="
            background: #ef4444; color: white; border: none; padding: 6px 12px;
            border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%;
        ">🛑 Parar e Baixar Agora</button>
    `;

    document.getElementById("steam_stop_btn").onclick = () => {
        shouldStop = true;
        document.getElementById("steam_auto_status").innerText = "Parando e gerando arquivo...";
    };

    let clicks = 0;
    const TARGET_YEAR = 2023; // Para quando alcançar partidas de 2023

    while (!shouldStop) {
        const tables = document.querySelectorAll('table.generic_kv_table');
        const loadBtn = document.getElementById('load_more_button');

        // Atualiza status visual
        const statusEl = document.getElementById("steam_auto_status");
        if (statusEl) {
            statusEl.innerHTML = `
                ⏳ Cliques realizados: <b>${clicks}</b><br>
                📊 Partidas carregadas: <b>${tables.length}</b>
            `;
        }

        // Verifica se alcançou partidas do ano alvo
        const text = document.body.innerText;
        if (text.includes(`\n${TARGET_YEAR}-`) || text.includes(` ${TARGET_YEAR}-`)) {
            console.log(`🎯 Ano ${TARGET_YEAR} alcançado!`);
            break;
        }

        // Verifica se o botão de carregar mais ainda existe e está visível
        if (!loadBtn || loadBtn.offsetParent === null || loadBtn.style.display === 'none' || loadBtn.classList.contains('disabled')) {
            console.log("🏁 Fim do histórico alcançado (botão sumiu)!");
            break;
        }

        // Clica no botão
        loadBtn.click();
        clicks++;

        // Aguarda a resposta da Steam (900ms para ser rápido e seguro)
        await new Promise(r => setTimeout(r, 900));

        // Rola suavemente até o final da página para garantir visibilidade
        window.scrollTo(0, document.body.scrollHeight);
    }

    // Processa a extração dos dados
    const statusEl = document.getElementById("steam_auto_status");
    if (statusEl) statusEl.innerHTML = "⚡ Extraindo dados das partidas...";

    const matches = [];
    const tables = document.querySelectorAll('table.generic_kv_table');
    const mapNames = ["mirage", "inferno", "dust", "nuke", "overpass", "anubis", "ancient", "vertigo", "office", "train"];

    tables.forEach((table, idx) => {
        try {
            const container = table.parentElement || table;
            const fullText = container.innerText;

            const dateMatch = fullText.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})/);
            if (!dateMatch) return;
            const matchDate = dateMatch[1];

            let mapName = "de_unknown";
            for (const m of mapNames) {
                if (fullText.toLowerCase().includes(m)) {
                    mapName = "de_" + (m === "dust" ? "dust2" : m);
                    break;
                }
            }

            const scoreMatch = fullText.match(/(\d{1,2})\s*[:xX\-]\s*(\d{1,2})/);
            const scoreA = scoreMatch ? parseInt(scoreMatch[1]) : 0;
            const scoreB = scoreMatch ? parseInt(scoreMatch[2]) : 0;

            const players = [];
            container.querySelectorAll('a[href*="steamcommunity.com"]').forEach(a => {
                const name = a.innerText.trim();
                const href = a.href;
                const sidMatch = href.match(/profiles\/(\d+)/);
                const sid = sidMatch ? sidMatch[1] : null;

                if (name && name.length > 0 && !name.includes("Download") && !name.includes("Baixar")) {
                    let kills = 0, deaths = 0;
                    const tr = a.closest('tr');
                    if (tr) {
                        const tds = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                        const nums = tds.map(t => parseInt(t)).filter(n => !isNaN(n));
                        if (nums.length >= 3) {
                            kills = nums[1] || 0;
                            deaths = nums[3] !== undefined ? nums[3] : (nums[2] || 0);
                        }
                    }

                    players.push({
                        name: name,
                        steam_id: sid,
                        kills: kills,
                        deaths: deaths
                    });
                }
            });

            matches.push({
                id: `steam_gcpd_${matchDate.replace(/-/g, '')}_${idx}`,
                date: matchDate,
                month: matchDate.slice(0, 7),
                map: mapName,
                score_a: scoreA,
                score_b: scoreB,
                players: players
            });
        } catch (err) {
            console.error("Erro na partida:", err);
        }
    });

    // Baixa o arquivo JSON
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(matches, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "steam_matches.json");
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();

    if (overlay) {
        overlay.style.borderColor = "#10b981";
        overlay.innerHTML = `
            <div style="font-weight: bold; font-size: 15px; color: #10b981; margin-bottom: 6px;">
                🎉 Extração Concluída!
            </div>
            <div style="color: #cbd5e1; font-size: 13px;">
                <b>${matches.length}</b> partidas foram extraídas!<br>
                Arquivo <b>steam_matches.json</b> baixado.<br><br>
                Agora envie esse arquivo no Dashboard!
            </div>
        `;
    }
})();
