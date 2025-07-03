odoo.define('hotel_dashboard.dashboard', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');

    const Dashboard = AbstractAction.extend({
        start: function () {
            this._super();
            this._renderCharts();
        },
        _renderCharts: function () {
            const charts = [
                { id: 'arrival_chart_', data: [5, 15], labels: ['Pending', 'Arrived'] },
                { id: 'departure_chart_', data: [10, 5], labels: ['Pending', 'Checked Out'] },
                { id: 'guests_chart_', data: [9, 3], labels: ['Adults', 'Children'] },
                { id: 'room_status_chart_', data: [267, 2, 0, 0, 2], labels: ['Vacant', 'Sold', 'Day Use', 'Complimentary', 'Blocked'] },
                { id: 'housekeeping_status_', data: [234, 20, 40], labels: ['Clean', 'In Progress', 'Dirty'] }
            ];

            charts.forEach((chart) => {
                const ctx = document.getElementById(chart.id);
                if (ctx) {
                    new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: chart.labels,
                            datasets: [{
                                data: chart.data,
                                backgroundColor: ['#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF'],
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                        },
                    });
                }
            });
        },
    });

    return Dashboard;
});
