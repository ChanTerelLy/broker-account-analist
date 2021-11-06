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

function getReportDataByIndex(accountName = 'Total') {
    return queryData.data.reportAssetEstimateDataset.filter(obj => {
        return obj.accountName === accountName
    })[0].data
}

function showReportChart(accountName="Total") {
    google.charts.load('current', {'packages': ['corechart']});
    var reportInstanceData = getReportDataByIndex(accountName)
    google.charts.setOnLoadCallback(drawChart);

    function drawChart() {
        let darrays = [];
        $.each(reportInstanceData, function (index, value) {
            darrays.push([new Date(value.date), value.sum, value.incomeSum])
        })
        var data = google.visualization.arrayToDataTable(
            [
                ['Дата', 'Стоимость', 'Вложено'],
                ...darrays
            ]
        );
        var options = {
            curveType: 'function',
            legend: {position: 'bottom'},
            backgroundColor: { fill:'transparent' }
        };

        var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

        chart.draw(data, options);
    }
}

function updateChart() {
    showReportChart($("#report-menu option:selected").text())
}

function setReportSelectors() {
    if(queryData.data.userAccounts){
        $("#report-menu").attr({'visibility': 'visible'})
    }
    $("#report-menu").append(new Option('Total', queryData.data.userAccounts.length));
    $.each(queryData.data.userAccounts, function(index, value){
        $("#report-menu").append(new Option(value.name, index));
    })

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
        } else if(reportType==='sberbank') {
            formatter.format(data, 10);
        }
        else {}
    }
    function drawTable() {
        var data = google.visualization.arrayToDataTable(
            [map.filter(Boolean),
            ...reportValues]
        );
        styling(data);
        var table = new google.visualization.Table(document.getElementById('table_div'));
        let options = {allowHtml: true, showRowNumber: true, width: '100%'}
        if(reportType==='sberbank') {
            options.sortColumn = 10
        }
        table.draw(data, options);
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
            title: 'Сборная диаграмма',
            backgroundColor: { fill:'transparent' }
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
                title: 'Анализ по типу',
                backgroundColor: { fill:'transparent' }
            };

        var chart = new google.visualization.PieChart(document.getElementById('pie-position-chart'));

        chart.draw(data, options);
    }
}

function showIISIncome(queryData) {
    google.charts.load('current', {'packages': ['table', 'corechart']});
    google.charts.setOnLoadCallback(drawTable);
    let darrays = [];
    $.each(queryData, function (index, value) {
                darrays.push([value.year + ' year', value.sum])
            })

    function drawTable() {
        var data = google.visualization.arrayToDataTable(
            [['Год', 'Сумма'],
            ...darrays]
        );
        var table = new google.visualization.Table(document.getElementById('iis_div'));
        let options = {
            allowHtml: true,
            showRowNumber: true,
            width: '50%',
            height: '50%',
        }
        table.draw(data, options);
        }
}

function showAvgIncome(queryData){
    google.charts.load('current', {'packages': ['table']});
    google.charts.setOnLoadCallback(drawTable);
    let reportValues = [];
    let myTransferXirr = queryData.data.myTransferXirr
    let assetsRemains = JSON.parse(queryData.data.assetsRemains)
    $.each(myTransferXirr, function(key, value){
        for (const key in value){
            if(key == 'avgPercent' || key == 'totalPercent'){
                let v = value[key]
                let n = Math.round(strip((v * 100)))
                value[key] = {v:n, f: n + '%'}
            }
        }
        value.remain = 0
        if(assetsRemains[value.accountName]){
            value.remain = assetsRemains[value.accountName]
        }
        console.log(2)
        let ar = Object.values(value);
        reportValues.push(ar)
    })
    var totalSum = calculateSum(reportValues, 3)
    var remainSum = calculateSum(reportValues, 4)
    reportValues.push(['Итог', '-', '-', totalSum, remainSum])
    function drawTable() {
            var data = google.visualization.arrayToDataTable(
                [['Счет', 'Средний за год', 'Средний за все время', 'Доход', 'Остатки'],
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
        google.charts.load('current', {'packages': ['corechart', 'bar']});
        google.charts.setOnLoadCallback(drawChart);
        google.charts.setOnLoadCallback(drawAvgYearChart);
        google.charts.setOnLoadCallback(drawAvgMonthChart);

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
                legend: { position: "none" },
                backgroundColor: { fill:'transparent' }
            };
            var chart = new google.visualization.ColumnChart(document.getElementById('column_chart'));
            chart.draw(data, options);
        }
        function drawAvgYearChart(){
            drawAvgChart("Общая сумма за год", 'sum', 'year_total_chart', [100000,200000,300000])
        }
        function drawAvgMonthChart(){
            drawAvgChart("Средняя сумма в месяц", 'avgMonth', 'month_avg_chart', [5000,10000,20000, 30000])
        }
        function drawAvgChart(title, valueParam, elementId, ticks) {
            let darrays = [];
            $.each(queryData.data.couponAggregated, function (index, value) {
                darrays.push([value.year + '', value[valueParam]])
            })
            var data = google.visualization.arrayToDataTable(
                [
                    ['Год', 'Сумма'],
                    ...darrays
                ]
            );
            var options = {
                chart: {
                    title: title,
                    hAxis: {
                        ticks: ticks
                    }
                },
                bars: 'horizontal',
                backgroundColor: {fill: 'transparent'},
                legend: {position: "none"},
            };
            var chart = new google.charts.Bar(document.getElementById(elementId));
            chart.draw(data, google.charts.Bar.convertOptions(options))
        }
}