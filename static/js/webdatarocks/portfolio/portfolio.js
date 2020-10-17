function processData(dataset) {
    var result = [];
    dataset.forEach(item => result.push(returnAccountName(item)));
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
    `,
    }),
    success: function (data) {
        data = data.data.myPortfolio
        $.getJSON(portfolio_json_path, function (parametrs) {
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
                slice : parametrs.slice,
                formats: parametrs.formats
            },
            global: {
                localization: ru_localization
            }
        });
        })
    }
})