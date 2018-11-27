#! /usr/bin/env python3
# coding=utf-8
from __future__ import division
from __future__ import unicode_literals
from __future__ import with_statement
from __future__ import absolute_import
from io import open
import os
import random
import re
from datetime import datetime

import six
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Range1d, SingleIntervalTicker, WidgetBox, \
    HoverTool, CustomJS, Button, TapTool
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from jinja2 import Environment, FileSystemLoader

__author__ = 'Sayed Hadi Hashemi'


class TimelineVisualizer:
    def __init__(self, data_loader):
        self._load_templates()
        self._tools = self._get_tools()
        self._data_loader = data_loader
        self._iteration_time = 0

    def visualize(self, output_file=None):
        data = self._data_loader.get_data()
        self._iteration_time = max([max([event['end'] for event in device['events']]) for device in data])

        device_plots = []
        for device in data:
            plot, widget_box = self._generate_device_plot(device)
            device_plots += [[plot], [widget_box]]

        final_plot = gridplot(
            device_plots,
            toolbar_options={
                'logo': None,
            },
            sizing_mode='scale_width'
        )

        result = self._export_to_html(final_plot)

        if output_file:
            if six.PY2:
                with open(output_file, "wb") as fp:
                    fp.write(result.decode("utf-8").encode('utf-8'))
            elif six.PY3:
                with open(output_file, "w") as fp:
                    fp.write(result)
            else:
                raise Exception("Unsupported Python Version")
        else:
            return result

    def _load_templates(self):
        _template_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/templates/')),
        )

        self._js_on_change_callback = _template_env.get_template("on_change_callback.js").render()
        self._js_on_click_callback = _template_env.get_template("on_click_callback.js").render()
        self._js_update_ranges = _template_env.get_template("update_ranges.js").render()
        self._js_on_hover_callback = _template_env.get_template("on_hover_callback.js").render()
        self._main_template = _template_env.get_template("timeline.html")
        self._tooltips_template = _template_env.get_template("tooltips.html").render()

    def _get_tools(self):
        def boxed(content, tag='div'):
            return "<{tag} class='xl-box'>{content}</{tag}>".format(
                content=content,
                tag=tag)

        callback = CustomJS(code=self._js_on_hover_callback)

        hover = HoverTool(tooltips=self._tooltips_template, mode='mouse',
                          point_policy='follow_mouse', attachment='below', show_arrow=False,
                          anchor="bottom_center",
                          callback=callback
                          )

        tap = TapTool(callback=CustomJS(code=self._js_on_click_callback))

        tools = "xzoom_in,xzoom_out,xpan,xbox_zoom,xwheel_zoom,xwheel_pan,reset,undo,redo,crosshair".split(',')
        tools += [hover, tap]

        return tools

    def _generate_device_plot(self, device_events):
        data_source = self._convert_events_to_datasource(device_events['events'])
        n_rows = device_events['n_rows']
        if n_rows == 0:
            n_rows = 1
        elif n_rows == 1:
            n_rows = 2
        name = device_events['name']

        plot = figure(
            title="{}".format(name),
            plot_height=20 * n_rows + 60,
            plot_width=1200,
            tools=self._tools,
            sizing_mode='scale_width',
            active_scroll='xwheel_zoom'
        )
        plot.hbar(
            left='start',
            right='end',
            y='height',
            color='color',
            height=0.85,
            source=data_source,
            hover_fill_alpha=0.5,
            line_join='round',
            line_cap='round',
            hover_line_color='red'
        )

        plot.x_range = Range1d(0, self._iteration_time, bounds="auto")
        plot.y_range = Range1d(0, n_rows)

        plot.yaxis.visible = False
        plot.ygrid.ticker = SingleIntervalTicker(interval=1)
        plot.ygrid.grid_line_color = None
        plot.ygrid.band_fill_alpha = 0.1
        plot.ygrid.band_fill_color = "gray"

        button = Button(label=" Sync", width=20, button_type='primary', disabled=True)
        button.css_classes = ['xl-hidden']
        button.js_on_click(
            CustomJS(
                args={
                    'me': plot,
                },
                code=self._js_update_ranges
            )
        )

        plot.x_range.js_on_change(
            'start',
            CustomJS(
                args={
                    'button': button,
                },
                code=self._js_on_change_callback)
        )

        return plot, WidgetBox(button)

    @staticmethod
    def _convert_events_to_datasource(device_data, base_row=0):
        def get_col(column_name, offset=None):
            if offset:
                return [item[column_name] + offset for item in device_data]
            else:
                return [item[column_name] for item in device_data]

        return ColumnDataSource(data=dict(
            duration=get_col("duration"),
            start=get_col("start"),
            end=get_col('end'),
            height=get_col('row', base_row + 0.5),
            color=get_col('color'),
            row=get_col('row', base_row),
            name=get_col('name'),
            description=get_col('description'),
            details=get_col('details'),
            op=get_col('op'),
            inputs=["".join(["<li>{}</li>".format(i) for i in item.split()]) for item in get_col('inputs')]
        ))

    def _export_to_html(self, plot):
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        script, div = components(plot)
        html = self._main_template.render(
            plot_script=script,
            plot_div=div,
            js_resources=js_resources,
            css_resources=css_resources,
            title="TensorFlow Timeline",
            header=str(datetime.now()),
            custom_css='',
            custom_header='',
            custom_js=''
        )

        return encode_utf8(html)


