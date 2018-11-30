#! /usr/bin/env python -u
# coding=utf-8

# Using tracing server with TesorFlow Estimator API

__author__ = 'Sayed Hadi Hashemi'

import tensorflow as tf

import tftracer
tftracer.hook_inject()

import numpy as np

INPUT_SIZE = (299, 299, 3)
MINIBATCH_SIZE = 128
NUM_CLASSES = 1000
NUM_STEPS = 500


def input_fn():
    dataset = tf.data.Dataset.from_tensor_slices([0]).repeat(MINIBATCH_SIZE)
    dataset = dataset.map(
        lambda _:
        (
            {"x": np.random.uniform(size=INPUT_SIZE)},
            [np.random.random_integers(0, NUM_CLASSES)]
        )
    )
    dataset = dataset.repeat(NUM_STEPS).batch(MINIBATCH_SIZE)
    return dataset


def main():
    estimator = tf.estimator.DNNClassifier(
        hidden_units=[10] * 150,
        feature_columns=[tf.feature_column.numeric_column("x", shape=INPUT_SIZE)],
        n_classes=NUM_CLASSES,
    )
    estimator.train(input_fn)
    estimator.evaluate(input_fn)


if __name__ == '__main__':
    tf.logging.set_verbosity(tf.logging.INFO)
    main()
