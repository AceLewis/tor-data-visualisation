import itertools
import io
import time

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import transforms
plt.rcdefaults()


def find_renderer(fig):
    """Find the renderer used"""
    if hasattr(fig.canvas, "get_renderer"):
        # Some backends, such as TkAgg, have the get_renderer method, which
        # makes this easy.
        renderer = fig.canvas.get_renderer()
    else:
        # Other backends do not have the get_renderer method, so we have a work
        # around to find the renderer. Print the figure to a temporary file
        # object, and then grab the renderer that was used.
        # (I stole this trick from the matplotlib backend_bases.py
        # print_figure() method.)
        fig.canvas.print_pdf(io.BytesIO())
        renderer = fig._cachedRenderer
    return renderer


def get_text_length(text, **kwargs):
    """Function to get the length of a text box for the text provided."""
    # I could not find a nice way to do this so I have to create a temp figure to render
    # to then grab the size of the textbox.
    plt.ioff()  # So temp figures don't flash
    temp_fig = plt.figure()
    renderer = mpl.backend_bases.RendererBase()
    text_box = plt.text(0, 0, text, **kwargs)
    text_box_dim = text_box.get_window_extent(renderer=renderer)
    # Close the temp figure
    plt.close(temp_fig)
    return (text_box_dim.width, text_box_dim.height)


def text_multiple_colours(ax, x, y, strings, colours, dpi, svg_fix, **kwargs):
    """Show text with multiple colours, needed only in plots with normal and exit"""
    transform = plt.gca().transData

    for string, colour in zip(strings, colours):
        text = ax.text(x, y, string+" ", color=colour, transform=transform, **kwargs)
        text.draw(find_renderer(plt.gcf()))
        extent = text.get_window_extent()
        transform = transforms.offset_copy(text._transform, x=extent.width*(dpi/100)*svg_fix,
                                           units='dots')


