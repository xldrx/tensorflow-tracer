#! /usr/bin/env python -u
# coding=utf-8

__author__ = 'Sayed Hadi Hashemi'

import tensorflow as tf
import horovod.tensorflow as hvd
from tensorflow.contrib.slim.nets import inception
from tftracer import TracingServer

INPUT_SIZE = [299, 299, 3]
MINIBATCH_SIZE = 4
NUM_CLASSES = 1000
NUM_STEPS = 200


def get_model():
    input_data = tf.random_uniform([MINIBATCH_SIZE] + INPUT_SIZE)
    labels = tf.random_uniform([MINIBATCH_SIZE, NUM_CLASSES])
    logit, _ = inception.inception_v3(input_data, num_classes=NUM_CLASSES)
    loss = tf.losses.softmax_cross_entropy(labels, logit)
    train_op = hvd.DistributedOptimizer(tf.train.MomentumOptimizer(0.01, 0.01)).minimize(loss)
    return train_op


def get_config():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.visible_device_list = str(hvd.local_rank())

    if hvd.rank() == 0:
        tf.logging.set_verbosity(tf.logging.INFO)
    else:
        tf.logging.set_verbosity(tf.logging.WARN)

    return dict(config=config)


def main(_):
    print(_)
    hvd.init()
    train_op = get_model()

    hooks = [
        hvd.BroadcastGlobalVariablesHook(0),
    ]

    if hvd.rank() == 0:
        tracing_server = TracingServer()
        hooks.append(tracing_server.hook)

    with tf.train.MonitoredTrainingSession(hooks=hooks, **get_config()) as sess:
        for _ in range(NUM_STEPS):
            sess.run(train_op)

    if hvd.rank() == 0:
        # Save the tracing session
        tracing_server.save_session("session.pickle")

        # Keep the tracing server running beyond training. Remove otherwise.
        tracing_server.join()


if __name__ == "__main__":
    tf.app.run()
