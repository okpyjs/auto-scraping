
function run(flag) {
    var url = ""
    var timeInterval = 0
    if(flag == "auto") {
        var timeInterval = $("#auto_interval").val()
    }
    if(flag == "manual") {
        var url = $("#manual_url").val()
    }

    console.log(flag, url, timeInterval)

    $.post(
        "/run",
        {
            "flag": flag,
            "interval": timeInterval,
            "url": url
        },
        (res) => {
            console.log(res.status)
        }
    )
}

function stop(flag) {
    console.log(flag)
    $.post(
        "/stop",
        {
            "flag": flag,
            "data": "stop"
        },
        (res) => {
            console.log(res.status)
        }
    )
}


$(document).ready(() => {
    $("#auto_run").click((e) => {
        e.preventDefault()
        run("auto")
    })

    $("#manual_run").click((e) => {
        e.preventDefault()
        run("manual")
    })

    $("#auto_stop").click((e) => {
        e.preventDefault()
        stop("auto")
    })

    $("#manual_stop").click((e) => {
        e.preventDefault()
        stop("manual")
    })
})