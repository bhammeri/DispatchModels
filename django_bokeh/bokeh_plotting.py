import bokeh.plotting as bplt
from bokeh.models import Legend, LegendItem, ColumnDataSource,  FactorRange, DataRange1d, Plot, LinearAxis, Grid, Range1d
from bokeh.models import HoverTool, PanTool, SaveTool, UndoTool, RedoTool, ZoomInTool, ZoomOutTool, BoxZoomTool, ResetTool
from bokeh.models.glyphs import VBar
from bokeh.io import curdoc, output_notebook
from bokeh.models.annotations import Title
from bokeh.palettes import Category20, Spectral
from bokeh.core.properties import value as bokeh_value
from bokeh.transform import dodge

import numpy as np

from math import pi, isnan
from pandas.api.types import is_datetime64_ns_dtype

# stacked bar chart
def stacked_bar_chart(df, cmap, value_key, group_by, title='', xlabel='Years', ylabel='Diff. Capacity [GW]', width=850, height=400, split_neg_pos_by=None, extra_lines=None, extra_lines_y_axis=None, ):
    """
    df: df to plot. long format
    cmap: colour map dict with [category key] = colour
    value_key: sets the height of the bars elements
    group_by: ['category', 'x-label'] -> category is used to stack the bars and colour them, x-label distribute the stacked bars on the x axis
    title: Graph title
    xlabel:
    ylabel:
    width:
    height:
    split_pos_neg_by: Values are filtered for positive and negative values. For import/export NTC flows for each year each year has positive and negative values.
                So it is necessary to drop the 0 values otherwise the information cannot be plotted.
    extra_lines: dataframe like for line plot
    extra_lines_y_axis: list of columns to go to the second y axis

    """

    # round the difference to 2 decimals places
    df = df.round(4)

    # set all positive numbers to 0
    all_negative = df.copy(deep=True)
    all_negative.loc[all_negative[value_key] >= 0, value_key] = 0
    all_negative.fillna(0, inplace=True)
    # if drop_zeros then drop all the zeros
    if split_neg_pos_by:
        split_column = list(split_neg_pos_by.keys())[0]
        splite_arguments = split_neg_pos_by[split_column]
        all_negative = all_negative[all_negative[split_column] == splite_arguments[0]]
    all_negative.set_index(group_by, inplace=True)

    # set all negative numbers to 0
    all_positive = df.copy(deep=True)
    all_positive.loc[all_positive[value_key] <= 0, value_key] = 0
    all_positive.fillna(0, inplace=True)
    # if drop_zeros then drop all the zeros
    if split_neg_pos_by:
        split_column = list(split_neg_pos_by.keys())[0]
        splite_arguments = split_neg_pos_by[split_column]
        all_positive = all_positive[all_positive[split_column] == splite_arguments[1]]
    all_positive.set_index(group_by, inplace=True)

    # groupings
    categories = sorted(list(df[group_by[0]].unique())) # keeps the defined order

    # check the type of x labels - need to be converted to strings
    if is_datetime64_ns_dtype(df[group_by[1]]):
        # convert datetime to string
        xs = df[group_by[1]].dt.strftime('%Y.%m.%d - %H').unique()

    else:
        xs = df[group_by[1]].unique()

    xs = sorted(list(xs)) # maybe check if there is data for each tech and year?

    # create index
    df.set_index(group_by, inplace=True)

    idx = pd.IndexSlice

    # create the figure handle

    hover_stack = HoverTool(tooltips=[
        ("%s: " % (group_by[0][0].upper() + group_by[0][1:]), "@cat"),
        ("%s: " % (group_by[1][0].upper() + group_by[1][1:]), "@x"),
        ("%s: " % (value_key.upper() + value_key[1][1:]), "@count"),
    ], names=['stack'])

    hover_lines = HoverTool(tooltips=[
        ("Type: ", "@type"),
        ("%s: " % (group_by[1][0].upper() + group_by[1][1:]), "@x"),
        ("Value: ", "@y"),
    ], names=['lines'])

    # plot tools
    tools = [PanTool, SaveTool, UndoTool, RedoTool, ZoomInTool, ZoomOutTool, BoxZoomTool, ResetTool]
    called_tools = [item() for item in tools] + [hover_stack, hover_lines]

    p = bplt.figure(plot_width=width, plot_height=height, title="", x_range=xs, tools=called_tools, toolbar_location="above")

    # plot all the positive values
    lower_bound = np.array([0 ] *len(xs)) # lower bound for boxes
    upper_bound = np.array([0 ] *len(xs)) # upper bound for boxes
    positive_rs = []
    for index, cat in enumerate(categories):
        # if df.loc[idx[cat,:], value_key].sum() != 0:

        colour = cmap[cat]

        if cat in all_positive.index:
            values = all_positive.loc[idx[cat, :], value_key].values
        else:
            values = [0 ] *len(xs)

        upper_bound = lower_bound + values

        source = {
            'x': xs,
            'top': upper_bound,
            'bottom': lower_bound,
            'count': values,
            'cat': [cat ] *len(xs)
        }

        positive_rs.append \
            (p.vbar(source=source, x='x', top='top', bottom='bottom', width=0.75, fill_color=colour, muted_color=colour, muted_alpha=0.4, line_width=0.1, line_color="black", name='stack'))

        # set lower_bound to upper_bound
        lower_bound = upper_bound

    # plot all the negative values
    lower_bound = np.array([0 ] *len(xs)) # lower bound for boxes
    upper_bound = np.array([0 ] *len(xs)) # upper bound for boxes
    negative_rs = []
    for index, cat in enumerate(categories):
        # if df.loc[idx[cat,:], value_key].sum() != 0:
        colour = cmap[cat]

        if cat in all_positive.index:
            values = all_negative.loc[idx[cat, :], value_key].values
        else:
            values = [0 ] *len(xs)

        upper_bound = lower_bound + values

        source = {
            'x': xs,
            'top': upper_bound,
            'bottom': lower_bound,
            'count': values,
            'cat': [cat ] *len(xs)
        }

        # negative_rs.append(p.vbar(xs, 0.7, upper_bound, lower_bound, fill_color=colour, line_color="black", name=cat, source=source))
        negative_rs.append \
            (p.vbar(source=source, x='x', top='top', bottom='bottom', width=0.75, fill_color=colour, muted_color=colour, muted_alpha=0.25, line_width=0.1, line_color="black", name='stack'))

        # set lower_bound to upper_bound
        lower_bound = upper_bound

        # plot extra lines if provided
    if extra_lines is not None:
        lines_to_plot = extra_lines

        # add extra y axis
        if extra_lines_y_axis is not None:
            # get min, max for
            _min = 99999
            _max = -99999
            for line in extra_lines_y_axis:
                if line in lines_to_plot.columns:
                    _min_column = lines_to_plot[line].min()
                    if _min_column < _min:
                        _min = _min_column

                    _max_column = lines_to_plot[line].max()
                    if _max_column > _max:
                        _max = _max_column

            # scale the window 10% larger than the actual min, max values to be plotted
            if _min < 0:
                _min = 1.1 * _min
            else:
                _min = 0.9 * _min

            if _max > 0:
                _max = 1.1 * _max
            else:
                _max = 0.9 * _max

            # check that _min, _max cannot be nan
            if isnan(_min):
                _min = 0

            if isnan(_max):
                _max = 1

            p.extra_y_ranges = {"SecondYAxis": Range1d(start=_min, end=_max)}
            p.add_layout(LinearAxis(y_range_name="SecondYAxis"), 'right')

        # lines colour map
        # setup the colour map
        lines_cmap = Spectral[11]

        # retrieve the x values

        # convert index to string if necessary
        if isinstance(lines_to_plot.index, pd.DatetimeIndex):
            x_all_values = list(lines_to_plot.index.strftime('%Y.%m.%d - %H'))
        else:
            x_all_values = list(lines_to_plot.index)

        # add a line renderer
        legend_items = []
        for index, line in enumerate(lines_to_plot.columns):
            new_line = []

            y = list(lines_to_plot[line].values)

            # get rid of NaN values
            xy = [item for item in zip(x_all_values, y) if not np.isnan(item[1])]
            # x = [item[0] for item in xy]
            # y = [item[1] for item in xy]
            source = {
                'x': [item[0] for item in xy],
                'y': [item[1] for item in xy],
                'type': [line ] *len(xy)
            }

            # change to source and change hover tool for circles!

            if line in extra_lines_y_axis:
                new_line.append(p.line(source=source, x='x', y='y',
                                       line_width=2,
                                       color=lines_cmap[index % len(lines_cmap)], y_range_name='SecondYAxis', name='lines'))

                new_line.append(p.circle(source=source, x='x', y='y',
                                         line_width=2,
                                         color=lines_cmap[index % len(lines_cmap)], y_range_name='SecondYAxis', name='lines'))

            else:
                new_line.append(p.line(source=source, x='x', y='y',
                                       line_width=2,
                                       color=lines_cmap[index % len(lines_cmap)], name='lines'))

                new_line.append(p.circle(source=source, x='x', y='y',
                                         line_width=2,
                                         color=lines_cmap[index % len(lines_cmap)], name='lines'))

    # create the legend
    legend_items = []
    for index, cat in enumerate(categories):
        new_item = (cat, [positive_rs[index], negative_rs[index]])
        legend_items.append(new_item)

    legend_items.reverse()

    legend = Legend(items=legend_items, location=(0, 0))

    # legend.legend.location = 'top_left'
    legend.click_policy ="mute"

    p.add_layout(legend, 'right')

    if title:
        p.title.text = title

    # axes
    p.xaxis.axis_label = xlabel
    p.yaxis.axis_label = ylabel
    p.xaxis.major_label_orientation = pi /2

    bplt.show(p)



