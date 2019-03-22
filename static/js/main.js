//@ts-nocheck
/* Grey out the 'Search' button until required inputs are provided */
$('#query-form > input').keyup(function () {

    var empty = false;
    $('#query-form > input').each(() => {
        if ($(this).val() === '') {
            empty = true;
        }
    });

    if (empty) {
        $('#Search').attr('disabled', 'disabled');
    } else {
        $('#Search').removeAttr('disabled');
    }
});

/* Only display time on the legend when mouse over */
function legendFormatter(data) {
    if (!data.x) {
        return '<br>' + data.series.map(series =>
            series.dashHTML + ' ' + series.labelHTML
        ).join('<br>');
    }
    return this.getLabels()[0] + ': ' + data.xHTML;
}

/* Add grey background to Saturdays and Sundays */
function highlightWeekends(canvas, area, g) {

    canvas.fillStyle = "rgba(0, 0, 0, 0.2)";
    const oneDay = 24 * 60 * 60 * 1000;

    var min_data_x = g.getValue(0, 0);
    var max_data_x = g.getValue(g.numRows() - 1, 0);

    function highlight_period(x_start, x_end) {
        if (x_start < min_data_x) {
            x_start = min_data_x;
        }
        if (x_end > max_data_x) {
            x_end = max_data_x;
        }

        var canvas_left_x = g.toDomXCoord(x_start);
        var canvas_right_x = g.toDomXCoord(x_end);
        var canvas_width = canvas_right_x - canvas_left_x;

        canvas.fillRect(canvas_left_x, area.y, canvas_width, area.h);
    }

    var timezone = new Date().getTimezoneOffset() * 60 * 1000;
    var day_of_week = new Date(min_data_x).getDay();
    var w = min_data_x;

    // Edge case - starting on Sunday
    var next_midnight = w + oneDay - (w % oneDay) + timezone;
    if (day_of_week === 0) {
        highlight_period(w, next_midnight);
    }

    // Find first Saturday
    w = next_midnight;
    while (day_of_week != 6) {
        w += oneDay;
        day_of_week = new Date(w).getDay();
    }

    while (w < max_data_x) {
        var start_x_highlight = w;
        var end_x_highlight = w + 2 * oneDay;
        highlight_period(start_x_highlight, end_x_highlight);
        w += 7 * oneDay;
    }
}
/* Main front-end logic */
$("#query-form").submit(e => {
    e.preventDefault();

    var query = $("#query-input").val();
    var timespan = $("#query-timespan").val();
    var unit = $("#query-unit").val();

    new Dygraph(document.getElementById("graphDiv"),
        `query/${query}/${timespan}/${unit}`, {
            title: 'Facebook Activity',
            xlabel: 'Time',
            ylabel: 'Activity Type',
            legend: 'always',
            colors: ['blue', 'orange', 'green', 'red', 'black'],
            legendFormatter: legendFormatter,
            underlayCallback: highlightWeekends,
            plugins: [
                new Dygraph.Plugins.Crosshair({
                    direction: "vertical"
                })
            ],
            axes: {
                y: {
                    valueRange: [0, 1.05],
                    ticker: () => [{
                        v: 0.1,
                        label: "Activity"
                    }, {
                        v: 0.3,
                        label: "Messenger"
                    }, {
                        v: 0.5,
                        label: "App"
                    }, {
                        v: 0.7,
                        label: "Web"
                    }, {
                        v: 0.9,
                        label: "Other"
                    }]

                }
            }
        }
    );
});