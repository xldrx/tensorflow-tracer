.. tensorflow-tracer documentation master file, created by
   sphinx-quickstart on Sun Nov 25 23:02:10 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TensorFlow Runtime Tracer documentation!
====================================================

TensorFlow Runtime Tracer is a web application to monitor and trace TensorFlow scripts in the runtime on the ``op`` level.

It starts a web server upon the execution of the script. The web interface keeps track of all the session runs and can trace the execution on demand.

The goal of this tool is to facilitate the process of performance tuning with minimal code changes and insignificant runtime overhead. Both Higher-level (\ `tf.estimator.Estimator <https://www.tensorflow.org/guide/estimators>`_\ ) and Low-level (\ `tf.train.MonitoredTrainingSession <https://www.tensorflow.org/api_docs/python/tf/train/MonitoredTrainingSession>`_ and co) APIs are supported. It also supports `horovod <https://github.com/uber/horovod>`_ and `IBM Distributed Deep Learning (DDL) <https://dataplatform.cloud.ibm.com/docs/content/analyze-data/ml_dlaas_ibm_ddl.html>`_.
The tracing session can be saved, reloaded, and distributed effortlessly.

Installation
============

Use ``pip`` to install:

.. code-block:: bash

   pip install tensorflow-tracer

Quick Start
===========


#.
   Add ``tftracer`` to your code:

      Estimator API:

      .. code-block:: python

          from tftracer import TracingServer
          ...

          tracing_server = TracingServer()
          estimator.train(input_fn, hooks=[tracing_server.hook])

      Low-Level API:

      .. code-block:: python

          from tftracer import TracingServer
          ...
          tracing_server = TracingServer()
          with tf.train.MonitoredTrainingSession(hooks=[tracing_server.hook]):
             ...

#.
   Browse to:

   .. code-block:: html

      http://0.0.0.0:9999

Command line
============

Tracing sessions can be stored either through the web interface or by calling :func:`tftracer.TracingServer.save_session`.

To reload a session, run this in the terminal:

.. code-block:: bash

   tftracer filename

Then browse to:

.. code-block:: html

   http://0.0.0.0:9999

Full Usage
----------
.. code-block:: bash

   usage: tftracer [-h] [--port PORT] [--ip IP] session_file

   positional arguments:
     session_file  Path to the trace session file

   optional arguments:
     -h, --help    show this help message and exit
     --port PORT   To what TCP port web server to listen
     --ip IP       To what IP address web server to listen

Examples
========
.. glossary::

   Higher-Level API <`estimator-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/estimator-example.py>`__>
      Example of using :class:`tftracer.TracingServer` with TensorFlow ``estimator`` API.

   Low-Level API <`monitoredtrainingsession-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/monitoredtrainingsession-example.py>`__>
      Example of using :class:`tftracer.TracingServer` with TensorFlow ``MonitoredTrainingSession`` API.

   Horovod: One Process <`horovod-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/horovod-example.py>`__>
      Example of using :class:`tftracer.TracingServer` with ``horovod``. In this example only the one process is being traced.

   Horovod: All Processes <`horovod-all-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/horovod-all-example.py>`__>
      Example of using :class:`tftracer.TracingServer` with ``horovod``. In this example all processes are being traced.

   Timeline <`timeline-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/timeline-example.py>`__>
      Example of using :class:`tftracer.Timeline` to trace and visualize one ``session.run`` call without a tracing server.

   Load Session <`load_session-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/load_session-example.py>`__>
      Example of saving and loading tracing sessions.

   TracingServer Options <`options-example.py <https://github.com/xldrx/tensorflow-tracer/blob/master/examples/options-example.py>`__>
      Example of setting tracing options.


API Reference
=============

tftracer.TracingServer
----------------------
.. autoclass:: tftracer.TracingServer
    :members:
    :inherited-members:
    :undoc-members:

tftracer.Timeline
-----------------
.. autoclass:: tftracer.Timeline
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: communication_elapsed_time, communication_time, computation_time



Known Bugs/Limitations
======================

* Only Python3 is supported.
* The web interface loads javascript/css libraries remotely (e.g. ``vue.js``\ , ``ui-kit``\ , ``jquery``\ , ``jquery-ui``\ , ``Google Roboto``\ , ``awesome-icons``\ , ... ). Therefore an active internet connection is needed to properly render the interface. The tracing server does not require any remote connection.
* All traces are kept in the memory while tracing server is running.
* Tracing uses ``tf.train.SessionRunHook`` and is unable to trace auxiliary runs such as ``init_op``.
* The tracing capability is limited to what ``tf.RunMetadata`` offers. For example, CUPTI events are missing when tracing a distributed job.
* HTTPS is not supported.


Frequently Asked Questions
==========================

How to trace/visualize just one session run?
--------------------------------------------

Use ``tftracer.Timeline``. for example:

.. code-block:: python

       from tftracer import Timeline
       ...
       with tf.train.MonitoredTrainingSession() as sess:
          with Timeline() as tl:
           sess.run(fetches, **tl.kwargs)
       ...
       tl.visualize(filename)

Comparision to TensorBoard?
---------------------------

The nature of this project is a short-lived light-weight interactive tracing interface to monitor and trace execution on the ``op``\ -level. In comparison ``TensorBoard`` is a full-featured tool to inspect the application on many levels:


*
  ``tftracer`` does not make any assumption about the dataflow DAG. There is no need to add any additional ``op`` to the data flow dag (i.e. ``tf.summary``\ ) or having a ``global step``.

*
  ``tftracer`` runs as a thread and lives from the start of the execution and lasts until the end of it. ``TensorBoard`` runs as a separate process and can outlive the main script.