class DataLoader:
    def __init__(self, run_metadata, device_pattern=None):
        self._device_pattern_re = re.compile(device_pattern if device_pattern else "^.*$")
        self._step_stats = run_metadata.step_stats
        self.comm_op_name = "RecvTensor"

    @staticmethod
    def _assign_row(events):
        rows = []
        for event in sorted(events, key=lambda x: x['start']):
            assigned = False
            for i, row in enumerate(rows):
                if row <= event['start']:
                    event['row'] = i
                    rows[i] = event['end']
                    assigned = True
                    break
            if not assigned:
                event['row'] = len(rows)
                rows.append(event['end'])
        return len(rows)

    @staticmethod
    def _assign_color(events):
        for event in events:
            rand = random.Random(event['op'])
            event['color'] = "#%02x%02x%02x" % (rand.randint(0, 256), rand.randint(0, 256), rand.randint(0, 256))

    @staticmethod
    def _parse_event_description(label):
        """Parses the fields in a node timeline label."""
        # Expects labels of the form: name = op(arg, arg, ...).
        match = re.match(r'(.*) = (.*)\((.*)\)', label)
        if match is None:
            return 'unknown', 'unknown', []
        nn, op, inputs = match.groups()
        if not inputs:
            inputs = []
        else:
            inputs = inputs.split(', ')
        return nn, op, inputs

    def _fix_op_names(self, events):
        for event in events:
            _, op, inputs = self._parse_event_description(event['description'])
            if op == "unknown":
                op = event['name']
                inputs = ""
            event['op'] = op
            event['inputs'] = "\n\n".join(inputs)

    def _process_device(self, device_name, node_stats, base_timestamp):
        device_events = []

        for node in node_stats:
            device_events.append(dict(
                start=(node.all_start_micros - base_timestamp) / 1000,
                end=(max(node.all_end_rel_micros, 1) + node.all_start_micros - base_timestamp) / 1000,
                duration=node.all_end_rel_micros / 1000,
                name=node.node_name,
                description=node.timeline_label,
                details=str(node).replace("\n", "\n\n")
            ))

        self._fix_op_names(device_events)
        self._assign_color(device_events)
        n_rows = self._assign_row(device_events)

        return dict(
            name=device_name,
            n_rows=n_rows,
            events=device_events
        )

    def _find_minimum_timestamp(self):
        return min([
            min([node.all_start_micros for node in device.node_stats])
            for device in self._step_stats.dev_stats if len(self._device_pattern_re.findall(device.device)) > 0
        ])

    def __is_communication_op(self, op):
        if " = HorovodAllreduce(" in op.timeline_label:
            return True
        else:
            return op.node_name == self.comm_op_name

    def get_data(self):
        stats = self._step_stats
        events = []

        base_timestamp = self._find_minimum_timestamp()

        for device in stats.dev_stats:
            device_name = device.device
            if len(self._device_pattern_re.findall(device_name)) == 0:
                print(("ignoring device: {}".format(device_name)))
                continue
            device_events = self._process_device(
                device_name,
                [node for node in device.node_stats if
                 not self.__is_communication_op(node)],
                base_timestamp
            )
            if len(device_events["events"]) > 0:
                events.append(device_events)

            device_events = self._process_device(
                device_name + " (Communication)",
                [node for node in device.node_stats if
                 self.__is_communication_op(node)],
                base_timestamp
            )
            if len(device_events["events"]) > 0:
                events.append(device_events)

        events.sort(key=lambda x: x['name'])
        return events
