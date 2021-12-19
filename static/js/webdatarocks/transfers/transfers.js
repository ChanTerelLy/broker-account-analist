let graphqlData = [];

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

function generatePivotTable() {
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
      },
      getTemplateByKey(key:"transfer"){
            name,
            url
      }
    }
    `,
        }),
        success: function (data) {
            graphqlData = data.data
            data = data.data.myTransfers
            $.getJSON(transfers_json_path, function (parametrs) {
                new WebDataRocks({
                    container: "#pivot-table-container",
                    beforetoolbarcreated: customizeToolbar,
                    width: "100%",
                    height: 700,
                    report: {
                        dataSource: {
                            type: "json",
                            data: processData(data),
                        },
                        slice: parametrs.slice,
                        formats: parametrs.formats
                    },
                    toolbar: true,
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
        tabs.unshift({
            id: "wdr-tab-upload",
            title: "Загрузить данные",
            handler: uploadData,
            icon: this.icons.connect
        });
        tabs.unshift({
            id: "wdr-tab-template",
            title: "Шаблон",
            handler: function (){
                location.href = graphqlData.getTemplateByKey[0].url
            },
            icon: this.icons.connect_json
        });
        return tabs;
    }
}

function uploadData() {
    $('#input-upload-button').click()
}

$('#input-upload-button').on('change', function () {

    const uploadQuery = {
        'query' : "mutation($file: Upload!) {\n  \tuploadTransfers(file: $file)  {\n  \t\tsuccess\n  \t}\n\t}",
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