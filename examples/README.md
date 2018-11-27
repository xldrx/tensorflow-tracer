# Examples

### Higher-Level API
[estimator-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/estimator-example.py)
<br/>
Example of using `tftracer.TracingServer` with TensorFlow ``estimator`` API.

### Low-Level API
[monitoredtrainingsession-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/monitoredtrainingsession-example.py)
<br/>
Example of using `tftracer.TracingServer` with TensorFlow `MonitoredTrainingSession` API.
   
### Horovod: One Process
[horovod-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/horovod-example.py)
<br/>
Example of using `tftracer.TracingServer` with `horovod`. In this example only the one process is being traced.

### Horovod: All Processes
[horovod-all-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/horovod-all-example.py)
<br/>     
Example of using `tftracer.TracingServer` with `horovod`. In this example all processes are being traced.

### Timeline
[timeline-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/timeline-example.py)
<br/>
Example of using :class:`tftracer.Timeline` to trace and visualize one ``session.run`` call without a tracing server.

### Load Session
[load_session-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/load_session-example.py)
<br/>
Example of saving and loading tracing sessions.

### TracingServer Options
[options-example.py](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/options-example.py)
<br/>
Example of setting tracing options.