def line_chart(lines_to_plot, title='', xticks=None, xlabel='', ylabel='', width=800, height=400,
               colour_map='Category20', yrange=None):
    """
    lines_to_plot = dataframe in wide format (pivot: index=x, columns=scenario_names, values=values)

        - x: the index of the dataframe
        - name of the lines: column names

    :param colour_map: 'Category20', 'Spectral'
    """

    # setup the colour map
    if colour_map == 'Category20':
        cmap = Category20[20]
    else:
        cmap = Spectral[11]

    # to show scenario name -> https://github.com/bokeh/bokeh/issues/3454#issuecomment-168238796
    hover = HoverTool(tooltips=[
        ("{x}: ".format(x=xlabel), "@x"),
        ("{y}: ".format(y=ylabel), "@y"),
        ("Scenario", "@scenario")
    ])

    tools = [PanTool, SaveTool, UndoTool, RedoTool, ZoomInTool, ZoomOutTool, BoxZoomTool, ResetTool]
    called_tools = [item() for item in tools] + [hover]

    line_plot = bplt.figure(plot_width=width, plot_height=height, tools=called_tools, toolbar_location="above")

    # retrieve the x values
    x_all_values = list(lines_to_plot.index)

    # add a line renderer
    legend_items = []
    for index, line in enumerate(lines_to_plot.columns):
        new_line = []

        y = list(lines_to_plot[line].values)

        # get rid of NaN values
        xy = [item for item in zip(x_all_values, y) if not np.isnan(item[1])]
        source = {
            'x': [item[0] for item in xy],
            'y': [item[1] for item in xy],
            'scenario': [line] * len(xy)
        }

        new_line.append(line_plot.line(source=source, x='x',
                                       y='y',
                                       line_width=2,
                                       color=cmap[index % len(cmap)],
                                       name=str(line)))

        new_line.append(line_plot.circle(source=source, x='x',
                                         y='y',
                                         line_width=2,
                                         color=cmap[index % len(cmap)],
                                         name=str(line)))

        legend_items.append((str(line), new_line[:]))

    legend = Legend(items=legend_items, location=(0, 0))

    # legend.legend.location = 'top_left'
    legend.click_policy = "hide"

    if title:
        line_plot.title.text = title

    line_plot.add_layout(legend, 'right')

    # axis
    line_plot.x_range.range_padding = 0.05
    line_plot.xaxis.axis_label = xlabel
    line_plot.yaxis.axis_label = ylabel

    _min = lines_to_plot.min().min()
    if _min < 0:
        _min = 1.1 * _min
    else:
        _min = 0.9 * _min

    _max = lines_to_plot.max().max()

    if _max > 0:
        _max = 1.1 * _max
    else:
        _max = 0.9 * _max

    # check that _min, _max cannot be nan
    if isnan(_min):
        _min = 0

    if isnan(_max):
        _max = 1

    # yrange
    if yrange is not None:
        assert isinstance(yrange, list)
        if yrange[0] is not None:
            _min = yrange[0]

        if yrange[1] is not None:
            _max = yrange[1]

    line_plot.y_range = Range1d(_min, _max)

    # x axis - tick labels
    if xticks:
        assert len(xticks) == len(x_all_values)

        # create a dict
        ticks = {}
        for index, item in enumerate(xticks):
            ticks[x_all_values[index]] = item

        line_plot.xaxis.major_label_overrides = ticks

    bplt.show(line_plot)
