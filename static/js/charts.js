/* ==========================================================================
   ACADIFY - DYNAMIC CHART RENDERING ENGINE (CHART.JS)
   Genuinely renders data passed from Django database views.
   ========================================================================== */

function initAttendanceTrendChart(canvasId, labels, dataPoints) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Check if there are no data points or all zeros
    const hasData = dataPoints && dataPoints.length > 0 && dataPoints.some(v => v > 0);

    if (!hasData) {
        // Show empty message on parent or clean zero line
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(67, 24, 255, 0.28)');
    gradient.addColorStop(1, 'rgba(67, 24, 255, 0.00)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attendance Rate (%)',
                data: dataPoints,
                borderColor: '#4318ff',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#4318ff',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#111c44',
                    titleFont: { family: 'Plus Jakarta Sans', size: 13, weight: '700' },
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `Attendance: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#a3aed0',
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' }
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: '#edf2f7',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#a3aed0',
                        font: { family: 'Plus Jakarta Sans', size: 11 },
                        stepSize: 20,
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function initDepartmentDonutChart(canvasId, labels, dataCounts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = [
        '#4318ff', '#05cd99', '#ffb547', '#ee5d50', '#868cff', '#01b574', '#707eae'
    ];

    const total = dataCounts.reduce((a, b) => a + b, 0);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataCounts.length > 0 && total > 0 ? dataCounts : [1],
                backgroundColor: dataCounts.length > 0 && total > 0 ? colors.slice(0, labels.length) : ['#e2e8f0'],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#2b3674',
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                        boxWidth: 12,
                        padding: 12,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    enabled: total > 0,
                    backgroundColor: '#111c44',
                    padding: 10,
                    cornerRadius: 8,
                }
            }
        }
    });
}
