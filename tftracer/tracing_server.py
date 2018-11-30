#! /usr/bin/env python -u
# coding=utf-8
import gzip
import pickle

from io import BytesIO

__author__ = 'Sayed Hadi Hashemi'

import datetime
import json
import os
from collections import OrderedDict
from copy import deepcopy
from gevent.pywsgi import WSGIServer
import flask
import threading
from .timeline import Timeline
import tensorflow as tf
from .version import __version__

class VisualizationServerBase:
    def __init__(self, server_port=9999, server_ip="0.0.0.0", **kwargs):
        self._server_port = server_port
        self._server_ip = server_ip
        self._wsgi_server = None
        self._flask_app = None
        self._server_thread = None

    def _start_server(self):
        self._flask_app = self._get_flask_app()
        self._wsgi_server = WSGIServer((self._server_ip, self._server_port), self._flask_app)
        self._wsgi_server.serve_forever()

    def start_web_server(self):
        """
        Start a web server in a separate thead.

        Note:
            The tracing server keeps track of session runs even without a running web server.
        """
        if not self._server_thread:
            self._server_thread = threading.Thread(target=self._start_server)
            self._server_thread.start()
            tf.logging.warn("Tracing Server: http://{}:{}/".format(self._server_ip,
                                                                   self._server_port))

    def stop_web_server(self):
        """
        Stop the web server.

        Note:
            The tracing server keeps track of session runs even after the web server is stopped.
        """
        if self._wsgi_server.started:
            self._wsgi_server.stop()
            if threading.current_thread() != self._server_thread:
                self._server_thread.join()
            self._server_thread = None

    def join(self):
        """
        Wait until the web server is stopped.
        """
        if self._wsgi_server.started:
            self._server_thread.join()

    def _get_flask_app(self):
        raise NotImplemented


class VisualizationServer(VisualizationServerBase):
    _static_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/web/')

    def __init__(self, name, source, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._source = source
        self._keep_traces = kwargs.get("keep_traces", 5)

    def _handle_update(self):
        runs = self._source.get_runs()
        response = {
            "running": self._source.running,
            "global_tracing": self._source.global_tracing,
            "runs": deepcopy(runs),
        }
        for run in response["runs"]:
            run_id = run["run_id"]
            run["trace_url"] = "/trace/{}".format(run_id)

            run["stats"]["runtime_avg"] = str(run["stats"]["runtimes"])
            del run["stats"]["runtimes"]

            run["stats"]["first_run"] = str(run["stats"]["first_run"])
            run["stats"]["last_run"] = str(run["stats"]["last_run"])

            run["traces"] = run["traces"][-self._keep_traces:]

            for trace in run["traces"]:
                trace_id = trace["trace_id"]
                trace["title"] = str(trace["date"])
                del trace["date"]
                trace["url"] = "/{}/{}".format(run_id, trace_id)
                trace["download_url"] = "/download/{}/{}".format(run_id, trace_id)

        return json.dumps(response)

    def _handle_main(self):
        with open(os.path.join(self._static_folder, "main.html")) as fp:
            return fp.read()

    def _handle_timelime(self, run_id, trace_id=0):
        run_metadata = self._source.get_trace(run_id, trace_id)
        if run_metadata is None:
            return flask.redirect("/")
        else:
            result = Timeline(run_metadata=run_metadata).visualize()
            return result

    def _handle_download(self, run_id, trace_id=0):
        run_metadata = self._source.get_trace(run_id, trace_id)
        if run_metadata is None:
            return flask.redirect("/")
        else:
            fp = BytesIO()
            pickle.dump(run_metadata, fp)
            fp.seek(0, 0)
            return flask.send_file(fp,
                                   as_attachment=True,
                                   attachment_filename="run_metadata-{}-{}.pickle".format(run_id, trace_id))

    def _handle_save_session(self):
        data = pickle.dumps(self._source)
        gdata = gzip.compress(data)
        fp = BytesIO(gdata)
        fp.seek(0, 0)
        return flask.send_file(fp,
                               as_attachment=True,
                               attachment_filename="tracing-session.pickle.gz")

    def _handle_enable_tracing(self, run_id):
        self._source.enable_tracing(run_id)
        return flask.redirect("/")

    def _handle_enable_global_tracing(self):
        self._source.enable_global_tracing()
        return flask.redirect("/")

    def _handle_disable_global_tracing(self):
        self._source.disable_global_tracing()
        return flask.redirect("/")

    def _handle_kill_server(self):
        self.stop_web_server()
        return flask.redirect("/")

    def _get_flask_app(self):
        app = flask.Flask(self._name, static_folder=self._static_folder, static_url_path="/static")
        app.route("/")(self._handle_main)
        app.route("/<int:run_id>/<int:trace_id>")(self._handle_timelime)
        app.route("/download/<int:run_id>/<int:trace_id>")(self._handle_download)
        app.route("/trace/<int:run_id>")(self._handle_enable_tracing)
        app.route("/update")(self._handle_update)
        app.route("/enable_global_tracing")(self._handle_enable_global_tracing)
        app.route("/disable_global_tracing")(self._handle_disable_global_tracing)
        app.route("/kill_tracing_server")(self._handle_kill_server)
        app.route("/save_session")(self._handle_save_session)
        return app


class TracingSource:
    tftracer_version = __version__

    def __init__(self, **kwargs):
        self._run_profile = OrderedDict()
        self._traces = {}
        self.global_tracing = False
        self.running = False
        self._keep_traces = kwargs.get("keep_traces", 5)

    @staticmethod
    def get_run_context_key(run_context):
        return repr(run_context.original_args)

    def get_trace(self, run_id, trace_id):
        if run_id >= len(self._run_profile):
            return None
        if trace_id >= len(self._traces[run_id]):
            return None
        return self._traces[run_id][trace_id]

    def get_runs(self):
        return list(self._run_profile.values())

    def enable_tracing(self, run_id):
        profile = list(self._run_profile.values())[run_id]
        profile["tracing"] = True

    def enable_global_tracing(self):
        self.global_tracing = True

    def disable_global_tracing(self):
        self.global_tracing = False

    def is_tracing_on(self, run_context):
        if self.global_tracing:
            return True
        key = self.get_run_context_key(run_context)
        if key in self._run_profile:
            return self._run_profile[key]["tracing"]
        else:
            return False

    def before_run(self, run_context):
        key = self.get_run_context_key(run_context)

        if key not in self._run_profile:
            run_id = len(self._run_profile)
            profile = {
                "info": {
                    "fetches": repr(run_context.original_args.fetches),
                    "feeds": repr(run_context.original_args.feed_dict),
                    "options": repr(run_context.original_args.options)
                },
                "stats": {
                    "runs": 0,
                    "traces": 0,
                    "runtimes": datetime.timedelta(microseconds=0),
                    "first_run": datetime.datetime.now(),
                    "last_run": datetime.datetime.now(),
                },
                "traces": [
                ],
                "key": key,
                "run_id": run_id,
                "tracing": False,
            }
            self._run_profile[key] = profile
            self._traces[run_id] = []
        else:
            profile = self._run_profile[key]
            profile["stats"]["last_run"] = datetime.datetime.now()

    def add_run(self, run_context, run_values):
        key = self.get_run_context_key(run_context)
        profile = self._run_profile[key]

        # stats
        num_runs = profile["stats"]["runs"]
        old_runtime = profile["stats"]["runtimes"]
        profile["stats"]["runs"] += 1
        runtime = datetime.datetime.now() - profile["stats"]["last_run"]
        profile["stats"]["runtimes"] = (runtime + old_runtime * num_runs) / (num_runs + 1)

        if run_values.run_metadata.ByteSize() > 0:
            run_id = profile["run_id"]
            trace_id = len(self._traces[run_id])
            self._traces[run_id].append(run_values.run_metadata)
            profile["tracing"] = False
            profile["traces"].append(
                {
                    "trace_id": trace_id,
                    "date": datetime.datetime.now()
                }
            )
            profile["stats"]["traces"] = len(profile["traces"])
            if len(self._traces[run_id]) > self._keep_traces:
                self._traces[run_id][0] = None


class TracingServerHook(tf.train.SessionRunHook):
    def __init__(self, source):
        self._source = source

    def begin(self):
        super().begin()
        self._source.running = True

    def after_create_session(self, session, coord):
        super().after_create_session(session, coord)

    def before_run(self, run_context):
        super().before_run(run_context)
        self._source.before_run(run_context)
        if self._source.is_tracing_on(run_context):
            opts = (tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE))
            return tf.train.SessionRunArgs(None, None, options=opts)
        else:
            return None

    def after_run(self, run_context, run_values):
        super().after_run(run_context, run_values)
        self._source.add_run(run_context, run_values)

    def end(self, session):
        super().end(session)
        self._source.running = False


