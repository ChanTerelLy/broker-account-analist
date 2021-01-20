const COLORS = ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850"];

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
                text: 'Итоговые значения аккаунтов: ' + numberWithCommas(data.reduce((a, b) => a + b, 0)),
                fontSize: 16
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
                backgroundColor: ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850"],
                data: [2478, 5267, 734, 784, 433]
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

function getReportDataByIndex(index=0){
    return queryData.data.reportAssetEstimateDataset[index].data
}


function showReportChart(index=0) {
    google.charts.load('current', {'packages': ['corechart']});
    var reportInstanceData = getReportDataByIndex(index)
    google.charts.setOnLoadCallback(drawChart);

    function drawChart() {
        let darrays = [];
        $.each(reportInstanceData, function (index, value) {
            darrays.push([new Date(value.date), value.sum, value.incomeSum])
        })
        var data = google.visualization.arrayToDataTable(
            [
                ['Дата', 'Ликвидационная сумма', 'Входящий поток'],
                ...darrays
            ]
        );
        var options = {
            curveType: 'function',
            legend: {position: 'bottom'}
        };

        var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

        chart.draw(data, options);
    }
}

function updateChart() {
    showReportChart($("#report-menu option:selected").val())
}

function setReportSelectors() {
    if(queryData.data.userAccounts){
        $("#report-menu").attr({'visibility': 'visible'})
    }
    $.each(queryData.data.userAccounts, function(index, value){
        $("#report-menu").append(new Option(value.name, index));
    })
}

function showPortfolioReportTable(queryData){
        google.charts.load('current', {'packages': ['table']});
        google.charts.setOnLoadCallback(drawTable);
        let reportValues = [];
        $.each(queryData.data.portfolioByDate.data, function(key, value){
            reportValues.push(Object.values(value))
        })
        let map = Object.keys(JSON.parse(queryData.data.portfolioByDate.map));
        function drawTable() {
            var data = google.visualization.arrayToDataTable(
                [map,
                ...reportValues]
            );

            var table = new google.visualization.Table(document.getElementById('table_div'));

            table.draw(data, {showRowNumber: true, width: '100%', height: '100%'});
        }
}