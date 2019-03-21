//@ts-nocheck
/* Grey out the 'Search' button until required inputs are provided */
$('#query-form > input').keyup(function () {

    var empty = false;
    $('#query-form > input').each(function () {
        if ($(this).val() == '') {
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
    if (data.x == null) {
        return '<br>' + data.series.map(function (series) {
            return series.dashHTML + ' ' + series.labelHTML
        }).join('<br>');
    }
    var html = this.getLabels()[0] + ': ' + data.xHTML;
    return html;
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

    var d = new Date(min_data_x);
    var dow = d.getDay();

    var w = min_data_x;
    if (dow === 0) {
        highlight_period(w, w + oneDay - (w % oneDay) + timezone);
    }
    w = w + oneDay - (w % oneDay) + timezone;

    while (dow != 6) {
        w += oneDay;
        d = new Date(w);
        dow = d.getDay();
    }

    while (w < max_data_x) {
        var start_x_highlight = w;
        var end_x_highlight = w + 2 * oneDay;
        highlight_period(start_x_highlight, end_x_highlight);
        w += 7 * oneDay;
    }
}