class TracingServer(VisualizationServer):
    """
    This class provides a ``tf.train.SessionRunHook`` to track session runs as well as a web interface to interact with
    users. By default, the web interface is accessible on `http://0.0.0.0:9999`.
    The web server stops at the end of the script. Use :func:`tftracer.TracingServer.join` to keep the server alive.

    Example:
        Estimator API:

        .. code-block:: python

            tracing_server = TracingServer()
            estimator.train(input_fn, hooks=[tracing_server.hook])

        Low-Level API:

        .. code-block:: python

            tracing_server = TracingServer()
            with tf.train.MonitoredTrainingSession(hooks=[tracing_server.hook]):
                ...

    Args:
        start_web_server_on_start (bool): If true a web server starts on object initialization. (default: true)
        server_port (int): TCP port to which web server listens (default: 9999)
        server_ip (str): IP Address to which web server listens (default: "0.0.0.0")
        keep_traces (int): Number of traces per run which the tracing server should keep. \
        the server discards the oldest traces when exeeced the limit. (default: 5)
    """

    def __init__(self, **kwargs):
        self._source = TracingSource(**kwargs)
        super().__init__("tftracer", self._source, **kwargs)
        start_web_server_on_start = kwargs.get("start_web_server_on_start", True)
        if start_web_server_on_start:
            self.start_web_server()
        self._hook = TracingServerHook(self._source)

    def save_session(self, filename):
        """
        Stores the tracing session to a pickle file.

        Args:
            filename: path to the trace session file.
        """
        with open(filename, "wb") as fp:
            pickle.dump(self._source, fp)

    def load_session(self, filename, gziped=None):
        """
        Loads a tracing session into the current tracing server.

        Caution:
            This action discards the current data in the session.

        Args:
            filename: path to the trace session file.
            gziped (bool): when set, determines if the trace file is gziped. when None, use gzip if the filename ends with ".gz";
        """
        running = self._source.running
        global_tracing = self._source.global_tracing
        gziped = filename.endswith(".gz") if gziped is None else gziped

        with open(filename, "rb") as fp:
            if gziped:
                data = gzip.decompress(fp.read())
                self._source = pickle.loads(data)
            else:
                self._source = pickle.load(fp)

        self._source.running = running
        self._source.global_tracing = global_tracing

    @property
    def hook(self):
        """
        Returns a ``tensorflow.train.SessionRunHook`` object.
        This object is meant to pass to tensorflow ``estimator`` API or ``MonitoredSession``.

        """

        return self._hook
