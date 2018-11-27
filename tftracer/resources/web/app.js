Vue.component('run-card', {
    props: ['run'],
    template: "#run-card-template",
    methods: {
        trace: function () {
            var card = this;
            card["tracing"] = true;
            fetch(card.run.trace_url)
                .then(function (response) {
                    app.connection_error = false;
                    app.update_data();
                })
                .catch(function () {
                    app.connection_error = true;
                    card["tracing"] = false;
                });
        },
        trace_id: function (trace_id) {

        },
        hide_trace_spinner: function (name) {
            console.log(name)
            var x = document.getElementsByClassName(name);
            for (var i = 0; i < x.length; i++) {
                x[i].classList.add("uk-hidden");
            }
        }
    },
})

var app = new Vue({
    el: '#app',
    data: {
        running: true,
        updating: false,
        global_tracing: false,
        runs: [],
        connection_error: false
    },
    methods: {
        update_data: function () {
            this.updating = true;
            fetch("/update")
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    app.connection_error = false;
                    app.running = data.running;
                    app.global_tracing = data.global_tracing;
                    app.runs = data.runs;
                    setTimeout(function () {
                        app.updating = false;
                    }, 1000);
                })
                .catch(function () {
                    app.connection_error = true;
                    app.updating = false;
                })
        },
        cancelAutoUpdate: function () {
            clearInterval(this.timer)
        },
        enable_global_tracing: function () {
            UIkit.modal.confirm('Global tracing imposes a significant runtime overhead. Continue?',
                {labels: {ok: "Enable Global Tracing", cancel: "Cancel"}}).then(
                function () {
                    app.global_tracing = true;
                    fetch("/enable_global_tracing")
                        .then(function (response) {
                            app.connection_error = false;
                            app.update_data();
                        })
                        .catch(function () {
                            app.connection_error = true;
                            app.global_tracing = false;
                        });
                });
        },
        disable_global_tracing: function () {
            app.global_tracing = false;
            fetch("/disable_global_tracing")
                .then(function (response) {
                    app.connection_error = false;
                    app.update_data();
                })
                .catch(function () {
                    app.connection_error = true;
                    app.global_tracing = true;
                });
        },
        kill_tracing_server: function () {
            UIkit.modal.confirm('Are you sure?', {labels: {ok: "Kill Tracing Server", cancel: "Cancel"}})
                .then(function () {
                    fetch("/kill_tracing_server")
                        .then(function (response) {
                            app.connection_error = false;
                        })
                        .catch(function () {
                            app.connection_error = true
                        });
                }, function () {
                });
        },
    },
    created: function () {
        this.update_data();
        this.timer = setInterval(this.update_data, 5000)
    },
    beforeDestroy() {
        clearInterval(this.timer);
    },
});