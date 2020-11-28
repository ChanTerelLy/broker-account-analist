function processData(dataset) {
    var result = [];
    dataset.forEach(item => result.push(returnAccountName(item)));
    $('.loader').hide();
    return result;
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

function generatePivotTable() {
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
                    beforetoolbarcreated: customizeToolbar,
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
                    },
                    dataloaded: function () {
                        $('.loader').hide();
                    }
                });
            })
        }
    })
}

function customizeToolbar(toolbar) {
    var tabs = toolbar.getTabs();
    $.each([0,1,2], function (index, value) {
        delete tabs[value];
        return tabs;
    })
    toolbar.getTabs = function() {
        // There will be two new tabs at the beginning of the Toolbar
        tabs.unshift({
            id: "wdr-tab-upload",
            title: "Загрузить данные",
            handler: uploadData,
            icon: this.icons.connect
        });
        return tabs;
    }
}

function uploadData() {
    $('#input-upload-button').click()
}

$('#input-upload-button').on('change', function () {

    const uploadQuery = {
        'query' : "mutation($file: Upload!) {\n  \tuploadPortfolio(file: $file)  {\n  \t\tsuccess\n  \t}\n\t}",
        "variables":{"file":null},
        "operationName":null
    }

    var fd = new FormData();
    var files = $('#input-upload-button')[0].files;
    // Check file selected or not
    if (files.length > 0) {
        fd.append('0', files[0]);
        fd.append('map', JSON.stringify({"0":["variables.file"]}));
        fd.append('operations', JSON.stringify(uploadQuery));
        $('.loader').show();

        $.ajax({
            url: '/graphql',
            type: 'post',
            data: fd,
            contentType: false,
            processData: false,
            success: function (response) {
                if (response?.data?.uploadTransfers?.success) {
                    alert('Данные загружены успешно')
                    $('.loader').hide();
                    location.reload();
                } else {
                    alert('Что то пошло не так')
                    $('.loader').hide();
                }
            },
            onerror: function () {
                alert('Что то пошло не так')
                $('.loader').hide();
            }
        });
        $('#input-upload-button').val('');
    }
});