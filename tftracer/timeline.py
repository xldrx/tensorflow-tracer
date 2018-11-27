#! /usr/bin/env python -u
# coding=utf-8
from __future__ import absolute_import
from __future__ import with_statement

import math
import pickle
import time
from io import open
from .timeline_visualizer import DataLoader, TimelineVisualizer
import tensorflow
__author__ = 'Sayed Hadi Hashemi'


class Timeline(object):
    """
    This class traces a session run and visualizes the execution timeline.

    Example:

        .. code-block:: python

            with Timeline() as tl:
                sess.run(fetches, **tl.kwargs)

    Args:
        run_metadata (tensorflow.RunMetadata): If set a web server starts on object initialization. (default: true)
    """
    def __init__(self, run_metadata=None, **kwargs):
        self._elapsed = 0
        self._run_metadata = run_metadata
        self._options = None
        comm_op_name = kwargs.get("comm_op_name", None)
        self._comm_op_name = comm_op_name if comm_op_name is not None else "RecvTensor"

    def __is_communication_op(self, op):
        if " = HorovodAllreduce(" in op.timeline_label:
            return True
        else:
            return op.node_name == self._comm_op_name

    def __enter__(self):
        from tensorflow import RunMetadata, RunOptions

        self.__start = time.time()
        self._run_metadata = RunMetadata()
        self._options = RunOptions(trace_level=RunOptions.FULL_TRACE, output_partition_graphs=True)

        return self

    def __exit__(self, *args):
        self._elapsed = time.time() - self.__start

    @property
    def kwargs(self):
        """
        Returns a dict of config_pb2.RunOptions. This object should be unpacked and passed to session.run.

        Example: ::

            session.run(fetches, **timeline.kwargs)
        """
        if self._run_metadata is None:
            raise Exception("TensorFlow is not found")
        return dict(run_metadata=self._run_metadata, options=self._options)

    def visualize(self, output_file=None, device_pattern=None):
        """
        Visualizes the runtime_metadata and saves it as a HTML file.
        Args:
            output_file (str): the output file path. If is None, returns the HTML content instead.
            device_pattern (str): a regex pattern used to choose which device to be included.
            If None, all devices are used.

        Returns:
            str: If output_file is None returns the HTML content, otherwise returns None.

        """
        data_loader = DataLoader(self._run_metadata, device_pattern)
        visualizer = TimelineVisualizer(data_loader)
        return visualizer.visualize(output_file)

    def step_time(self, device_search_pattern=None):
        """
        Calculate the step time.
        Args:
            device_search_pattern (str): a regex pattern used to choose which device to be included.
            If None, all devices are used.

        Returns:
            float: the time in seconds.

        """
        max_time = 0
        min_time = math.inf
        device_search = "" if device_search_pattern is None else device_search_pattern
        all_ops = []
        for device in [d for d in self._run_metadata.step_stats.dev_stats if device_search in d.device]:
            all_ops += device.node_stats
        for op in sorted(all_ops, key=lambda a: a.all_start_micros):
            min_time = min(min_time, op.all_start_micros)
            max_time = max(max_time, op.all_start_micros + op.all_end_rel_micros)
        return max_time - min_time if min_time != math.inf else 0

    def communication_elapsed_time(self, device_search_pattern=None, exclude_pattern=None):
        max_time = 0
        min_time = math.inf
        device_search = "" if device_search_pattern is None else device_search_pattern
        all_ops = []
        for device in [d for d in self._run_metadata.step_stats.dev_stats if device_search in d.device]:
            all_ops += device.node_stats
        for op in sorted(all_ops, key=lambda a: a.all_start_micros):
            if not self.__is_communication_op(op):
                continue
            if exclude_pattern is not None and exclude_pattern in op.timeline_label:
                continue
            min_time = min(min_time, op.all_start_micros)
            max_time = max(max_time, op.all_start_micros + op.all_end_rel_micros)
        return max_time - min_time if min_time != math.inf else 0

    def communication_time(self, device_search_pattern=None, exclude_pattern=None):
        device_search = "" if device_search_pattern is None else device_search_pattern
        all_ops = []
        for device in [d for d in self._run_metadata.step_stats.dev_stats if device_search in d.device]:
            all_ops += device.node_stats

        last_ = -math.inf
        total = 0
        for op in sorted(all_ops, key=lambda a: a.all_start_micros):
            if not self.__is_communication_op(op):
                continue
            if exclude_pattern is not None and exclude_pattern in op.timeline_label:
                continue
            if op.all_start_micros > last_:
                total += op.all_end_rel_micros
            elif op.all_start_micros + op.all_end_rel_micros > last_:
                total += op.all_start_micros + op.all_end_rel_micros - last_
            last_ = max(last_, op.all_start_micros + op.all_end_rel_micros)

        return total

    def computation_time(self, device_search_pattern=None, exclude_pattern=None):
        device_search = "" if device_search_pattern is None else device_search_pattern
        all_ops = []
        for device in [d for d in self._run_metadata.step_stats.dev_stats if device_search in d.device]:
            all_ops += device.node_stats

        last_ = -math.inf
        total = 0
        for op in sorted(all_ops, key=lambda a: a.all_start_micros):
            if exclude_pattern is not None and exclude_pattern in op.timeline_label:
                continue
            if op.all_start_micros > last_:
                total += op.all_end_rel_micros
            elif op.all_start_micros + op.all_end_rel_micros > last_:
                total += op.all_start_micros + op.all_end_rel_micros - last_
            last_ = max(last_, op.all_start_micros + op.all_end_rel_micros)

        return total

    @property
    def wall_clock_elapsed(self):
        """
        Time elapsed in ``with Timeline()`` statement.

        Returns:
            float: the time in seconds.
        """
        return self._elapsed

    @classmethod
    def from_pickle(cls, pickle_file_name, **kwargs):
        """
        Load a timeline form a pickle file.

        Args:
            pickle_file_name (str): pickle file path.
            **kwargs: same as Timeline class.

        Returns:
            a Timeline object with the content of pickle_file_name.

        """
        with open(pickle_file_name, "rb") as fp:
            run_metadata = pickle.load(fp)
        return cls(run_metadata=run_metadata, **kwargs)

    def to_pickle(self, pickle_file_name):
        """
        Save the timeline in a pickle file.
        Returns:
            None.

        Raises:
            Exception: if the timeline trace is empty.
        """
        if self._run_metadata is None:
            raise Exception("No data has been collected yet")

        with open(pickle_file_name, "wb") as fp:
            pickle.dump(self._run_metadata, fp)
