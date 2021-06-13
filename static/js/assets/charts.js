const COLORS = ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850"];

function accountsChart(value) {
    let accountData = value;
    accountData = JSON.parse(accountData.data.accountChart);
    let colors = [];
    var total = accountData.data.map(function (e) {
        return {name: e.name, total: e.total};
    }).sort((a,b) => a.total-b.total)
    var labels = total.map(function (e) {
        return e.name;
    });
    var data = total.map(function (e) {
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
    $("#report-menu").append(new Option('Total', queryData.data.userAccounts.length));
}

function showPortfolioReportTable(queryData, reportType='sberbank'){
        google.charts.load('current', {'packages': ['table', 'corechart']});
        google.charts.setOnLoadCallback(drawTable);
        google.charts.setOnLoadCallback(drawPieChart);
        google.charts.setOnLoadCallback(piePositionChart);
        let reportValues = [];
        $.each(queryData.data, function(key, value){
            reportValues.push(Object.values(value))
        })
        let totalStyle = 'font-size:1.5rem';
        let mapJson = JSON.parse(queryData.map);
        let reverseMapJson = swap(mapJson)
        let map = listOfQueryFields.map(function(value, index){
            return reverseMapJson[value]
        })

    function styling(data) {
        let formatter = new google.visualization.ArrowFormat()
        if(reportType==='tinkoff') {
            var totalSum = calculateSum(reportValues, 2)
            var totalEarn = calculateSum(reportValues, 4)
            let index = data.addRow(['Итог', null, totalSum, null, totalEarn, null, null, null, null])
            data.setProperty(index, 2, 'style', totalStyle);
            data.setProperty(index, 4, 'style', totalStyle);
            formatter.format(data, 4);
        } else {

        }
    }

    function drawTable() {
        var data = google.visualization.arrayToDataTable(
            [map.filter(Boolean),
            ...reportValues]
        );
        styling(data);
        var table = new google.visualization.Table(document.getElementById('table_div'));
        table.draw(data, {allowHtml: true, showRowNumber: true, width: '100%', height: '100%'});
        }
        function drawPieChart() {
            let pieData = [];
            $.each(queryData.data, function(key, value){
                pieData.push([value.name,value.startMarketTotalSumWithoutNkd])
            })
            var data = google.visualization.arrayToDataTable([
                ['Наименование', 'Сумма'],
                ...pieData
            ]);
            var options = {
                title: 'Сборная диаграмма'
            };

            var chart = new google.visualization.PieChart(document.getElementById('piechart'));

            chart.draw(data, options);
        }
        function piePositionChart() {
            let pieData = [];
            let groupedPieData = {};
            $.each(queryData.data, function(key, value){
                if(groupedPieData[value.instrumentType]){
                    groupedPieData[value.instrumentType] += value.startMarketTotalSumWithoutNkd;
                } else {
                    groupedPieData[value.instrumentType] = value.startMarketTotalSumWithoutNkd
                }
            })
            pieData = Object.keys(groupedPieData).map((key) => [key, groupedPieData[key]]);
            var data = google.visualization.arrayToDataTable([
                ['Тип', 'Сумма'],
                ...pieData
            ]);
            var options = {
                title: 'Анализ по типу'
            };

            var chart = new google.visualization.PieChart(document.getElementById('pie-position-chart'));

            chart.draw(data, options);
        }
}

function showAvgIncome(queryData){
    google.charts.load('current', {'packages': ['table']});
    google.charts.setOnLoadCallback(drawTable);
    let reportValues = [];
    $.each(queryData.data.myTransferXirr, function(key, value){
        for (const key in value){
            if(key == 'avgPercent' || key == 'totalPercent'){
                let v = value[key]
                let n = Math.round(strip((v * 100)))
                value[key] = {v:n, f: n + '%'}
            }
        }
        let ar = Object.values(value);
        reportValues.push(ar)
    })
    var totalSum = calculateSum(reportValues, 3)
    reportValues.push(['Итог', '-', '-', totalSum])
    function drawTable() {
            var data = google.visualization.arrayToDataTable(
                [['Счет', 'Средний за год', 'Средний за все время', 'Доход'],
                ...reportValues]
            );

            var table = new google.visualization.Table(document.getElementById('table_div'));
            let formatter = new google.visualization.ArrowFormat()
            formatter.format(data, 2);
            formatter.format(data, 1);
            table.draw(data, {allowHtml: true,showRowNumber: true, width: '100%', height: '100%'});
        }
}

function showDividentChart(queryData) {
        google.charts.load('current', {'packages': ['corechart']});
        google.charts.setOnLoadCallback(drawChart);

        function drawChart() {
            let darrays = [];
            $.each(queryData.data.couponChart, function (index, value) {
                darrays.push([new Date(value.date), value.sum])
            })
            var data = google.visualization.arrayToDataTable(
                [
                    ['Дата', 'Сумма'],
                    ...darrays
                ]
            );
            var options = {
                legend: {position: 'bottom'}
            };
            var chart = new google.visualization.ColumnChart(document.getElementById('column_chart'));
            chart.draw(data, options);
        }
}