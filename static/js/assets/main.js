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
    let value = data;
    if(value){
        let avg_xirr = value.data.myTransferXirr.avgPercent
        let total_xirr = value.data.myTransferXirr.totalPercent
        $('#avg-xirr').text((avg_xirr * 100).toFixed(1) + '%')
        $('#total-xirr').text((total_xirr * 100).toFixed(1) + '%')
    }

}

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function strip(number) {
    return (parseFloat(number).toPrecision(12));
}