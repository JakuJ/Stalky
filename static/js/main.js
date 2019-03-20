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

/* Plot data received from the server */
$("#query-form").submit(e => {

    e.preventDefault();
    var query = $("#query-input").val();
    var timespan = $("#query-timespan").val();
    var unit = $("#query-unit").val();

    d3.csv(`query/${query}/${timespan}/${unit}`, (error, data) => {
        if (error) {
            console.error(error);
        }
        nv.addGraph(() => {
            var chart = nv.models.multiChart()
                .x(d => d.x)
                .y(d => d.y)
                .margin({
                    left: 50,
                    right: 50
                })
                .color(d3.scale.category10().range());

            var activityData = [{
                    key: "General Activity",
                    values: []
                },
                {
                    key: "Messenger Status",
                    values: []
                },
                {
                    key: "Web Status",
                    values: []
                },
                {
                    key: "FB App Status",
                    values: []
                },
                {
                    key: "Other Status",
                    values: []
                },
                {
                    key: "AP Type",
                    values: []
                }
            ];

            data.forEach(d => {
                // Activity
                activityData[0]["values"].push({
                    x: new Date(Number(d["Time"]) * 1000),
                    y: d['Activity']
                });
                // VC Type
                let vc_index = ['74', '0', '8', '10'].indexOf(d['VC_ID']);
                for (let i = 1; i <= 4; i++) {
                    activityData[i]["values"].push({
                        x: new Date(Number(d["Time"]) * 1000),
                        y: (i == vc_index) ? 1 : 0
                    });
                }
                // AP Type
                activityData[5]["values"].push({
                    x: new Date(Number(d["Time"]) * 1000),
                    y: d['AP_ID'] || 0
                });
            });

            for (let i = 0; i <= 5; i++) {
                activityData[i]['type'] = 'line';
                activityData[i]['yAxis'] = 1;
            }

            activityData[5]['type'] = 'scatter';
            activityData[5]['yAxis'] = 2;
            activityData[5]['disabled'] = true;

            var statusTypes = ["inactive", "active"];
            var statusTypes2 = ["none", "a0", "a2", "p0", "p2"];

            chart.xAxis.tickFormat(d => d3.time.format('%X')(new Date(d)));
            chart.yAxis1.tickFormat(val => statusTypes[val]);
            chart.yAxis2.tickFormat(val => statusTypes2[val]);
            chart.yAxis1.domain([0, 1]);
            chart.yAxis2.domain([0, 4]);

            d3.select("#chart svg")
                .datum(activityData)
                .call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
        });
    });
});