def country_code_plot(data, data_exit=None, title='title', xlabel='xlabel', ylabel='ylabel',
                      figsize=(16, 12), first_color='#36B669', second_colour='#0B698C',
                      filter_under=1, bar_height=0.75, unit_conversion=1, xlim_max=None,
                      show_plot=True, close_plot=False, save_names=[], ytick_fontsize=12,
                      xlabel_fontsize=20, ylabel_fontsize=20, title_fontsize=30,
                      label_size=12, label_offset_y=0.1, label_gap=3, date_text_size=14,
                      label_str_conversion=lambda x: x, text_scaling=1, dpi=100, svg_fix=1):
    """
    Makes a horizontal bar chart for the data supplied, exit data is optional.

    text_scaling is needed when the exit data text is being shown, the string
    could be too long for the box so display it after the first text. If it is being displayed
    after when it should not this is too big and if the text is overlapping this is too small.
    Unfourtunatly I didn't find a way to get the real size of the text to be displayed so
    get_text_length is used. text_scaling will be different on figures with different DPI.
    """
    # Convert the data into the units you want to plot
    data = {key: value/unit_conversion for key, value in data.items()}
    if data_exit:
        data_exit = {key: value/unit_conversion for key, value in data_exit.items()}

    data_above_all = sorted(data.items(), key=lambda x: x[1], reverse=True)
    # Optionally filter the results that have less than any number
    data_above = list(filter(lambda x: x[1] >= filter_under, data_above_all))
    data_under = list(filter(lambda x: x[1] < filter_under > 0, data_above_all))

    labels_to_plot = [x[0] for x in data_above]
    values_to_plot = [x[1] for x in data_above]

    # If values are filtered out then add an other bar
    sum_other = sum([x[1] for x in data_under])
    if sum_other:
        labels_to_plot.append('other ({})'.format(len(data_under)))
        values_to_plot.append(sum_other)

    # Create figure and axis for plotting
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

    # Plot the rectangles for both all nodes and exit nodes if applicable
    bars_all = ax.barh(labels_to_plot, values_to_plot, align='center', height=bar_height,
                       color=first_color, edgecolor=first_color)

    if data_exit:
        # exit_info is a list with the values in the same order as the non-exit data
        exit_info = [data_exit.get(x[0], 0) for x in data_above]
        if sum_other:
            exit_info.append(sum(data_exit.values())-sum(exit_info))
        bars_exit = ax.barh(labels_to_plot, exit_info, align='center', height=bar_height,
                            color=second_colour, edgecolor=second_colour)
        # Add legend to the bar chart
        legend = fig.legend(handles=[bars_all, bars_exit], labels=['All relays', 'Exit relays'],
                            loc=(0.75, 0.1), fontsize=25, frameon=False)
    else:
        bars_exit = []

    # Set the ytick to grey
    ax.set_yticks(range(len(values_to_plot)))
    ax.set_yticklabels(labels_to_plot, color='grey')
    ax.invert_yaxis()

    ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)
    ax.set_xlabel(xlabel, fontsize=xlabel_fontsize)
    ax.set_title(title, fontsize=title_fontsize, y=1.01)
    # Label style
    label_style = {
        'horizontalalignment': 'left',
        'verticalalignment': 'center',
        'weight': 'bold',
        'clip_on': True,
        'fontsize': label_size
    }
    # Add labels to the bars on the bar chart, zip_longest because there might be no exit data
    for rect_all, rect_exit in itertools.zip_longest(bars_all, bars_exit):
        # Convert float to int
        width_all = rect_all.get_width()
        label_text = label_str_conversion(width_all)
        height = rect_all.get_y() + rect_all.get_height()/2 + label_offset_y
        if not data_exit:
            ax.text(width_all+label_gap, height, label_text, color='grey', **label_style)
        else:
            width_exit = rect_exit.get_width()
            exit_label_text = label_str_conversion(width_exit)

            # Get text dimensions to know when something overlaps
            text_dimension_exit = get_text_length(exit_label_text, weight='bold',
                                                  fontsize=label_size)[0]*text_scaling
            exit_color = 'white'
            if width_exit == 0:
                # Don't put a text box for  the exit
                ax.text(width_all+label_gap, height, label_text, color='grey', **label_style)
            elif width_all - width_exit < text_dimension_exit + label_gap:
                # If the text will overlap with the other bar then place the text after
                # the second bar.
                exit_label_text = f'- {exit_label_text}'
                text_multiple_colours(ax, width_all+label_gap, height,
                                      [label_text, exit_label_text], ['grey', second_colour],
                                      dpi, svg_fix, **label_style)
            else:
                ax.text(width_all+label_gap, height, label_text, color='grey', **label_style)
                ax.text(width_exit+label_gap, height, exit_label_text, color=exit_color,
                        **label_style)
    # Styling section:
    # Change legend to grey and bold if it exists
    if 'legend' in vars():
        for text in legend.get_texts():
            text.set_color('grey')
            text.set_fontweight('bold')
    # Remove axis grid
    ax.grid(False)
    ylim = ax.get_ylim()
    ax.set_ylim([ylim[0]+(1-bar_height), ylim[1]-(1-bar_height)])
    # Change splines, splines are the lines on the graph
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('grey')
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_color('grey')
    ax.spines['bottom'].set_linewidth(1.5)
    # Remove ticks
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    # Change label axis labels_to_plot and colour
    ax.xaxis.label.set_color('grey')
    ax.xaxis.label.set_weight('bold')
    ax.yaxis.label.set_color('grey')
    ax.yaxis.label.set_weight('bold')
    # Remove y ticks and increase x tick font
    ax.yaxis.set_tick_params(width=0, labelsize=ytick_fontsize)
    ax.xaxis.set_tick_params(labelsize=xlabel_fontsize)
    # ax.title.set_size(1)
    # Change title
    ax.title.set_color('grey')
    ax.title.set_weight('bold')
    # Change x tick to grey and put an x axis grid
    ax.tick_params(axis='x', colors='grey')
    ax.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.5)
    # Set figure facecolour to white
    fig.patch.set_facecolor('white')
    # Make the figure tight
    plt.autoscale(enable=True, axis='y', tight=True)
    plt.tight_layout(rect=[0.01, 0.01, 0.95, 0.99])
    if xlim_max:
        ax.set_xlim((0, xlim_max))
    ax.set_xticklabels([f'{x:,.0f}' for x in ax.get_xticks().tolist()])

    fontdict = {'fontsize': date_text_size,
                'fontweight': 'bold',
                'color': 'gray'}
    date_string = time.strftime('%Y-%m-%d')
    fig.text(0, 0.0002, f'AceLewis.com - Date: {date_string}',
             fontdict=fontdict, horizontalalignment='left')

    # Now show the plot and save it
    if show_plot:
        plt.show()
    for save_name in save_names:
        plt.show()
        # If you want to change the DPI then reduce the extent in text_multiple_colours
        # by that same percentage. SVGs have a different issue.
        plt.savefig(save_name, dpi=dpi)
    if close_plot:
        plt.close()
