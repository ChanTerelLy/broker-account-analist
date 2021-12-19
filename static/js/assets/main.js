async function graphqlQuery(query) {
    return $.ajax({
        method: "POST",
        url: '/graphql',
        contentType: "application/json",
        data: JSON.stringify({
            query: query,
        }),
        success: function (data) {
            return data;
        },
        error: function (request, status, error) {
            console.log(request.responseText)
            return null;
        }
    })
}

function showXirrValue(data) {
    if(data){
        $.each(data.data.myTransferXirr, function (index, value){
            let avg_xirr = value.avgPercent
            let total_xirr = value.totalPercent
            let account_name = value.accountName
            $('#avg-xirr').after(`<p>${account_name} - ${(avg_xirr * 100).toFixed(1)}%</p>`)
            $('#total-xirr').after(`<p>${account_name} - ${(total_xirr * 100).toFixed(1)}%</p>`)
        })
    }

}

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function strip(number) {
    return (parseFloat(number).toPrecision(12));
}

function camelize(str) {
    return str.replace(/(?:^\w|[A-Z]|\b\w)/g, function (word, index) {
        return index === 0 ? word.toLowerCase() : word.toUpperCase();
    }).replace(/\s+/g, '');
}

function swap(json){
  var ret = {};
  for(var key in json){
    ret[json[key]] = key;
  }
  return ret;
}

function calculateSum(reportValues, col) {
    return reportValues.reduce(function (sum, current) {
        return sum + current[col];
    }, 0);
}

//Update button

async function updateReports() {
            let q = `
        mutation {
            loadDataFromMoneyManager {
                success,
                redirectUri
              }
            parseReportsFromGmail(limit:5) {
                success,
                redirectUri
              }
            updateTinkoffOperations {
                success
              }
            }
        `
        $('#report-loader').show();
        let data = await graphqlQuery(q);
        let uri = data.data?.loadDataFromMoneyManager?.redirectUri
        let errors = data?.errors
        if (uri && !errors) {
            location.replace(uri)
            return;
        }
        let loadDataFromMoneyManager = data.data?.loadDataFromMoneyManager?.success
        let parseReportsFromGmail = data.data?.parseReportsFromGmail?.success
        let updateTinkoffOperations = data.data?.updateTinkoffOperations?.success
        if (!errors) {
            alert(`
            Обновлены:
            - MoneyManager - ${loadDataFromMoneyManager}
            - Отчеты Сбербанк - ${parseReportsFromGmail}
            - Отчеты Тинькофф - ${updateTinkoffOperations}
            `)
            location.reload();
        } else {
            alert('Произошла ошибка')
            $('#report-loader').hide();
        }
}

function disableLoader(data) {
    let errors = data?.errors
    if (errors) {
        alert('Произошла ошибка')
        console.error(errors)
    }
    $('.loader').hide();
    $('#total-info').show();
}