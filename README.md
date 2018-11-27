# TensorFlow Runtime Tracer
This project is a web application to monitor and trace TensorFlow scripts in the runtime on the `op` level.

It starts a web server upon the execution of the script. The web interface keeps track of all the session runs and can trace the execution on demand.

The goal of this tool is to facilitate the process of performance tuning with minimal code changes and insignificant runtime overhead. Both Higher-level ([tf.estimator.Estimator](https://www.tensorflow.org/guide/estimators)) and Low-level ([tf.train.MonitoredTrainingSession](https://www.tensorflow.org/api_docs/python/tf/train/MonitoredTrainingSession) and co) APIs are supported. It also supports [horovod](https://github.com/uber/horovod) and [IBM Distributed Deep Learning (DDL)](https://dataplatform.cloud.ibm.com/docs/content/analyze-data/ml_dlaas_ibm_ddl.html).
The tracing session can be saved, reloaded, and distributed effortlessly.

Some screenshots [here](https://github.com/xldrx/tensorflow-tracer/blob/master/gallery).

## Installation
Use `pip` to install:
```bash
pip install tensorflow-tracer
```

## Quick Start
1. Add `tftracer` to your code:

    Estimator API:
    ```python
    from tftracer import TracingServer
    ...
    
    tracing_server = TracingServer()
    estimator.train(input_fn, hooks=[tracing_server.hook]) 
    ```
    
    Low-Level API:
    ```python
    from tftracer import TracingServer
    ...
    tracing_server = TracingServer()
    with tf.train.MonitoredTrainingSession(hooks=[tracing_server.hook]):
       ...
    ```
    
    [[More examples here]](https://github.com/xldrx/tensorflow-tracer/blob/master/examples/) 

2. Browse to:
```html
http://0.0.0.0:9999
``` 

## Command line
Tracing sessions can be stored either through the web interface or by calling `tracing_server.save_session(filename)`.

To reload a session, run this in the terminal:
```bash
tftracer filename
```

Then browse to:
```html
http://0.0.0.0:9999
``` 

## API
Full Documentation is [here](https://tensorflow-tracer.readthedocs.io/en/latest/).

## Known Bugs/Limitations
* Only Python3 is supported.
* The web interface loads javascript/css libraries remotely (e.g. `vue.js`, `ui-kit`, `jquery`, `jquery-ui`, `Google Roboto`, `awesome-icons`, ... ). Therefore an active internet connection is needed to properly render the interface. The tracing server does not require any remote connection. 
* All traces are kept in the memory while tracing server is running.
* Tracing uses `tf.train.SessionRunHook` and is unable to trace auxiliary runs such as `init_op`.
* The tracing capability is limited to what `tf.RunMetadata` offers. For example, CUPTI events are missing when tracing a distributed job.
* HTTPS is not supported. 

## Frequently Asked Questions

### How to trace/visualize just one session run?
Use `tftracer.Timeline`. for example:
```python
    from tftracer import Timeline
    ...
    with tf.train.MonitoredTrainingSession() as sess:
       with Timeline() as tl:
        sess.run(fetches, **tl.kwargs)
    ...
    tl.visualize(filename)
```

### Comparision to TensorBoard?
The nature of this project is a short-lived light-weight interactive tracing interface to monitor and trace execution on the `op`-level. In comparison `TensorBoard` is a full-featured tool to inspect the application on many levels:
* `tftracer` does not make any assumption about the dataflow DAG. There is no need to add any additional `op` to the data flow dag (i.e. `tf.summary`) or having a `global step`. 

* `tftracer` runs as a thread and lives from the start of the execution and lasts until the end of it. `TensorBoard` runs as a separate process and can outlive the main script.  

## Cite this tool
```latex
@misc{hashemi-tftracer-2018,
  author = {Sayed Hadi Hashemi},
  title = {TensorFlow Runtime Tracer},
  year = {2018},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/xldrx/tensorflow-tracer}},
}