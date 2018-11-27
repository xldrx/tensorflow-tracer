# #! /usr/bin/env python -u
# # coding=utf-8

# Using tracing server with TesorFlow low level API
import webbrowser

__author__ = 'Sayed Hadi Hashemi'
import tensorflow as tf
from tensorflow.contrib.slim.nets import inception
from tftracer import Timeline

INPUT_SIZE = [299, 299, 3]
MINIBATCH_SIZE = 4
NUM_CLASSES = 1000
NUM_STEPS = 200


def get_model():
    input_data = tf.random_uniform([MINIBATCH_SIZE] + INPUT_SIZE)
    labels = tf.random_uniform([MINIBATCH_SIZE, NUM_CLASSES])
    logit, _ = inception.inception_v3(input_data, num_classes=NUM_CLASSES)
    loss = tf.losses.softmax_cross_entropy(labels, logit)
    train_op = tf.train.MomentumOptimizer(0.01, 0.01).minimize(loss)
    return train_op


def main():
    train_op = get_model()
    with tf.train.MonitoredTrainingSession() as sess:
        with Timeline() as timeline:
            sess.run(train_op, **timeline.kwargs)

    # Save
    timeline.to_pickle("step.pickle")

    # Load
    timeline = Timeline.from_pickle("step.pickle")

    # Visualize
    timeline.visualize("step.html")
    webbrowser.open_new("step.html")


if __name__ == '__main__':
    tf.logging.set_verbosity(tf.logging.INFO)
    main()
