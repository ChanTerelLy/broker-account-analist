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

async function updateGmailReports() {
        let q = `
        mutation {
            parseReportsFromGmail(limit:50) {
                success,
                redirectUri
              }
            }
        `
        $('#report-loader').show();
        let data = await graphqlQuery(q);
        let uri = data.data?.parseReportsFromGmail?.redirectUri
        let errors = data?.errors
        if (uri && !errors) {
            location.replace(uri)
            return;
        }
        if (data.data?.parseReportsFromGmail?.success && !errors) {
            alert('Отчеты загружены успешно')
            $('#report-loader').hide();
        } else {
            alert('Произошла ошибка')
            $('#report-loader').hide();
        }
    }
async function updateTinkoffReports() {
        let q = `
            query {
                tinkoffOperations
                }
        `
        $('#tinkoff-loader').show();
        let data = await graphqlQuery(q);
        let errors = data?.errors
        if (data.data?.tinkoffOperations && !errors) {
            alert('Отчеты загружены успешно')
            $('#tinkoff-loader').hide();
        } else {
            alert('Произошла ошибка')
            $('#tinkoff-loader').hide();
        }
    }
async function updateMmData() {
        let q = `
        mutation {
            LoadDataFromMoneyManager {
                success,
                redirectUri
              }
            }
        `
        $('#mm-loader').show();
        let data = await graphqlQuery(q);
        let uri = data.data?.LoadDataFromMoneyManager?.redirectUri
        let errors = data?.errors
        if (uri && !errors) {
            location.replace(uri)
            return;
        }
        if (data.data?.LoadDataFromMoneyManager?.success && !errors) {
            alert('Данные загружены успешно')
            $('#mm-loader').hide();
        } else {
            alert('Произошла ошибка')
            $('#report-loader').hide();
        }
    }

