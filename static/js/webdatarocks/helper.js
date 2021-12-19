function processData(dataset) {
    var result = [];
    dataset.forEach(item => result.push(returnAccountName(item)));
    $('.loader').hide();
    return result;
}

function camelize(str) {
    return str.replace(/(?:^\w|[A-Z]|\b\w)/g, function (word, index) {
        return index === 0 ? word.toLowerCase() : word.toUpperCase();
    }).replace(/\s+/g, '');
}

function removeTabByIndex(tabIndexes, toolbar) {
    var tabs = toolbar.getTabs(); // get all tabs from the toolbar
    toolbar.getTabs = function () {
      $.each(tabIndexes, function (index, value) {
        delete tabs[value];
        return tabs;
      })
    }
}