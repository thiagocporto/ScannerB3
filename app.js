document.addEventListener('DOMContentLoaded', async () => {
    const formatador = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
    let ativosCache = [];
    
    try {
        const response = await fetch('banco_painel.json');
        const data = await response.json();
        ativosCache = data.ativos;
        
        const dataRef = new Date(data.atualizacao);
        document.getElementById('label-atualizacao').textContent = `Atualizado em: ${dataRef.toLocaleString('pt-BR')}`;
        document.getElementById('label-total').textContent = data.total;
        
        renderizarTabela(ativosCache);
        renderizarGraficos(ativosCache);
    } catch (e) {
        console.error("Erro ao carregar dados", e);
    }

    document.getElementById('filtro').addEventListener('input', (e) => {
        const termo = e.target.value.toUpperCase();
        const filtrados = ativosCache.filter(a => a.ticker.includes(termo));
        renderizarTabela(filtrados);
    });

    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const key = th.dataset.sort;
            ativosCache.sort((a, b) => a[key] > b[key] ? 1 : -1);
            renderizarTabela(ativosCache);
        });
    });

    function renderizarTabela(ativos) {
        const tbody = document.getElementById('corpoTabela');
        tbody.innerHTML = '';
        
        ativos.forEach(ativo => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-800/40 transition-colors border-b border-gray-800';
            
            const tdTicker = document.createElement('td');
            tdTicker.className = 'px-4 py-3.5 font-bold text-white tracking-wide';
            tdTicker.textContent = ativo.ticker;
            
            const tdPreco = document.createElement('td');
            tdPreco.className = 'px-4 py-3.5 text-right font-medium text-gray-100';
            tdPreco.textContent = formatador.format(ativo.preco);
            
            const tdSma = document.createElement('td');
            tdSma.className = 'px-4 py-3.5 text-right text-gray-400';
            tdSma.textContent = formatador.format(ativo.sma200);
            
            const tdIfr = document.createElement('td');
            tdIfr.className = `px-4 py-3.5 text-right font-bold ${ativo.ifr2 <= 15 ? 'text-green-400' : (ativo.ifr2 >= 85 ? 'text-red-400' : 'text-gray-300')}`;
            tdIfr.textContent = ativo.ifr2.toLocaleString('pt-BR');

            const tdConnors = document.createElement('td');
            tdConnors.className = 'px-4 py-3.5 text-right font-semibold text-yellow-400';
            tdConnors.textContent = ativo.connors.toLocaleString('pt-BR');
            
            const tdFase = document.createElement('td');
            tdFase.className = 'px-4 py-3.5 text-center';
            const spanFase = document.createElement('span');
            spanFase.textContent = ativo.fase_label;
            spanFase.className = `px-3 py-1 text-xs font-medium rounded-full bg-gray-800/80 border border-blue-500/30 text-blue-300`;
            tdFase.appendChild(spanFase);

            const tdScore = document.createElement('td');
            tdScore.className = 'px-4 py-3.5 text-center text-xs font-semibold';
            if(ativo.score_label === 'Excelente' || ativo.score_label === 'Bom') {
                tdScore.className += ' text-green-400';
            } else if (ativo.score_label === 'Fraco') {
                tdScore.className += ' text-red-400';
            } else {
                tdScore.className += ' text-yellow-400';
            }
            tdScore.textContent = `${ativo.score} (${ativo.score_label})`;
            
            const tdBtn = document.createElement('td');
            tdBtn.className = 'px-4 py-3.5 text-center';
            const btn = document.createElement('button');
            btn.innerHTML = `<span class="w-2 h-2 rounded-full inline-block mr-1.5" id="led-${ativo.ticker}"></span>Tese IA`;
            
            let corClasse = 'border-gray-500 text-gray-300 bg-gray-600/30';
            let corLed = '#64748b';

            if (ativo.sinal_ia === 'COMPRA') {
                corClasse = 'border-green-500 text-green-300 bg-green-900/30 shadow-[0_0_8px_rgba(16,185,129,0.3)]';
                corLed = '#10b981';
            }
            if (ativo.sinal_ia === 'VENDA') {
                corClasse = 'border-red-500 text-red-300 bg-red-900/30 shadow-[0_0_8px_rgba(244,63,94,0.3)]';
                corLed = '#f43f5e';
            }
            if (ativo.sinal_ia === 'NEUTRO') {
                corClasse = 'border-yellow-500 text-yellow-300 bg-yellow-900/30 shadow-[0_0_8px_rgba(245,158,11,0.3)]';
                corLed = '#f59e0b';
            }
            
            btn.className = `px-3 py-1 text-xs font-bold rounded cursor-pointer transition-transform hover:scale-105 border ${corClasse} inline-flex items-center`;
            btn.dataset.parecer = ativo.parecer_ia;
            btn.dataset.ticker = ativo.ticker;
            
            btn.addEventListener('click', () => abrirModal(btn.dataset.ticker, btn.dataset.parecer));
            tdBtn.appendChild(btn);
            
            tr.append(tdTicker, tdPreco, tdSma, tdIfr, tdConnors, tdFase, tdScore, tdBtn);
            tbody.appendChild(tr);

            document.getElementById(`led-${ativo.ticker}`).style.backgroundColor = corLed;
            document.getElementById(`led-${ativo.ticker}`).style.boxShadow = `0 0 6px ${corLed}`;
        });
    }

    const modal = document.getElementById('modalTese');
    document.getElementById('btnFecharModal').addEventListener('click', () => modal.close());
    document.getElementById('btnFecharModal2').addEventListener('click', () => modal.close());
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.close(); });
    
    function abrirModal(ticker, texto) {
        document.getElementById('modalTitle').innerHTML = `Tese Institucional: #${ticker}`;
        document.getElementById('modalContent').textContent = texto;
        modal.showModal();
    }

    function renderizarGraficos(ativos) {
        // Grafico Donut
        const freqFases = {};
        ativos.forEach(a => freqFases[a.fase_label] = (freqFases[a.fase_label] || 0) + 1);
        
        new Chart(document.getElementById('chartDonut'), {
            type: 'doughnut',
            data: {
                labels: Object.keys(freqFases),
                datasets: [{
                    data: Object.values(freqFases),
                    backgroundColor: ['#10b981', '#f59e0b', '#a855f7', '#f43f5e', '#64748b', '#38bdf8', '#fb7185'],
                    borderColor: '#1f2937',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 }, color: '#cbd5e1' } }
                }
            }
        });

        // Grafico Bar
        const topIfr = [...ativos].sort((a,b) => a.ifr2 - b.ifr2).slice(0,8);
        new Chart(document.getElementById('chartBar'), {
            type: 'bar',
            data: {
                labels: topIfr.map(a => a.ticker),
                datasets: [{
                    label: 'IFR(2)',
                    data: topIfr.map(a => a.ifr2),
                    backgroundColor: '#d4af37',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
                    x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
});
