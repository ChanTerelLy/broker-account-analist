function processData(dataset) {
    var result = [];
    dataset.forEach(item => result.push(returnAccountName(item.node)));
    return result;
}

function camelize(str) {
  return str.replace(/(?:^\w|[A-Z]|\b\w)/g, function(word, index) {
    return index === 0 ? word.toLowerCase() : word.toUpperCase();
  }).replace(/\s+/g, '');
}

function returnAccountName(node){
    let map = JSON.parse(node.helpTextMap)
    let newMap = {};
    let newNode = {}
    if (node.account) {
        node.account = node.account.name
    } else {
        return node
    }
    $.each(map, function (key, value){
        newMap = {...newMap, ...value}
    })
    $.each(node, function(key, value) {
        key = newMap[key] || key;
        newNode[key] = value;
    });
    delete newNode['helpTextMap']
    return newNode
}

$.ajax({
    method: "POST",
    url: '/graphql',
    contentType: "application/json",
    data: JSON.stringify({
    query: `
    query {
        myPortfolio{
            edges {
              node {
                buycloseprice,
                buysum,
                cashflow,
                earnings,
                fromDate,
                secid,
                sellcloseprice,
                sellsum,
                tillDate,
                volume,
                yieldPercent,
                helpTextMap,
                account {
                  name
                }
              }
            }
          }
        }
    `,
    }),
    success: function (data) {
        data = data.data.myPortfolio.edges
        // let params = $.getJSON("assests/portfolio.json")
        new WebDataRocks({
            container: "#pivot-table-container",
            width: "100%",
            height: 700,
            toolbar: true,
            report: {
                dataSource: {
                    type: "json",
                    data: processData(data),
                },
                    "slice": {
        "rows": [
            {
                "uniqueName": "Дата продажи.Month"
            },
            {
                "uniqueName": "Аккаунт"
            },
            {
                "uniqueName": "Инструмент"
            }
        ],
        "columns": [
            {
                "uniqueName": "Measures"
            }
        ],
        "measures": [
            {
                "uniqueName": "Доход",
                "aggregation": "sum",
                "format": "47kdtbsh"
            },
            {
                "uniqueName": "Количество бумаг",
                "aggregation": "sum",
                "format": "47kdthat"
            },
            {
                "uniqueName": "Внутр. ставка доходности",
                "aggregation": "average",
                "format": "47kdw2yc"
            },
            {
                "uniqueName": "Купоны/ дивиденды",
                "aggregation": "sum",
                "format": "47kdv4x0"
            },
            {
                "uniqueName": "Цена закрытия в дату покупки, в рублях",
                "aggregation": "avg",
                "format": "47kdsyoo"
            },
            {
                "uniqueName": "Цена закрытия в дату продажи, в рублях",
                "aggregation": "average",
                "format": "47kdvrg0"
            },
            {
                "uniqueName": "Сумма покупки",
                "aggregation": "sum",
                "format": "47kdvbjh"
            },
            {
                "uniqueName": "Сумма продажи",
                "aggregation": "sum",
                "format": "47kdvh8q"
            },
        ]
    },
    "formats": [
        {
            "name": "47kdsyoo",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdtbsh",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdthat",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdv4x0",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdvbjh",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdvh8q",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdvrg0",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 0,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        },
        {
            "name": "47kdw2yc",
            "thousandsSeparator": " ",
            "decimalSeparator": ".",
            "decimalPlaces": 1,
            "currencySymbol": "",
            "currencySymbolAlign": "left",
            "nullValue": "",
            "textAlign": "right",
            "isPercent": false
        }
    ],
            },
            global: {
                localization: ru_localization
            }
        });
    }
})