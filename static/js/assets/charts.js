const COLORS = ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"];
async function accountsChart() {
    let accountData = await getAccountData();
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
        type: 'horizontalBar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Суммы по аккаунтам",
                    backgroundColor: colors,
                    data: data
                }
            ]
        },
        options: {
            legend: {display: false},
            title: {
                display: true,
                text: 'Итоговые значения аккаунтов'
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

function getAccountData() {
    return $.ajax({
        method: "POST",
        url: '/graphql',
        contentType: "application/json",
        data: JSON.stringify({
            query: `
    query {
     accountChart
    }
    `,
        }),
        success: function (data) {
            return data
        }
    })
}