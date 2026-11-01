// =====================================================================
// SCRIPT DE EXTRAÇÃO DE PARTIDAS STEAM GCPD (PREMIER & COMPETITIVO)
// =====================================================================
// COMO USAR:
// 1. Abra no navegador: https://steamcommunity.com/my/gcpd/730/?tab=matchhistorypremier
// 2. Abra o Console do desenvolvedor (F12 ou Ctrl+Shift+I -> aba 'Console').
// 3. Cole todo este código e aperte ENTER.
// 4. Um arquivo 'steam_matches.json' será baixado automaticamente!
// =====================================================================

(function() {
    console.log("🎮 Iniciando extração das partidas da Steam...");
    
    const tables = document.querySelectorAll('table.generic_kv_table');
    if (tables.length === 0) {
        alert("Nenhuma tabela de partidas encontrada! Certifique-se de estar na aba 'Partidas Premier' ou 'Partidas Competitivas'.");
        return;
    }

    const matches = [];
    const mapNames = ["mirage", "inferno", "dust", "nuke", "overpass", "anubis", "ancient", "vertigo", "office", "train"];

    tables.forEach((table, idx) => {
        try {
            const fullText = table.parentElement ? table.parentElement.innerText : table.innerText;
            
            // 1. Data da partida (ex: 2024-03-15 21:30:10)
            const dateMatch = fullText.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})/);
            if (!dateMatch) return;
            const matchDate = dateMatch[1];

            // 2. Mapa
            let mapName = "de_unknown";
            for (const m of mapNames) {
                if (fullText.toLowerCase().includes(m)) {
                    mapName = "de_" + (m === "dust" ? "dust2" : m);
                    break;
                }
            }

            // 3. Placar (ex: 13 : 9)
            const scoreMatch = fullText.match(/(\d{1,2})\s*[:xX\-]\s*(\d{1,2})/);
            const scoreA = scoreMatch ? parseInt(scoreMatch[1]) : 0;
            const scoreB = scoreMatch ? parseInt(scoreMatch[2]) : 0;

            // 4. Jogadores presentes na partida
            const players = [];
            const container = table.parentElement || table;
            
            container.querySelectorAll('a[href*="steamcommunity.com"]').forEach(a => {
                const name = a.innerText.trim();
                const href = a.href;
                const sidMatch = href.match(/profiles\/(\d+)/);
                const sid = sidMatch ? sidMatch[1] : null;

                if (name && name.length > 0 && !name.includes("Download") && !name.includes("Baixar")) {
                    // Tenta capturar linha de estatísticas (Kills / Deaths)
                    let kills = 0, deaths = 0, assists = 0;
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
            console.error("Erro ao analisar partida:", err);
        }
    });

    console.log(`✅ Sucesso! ${matches.length} partidas encontradas.`);
    
    // Baixa o arquivo JSON
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(matches, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "steam_matches.json");
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();

    alert(`🎉 Extração concluída com sucesso!\n\n${matches.length} partidas foram exportadas para o arquivo 'steam_matches.json'.\nBasta colocar esse arquivo na pasta do projeto ou enviá-lo pelo Dashboard!`);
})();
