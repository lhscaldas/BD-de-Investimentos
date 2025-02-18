document.addEventListener("DOMContentLoaded", function () {
    /**
     * Função para inicializar um gráfico de linha do Chart.js.
     * @param {string} canvasId - ID do elemento <canvas> onde o gráfico será renderizado.
     * @param {string} labelCarteira - Nome da primeira linha do gráfico (Rentabilidade da Carteira ou Ativo).
     */
    function inicializarGraficoLinha(canvasId, labelCarteira) {
        var ctx = document.getElementById(canvasId);
        if (!ctx) return; // Evita erro caso o elemento não exista no template

        return new Chart(ctx.getContext("2d"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: labelCarteira,
                        data: dataPerc,
                        borderColor: "green",
                        backgroundColor: "rgba(0, 128, 0, 0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: "CDI Acumulado (%)",
                        data: dataCdi,
                        borderColor: "red",
                        borderDash: [5, 5],
                        backgroundColor: "rgba(255, 0, 0, 0.1)",
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Mês" } },
                    y: { title: { display: true, text: "Rentabilidade Acumulada (%)" }, beginAtZero: false }
                }
            }
        });
    }

    /**
     * Função para alternar entre CDI e IBOVESPA no gráfico de rentabilidade.
     * @param {Object} chart - Instância do Chart.js a ser atualizada.
     */
    function alternarIndice(chart) {
        var toggle = document.getElementById("toggleIndice");
        if (!toggle) return;

        toggle.addEventListener("change", function () {
            var datasetIndex = 1; // Segundo conjunto de dados (CDI ou IBOVESPA)

            if (this.checked) {
                console.log("Alternando para IBOVESPA");
                chart.data.datasets[datasetIndex].label = "IBOVESPA Acumulado (%)";
                chart.data.datasets[datasetIndex].data = [...dataIbov];
                chart.data.datasets[datasetIndex].borderColor = "blue";
                chart.data.datasets[datasetIndex].backgroundColor = "rgba(0, 0, 255, 0.1)";
            } else {
                console.log("Alternando para CDI");
                chart.data.datasets[datasetIndex].label = "CDI Acumulado (%)";
                chart.data.datasets[datasetIndex].data = [...dataCdi];
                chart.data.datasets[datasetIndex].borderColor = "red";
                chart.data.datasets[datasetIndex].backgroundColor = "rgba(255, 0, 0, 0.1)";
            }

            chart.update(); // Atualiza o gráfico
        });
    }

    /**
     * Função para inicializar um gráfico de evolução do patrimônio ou ativo.
     * @param {string} canvasId - ID do <canvas> onde o gráfico será renderizado.
     * @param {string} label - Nome da linha do gráfico.
     */
    function inicializarGraficoEvolucao(canvasId, label) {
        var ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx.getContext("2d"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: dataAbs,
                    borderColor: "blue",
                    backgroundColor: "rgba(0, 0, 255, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Mês" } },
                    y: { title: { display: true, text: "Valor (R$)" }, beginAtZero: false }
                }
            }
        });
    }

    /**
     * Função para ajustar a largura das barras de progresso para garantir que a soma seja 100%.
     */
    function ajustarBarrasProgresso() {
        var barraFixa = document.querySelector(".progress-bar.renda-fixa");
        var barraVariavel = document.querySelector(".progress-bar.renda-variavel");

        if (!barraFixa || !barraVariavel) return;

        var fixaPerc = parseFloat(barraFixa.getAttribute("data-width")) || 0;
        var variavelPerc = parseFloat(barraVariavel.getAttribute("data-width")) || 0;

        // Ajusta os valores para garantir que a soma seja exatamente 100%
        var soma = fixaPerc + variavelPerc;
        if (soma > 100) {
            fixaPerc = (fixaPerc / soma) * 100;
            variavelPerc = (variavelPerc / soma) * 100;
        } else if (soma < 100) {
            variavelPerc = 100 - fixaPerc;
        }

        barraFixa.style.width = fixaPerc + "%";
        barraVariavel.style.width = variavelPerc + "%";
    }

    /**
     * Função para inicializar o gráfico de composição da carteira.
     */
    function inicializarGraficoComposicao() {
        var ctx = document.getElementById("graficoComposicaoCarteira");
        if (!ctx) return;

        new Chart(ctx.getContext("2d"), {
            type: "pie",
            data: {
                labels: labelsSubclasse,
                datasets: [{
                    data: dataSubclasse,
                    backgroundColor: [
                        "rgba(255, 99, 132, 0.6)",
                        "rgba(54, 162, 235, 0.6)",
                        "rgba(255, 206, 86, 0.6)",
                        "rgba(75, 192, 192, 0.6)",
                        "rgba(153, 102, 255, 0.6)",
                        "rgba(255, 159, 64, 0.6)"
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                }
            }
        });
    }

    // Inicialização dos gráficos e funcionalidades para diferentes templates
    var chartRentabilidadeAtivo = inicializarGraficoLinha("graficoRentabilidadePerc", "Rentabilidade Percentual Acumulada do Ativo (%)");
    var chartRentabilidadeCarteira = inicializarGraficoLinha("graficoRentabilidadePercCarteira", "Rentabilidade Percentual Acumulada da Carteira (%)");

    if (chartRentabilidadeAtivo) alternarIndice(chartRentabilidadeAtivo);
    if (chartRentabilidadeCarteira) alternarIndice(chartRentabilidadeCarteira);

    inicializarGraficoEvolucao("graficoRentabilidadeAbs", "Evolução do Valor do Ativo (R$)");
    inicializarGraficoEvolucao("graficoRentabilidadeAbsCarteira", "Evolução do Patrimônio da Carteira (R$)");

    ajustarBarrasProgresso();
    inicializarGraficoComposicao();
});