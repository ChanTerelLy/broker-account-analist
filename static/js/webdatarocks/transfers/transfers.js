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
    if (node.accountIncome) {
        node.accountIncome = node.accountIncome.name
    } else {
        return node
    }
    if (node.accountCharge) {
        node.accountCharge = node.accountCharge.name
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
     myTransfers {
            accountIncome {
              name
            }
            accountCharge {
              name
            }
            dateOfApplication
            executionDate
            type
            sum
            currency
            description
            status
            typeSum
            helpTextMap
      }
    }
    `,
    }),
    success: function (data) {
        data = data.data.myTransfers
        $.getJSON(transfers_json_path, function (parametrs) {
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
                    slice: parametrs.slice,
                    formats: parametrs.formats
                },
                global: {
                    localization: ru_localization
                }
            });
        })
    }
})