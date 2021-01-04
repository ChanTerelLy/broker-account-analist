const COLORS = ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"];
function accountsChart(value) {
    let accountData = value;
    accountData = JSON.parse(accountData.data.accountChart);
    let colors = [];
    var labels = accountData.data.map(function (e) {
        return e.name;
    });
    var data = accountData.data.map(function (e) {
        return e.total;
    });
    $.each(labels, function (index, value) {
        colors.push(COLORS[index])
    })
    new Chart(document.getElementById("accounts"), {
        plugins: [ChartDataLabels],
        type: 'horizontalBar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Итог",
                    backgroundColor: colors,
                    data: data
                }
            ]
        },
        options: {
            plugins: {
                datalabels: {
                    font: {
                        size: 20,
                        weight: 600
                    },
                    formatter: function (value) {
                        return numberWithCommas(value)
                    }
                }
            },
            legend: {display: false},
            title: {
                display: true,
                text: 'Итоговые значения аккаунтов'
            },
            scales: {
                xAxes: [{
                    ticks: {
                        min: 0,
                        stepSize: 5000,
                        mirror: true
                    },
                    display: false
                }]
            },
        }
    });
}

function transterChart() {
    new Chart(document.getElementById("transfers"), {
    type: 'pie',
    data: {
      labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
      datasets: [{
        label: "Population (millions)",
        backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
        data: [2478,5267,734,784,433]
      }]
    },
    options: {
      title: {
        display: true,
        text: 'Predicted world population (millions) in 2050'
      }
    }
});
}