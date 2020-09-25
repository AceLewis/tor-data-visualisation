import time

import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects


def custom_autopct(pct, fff):
    """How numeric values should be displayed"""
    return ('%1.1f%%' % pct) if pct > fff else ''


def donut_chart(data, plot_title, colours=None, percent_thresh=0, title_font_size=25,
                wedge_text_size=22, label_text_size=22, filter_percent=5, startangle=70,
                pctdistance=0.8, labeldistance=1.1, wedgeprops=0.4, date_text_size=10,
                show_plot=True, close_plot=False, save_names=[], dpi=100):
    """Makes a donut chart"""
    # Sort data
    data_above_all = sorted(data.items(), key=lambda x: x[1], reverse=True)
    total_sum = sum(data.values())
    # Optionally filter the results that have less than any number
    data_above = list(filter(lambda x: x[1] >= filter_percent*total_sum/100, data_above_all))
    data_under = list(filter(lambda x: x[1] < filter_percent*total_sum/100 > 0, data_above_all))

    labels = [x[0] for x in data_above]
    sizes = [x[1] for x in data_above]

    # If values are filtered out then add an "other" bar
    sum_other = sum([x[1] for x in data_under])
    if sum_other:
        labels.append('Other')
        sizes.append(sum_other)

    sizes_percent = [100*x/sum(sizes) for x in sizes]
    my_label = [[label, f'{label} ({percent:1.1f}%)'][percent < percent_thresh]
                for percent, label in zip(sizes_percent, labels)]
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, labels, wedge_texts = ax.pie(sizes, colors=colours, labels=my_label,
                                         autopct=lambda x: custom_autopct(x, percent_thresh),
                                         startangle=startangle, pctdistance=pctdistance,
                                         labeldistance=labeldistance,
                                         wedgeprops={'width': wedgeprops})

    for label in labels:
        label.set_color('gray')
        label.set_weight('bold')
        label.set_size(label_text_size)

    for wedge_text in wedge_texts:
        wedge_text.set_color('white')
        wedge_text.set_weight('bold')
        wedge_text.set_size(wedge_text_size)
        wedge_text.set_path_effects([PathEffects.withStroke(linewidth=1, foreground="gray")])

    for wedge in wedges:
        wedge.set_edgecolor(wedge.get_facecolor())

    fontdict = {'fontsize': title_font_size,
                'fontweight': 'bold',
                'color': 'gray'}
    plt.title(plot_title, fontdict=fontdict, y=1.03)
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    plt.tight_layout()

    fontdict = {'fontsize': date_text_size,
                'fontweight': 'bold',
                'color': 'gray'}
    date_string = time.strftime('%Y-%m-%d')
    fig.text(0, 0.0002, f'AceLewis.com - Date: {date_string}',
             fontdict=fontdict, horizontalalignment='left')

    if show_plot:
        plt.show()
    for save_name in save_names:
        plt.show()
        plt.savefig(save_name, dpi=dpi)
    if close_plot:
        plt.close()
