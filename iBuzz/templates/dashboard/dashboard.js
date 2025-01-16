/* globals Chart:false */

let fetched_data = {}

async function get_data(field) {
    fetch("/data/" + field).then((r) => {
        if (!r.ok) {
            throw new Error("Bad Request")
        }
        return r.json()
    }).then((json) => {
        console.log(json)
        let times = json['Time']
        let data = json[field]
        let reformatted = []
        for (let i = 0; i < times.length; i++) {
            reformatted.push({t:times[i], y:data[i]})
        }
        console.log(reformatted)
        fetched_data[field] = reformatted
    })
}

function make_chart(field) {
    get_data(field).then(() => {
        const ctx = document.getElementById('myChart')
        let myChart = new Chart(ctx, {
            type: 'line',
            options: {
                scales: {
                    x: {
                        type: 'time',
                    }
                }
            },
            data: {
                datasets: [{
                    label: field,
                    data: fetched_data[field],
                }]
            }
        })
    })
}

make_chart('Outside_temp')

function main() {
// Graphs
    const ctx = document.getElementById('myChart')
// eslint-disable-next-line no-unused-vars
    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [
                'Sunday',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday'
            ],
            datasets: [{
                data: [
                    15339,
                    21345,
                    18483,
                    24003,
                    23489,
                    24092,
                    12034
                ],
                lineTension: 0,
                backgroundColor: 'transparent',
                borderColor: '#007bff',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    boxPadding: 3
                }
            }
        }
    })
}

