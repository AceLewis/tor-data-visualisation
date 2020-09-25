import requests
import pandas as pd

import matplotlib
import pycountry

from donut_chart import donut_chart
from country_code_bar_chart import country_code_plot


def download_file(url, local_filename):
    """Download a file to the local_filename"""
    request = requests.get(url)
    with open(local_filename, 'wb') as file:
        for chunk in request.iter_content(chunk_size=1024):
            if chunk:  # Filter out keep-alive new chunks
                file.write(chunk)


def get_version(row_number, sheet):
    """Get first three numbers from tor version"""
    return '.'.join(sheet.iloc[row_number]['Platform'].split(' ')[1].split('.')[:3])


def get_name(country_code):
    """Get the country name"""
    redefine_country_dict = {
        'A1': 'Anonymous',
        'EU': 'Europe',
        'RU': 'Russia',
        'MD': 'Moldova',
        'KR': 'South Korea',
        'IR': 'Iran',
        'GB': 'U.K.',
        'US': 'U.S.',
        }
    if country_code in redefine_country_dict.keys():
        return redefine_country_dict.get(country_code)
    elif isinstance(country_code, str):
        return pycountry.countries.get(alpha_2=country_code).name
    else:
        return country_code


def main():
    """The main function, get the data, do some processing then plot it"""
    # There are multiple sites that track tor nodes where you can download Tor_query_EXPORT.csv
    tor_status_url = r'https://torstatus.rueckgr.at/query_export.php/Tor_query_EXPORT.csv'
    file_name = 'tor_export.csv'
    # You should comment out the downloading of the file if you are making lots of small changes
    download_file(tor_status_url, file_name)

    # Proccessing the data section
    df = pd.read_csv(file_name)

    for country_code in df['Country Code'].unique():
        df['Country Code'].mask(df['Country Code'] == country_code, get_name(country_code),
                                inplace=True)

    # Group by country then find out the bandwidth and number of nodes per country
    grouped_by_country = df.groupby('Country Code')['Bandwidth (KB/s)']
    count_per_country = grouped_by_country.agg('count').to_dict()
    bandwidth_per_country = grouped_by_country.sum().to_dict()
    # Same but just for exit nodes
    exit_only = df[(df["Flag - Exit"] == 1)]
    grouped_by_country_exit = exit_only.groupby('Country Code')['Bandwidth (KB/s)']
    count_per_country_exit = grouped_by_country_exit.agg('count').to_dict()
    bandwidth_per_country_exit = grouped_by_country_exit.sum().to_dict()
    # Get the Platform OS for each relay
    platform_labels = ['Linux', 'BSD', 'Other']
    linux_relays = df[df['Platform'].str.contains('(Linux|GNU)')]
    bsd_relays = df[df['Platform'].str.contains('BSD')]
    other_relays = df[~df['Platform'].str.contains('(Linux|GNU|BSD)')]
    # Get total bandwidth per platform
    linux_relay_bandwidth = linux_relays['Bandwidth (KB/s)'].sum()
    bsd_relay_bandwidth = bsd_relays['Bandwidth (KB/s)'].sum()
    other_relay_bandwidth = other_relays['Bandwidth (KB/s)'].sum()
    # Convert this data to dictionaries
    relay_numbers = list(map(len, [linux_relays, bsd_relays, other_relays]))
    relay_bandwidth = [linux_relay_bandwidth, bsd_relay_bandwidth, other_relay_bandwidth]
    relay_number_dict = dict(zip(platform_labels, relay_numbers))
    relay_bandwidth_dict = dict(zip(platform_labels, relay_bandwidth))
    # Do the same for the version numbers, versions are four numbers e.g 0.4.3.5 but I will just
    # use the first 3 to group them together more.
    version_count = df.groupby(by=lambda x:
                               get_version(x, df))['Bandwidth (KB/s)'].agg('count').to_dict()
    version_bandwidth = df.groupby(by=lambda x:
                                   get_version(x, df))['Bandwidth (KB/s)'].sum().to_dict()

    # Section for plotting the data

    # Donut chart section
    png_dpi = 300
    # I found the tab20 colour tange the best but it is not perfect.
    colours = matplotlib.cm.get_cmap('tab20')(range(20))

    plot_title = "Total Number of Relays by Platform"
    donut_chart(relay_number_dict, plot_title, colours=colours, percent_thresh=3,
                dpi=png_dpi, close_plot=True,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    plot_title = "Total Bandwidth of Relays by Platform"
    donut_chart(relay_bandwidth_dict, plot_title, colours=colours, percent_thresh=3,
                dpi=png_dpi, title_font_size=23, close_plot=True,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    plot_title = "Total Number of Relays by Version"
    donut_chart(version_count, plot_title, colours=colours, percent_thresh=2,
                filter_percent=3, dpi=png_dpi, close_plot=True, startangle=0,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    plot_title = "Total Bandwidth of Relays by Version"
    donut_chart(version_bandwidth, plot_title, colours=colours, percent_thresh=2,
                filter_percent=3, dpi=png_dpi, close_plot=True, startangle=0,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    plot_title = "Total Number of Relays per Country"
    donut_chart(count_per_country, plot_title, colours=colours,
                percent_thresh=1, filter_percent=1.35, wedge_text_size=15, startangle=90,
                pctdistance=0.85, wedgeprops=0.3, title_font_size=22, label_text_size=15,
                dpi=png_dpi, close_plot=True, labeldistance=1.05,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    plot_title = "Total Bandwidth per Country"
    donut_chart(bandwidth_per_country, plot_title, colours=colours,
                percent_thresh=1.2, filter_percent=1.25, wedge_text_size=15, startangle=50,
                pctdistance=0.85, wedgeprops=0.3, dpi=png_dpi, close_plot=True,
                label_text_size=15, labeldistance=1.05,
                save_names=[f'./images/{plot_title}.png', f'./images/{plot_title}.svg'])

    # Bar chart section
    png_dpi = 300
    svg_fix = 0.73
    title = "Bandwidth of Tor Relays in Each Country"
    title_exit = "Bandwidth of Tor Exit Relays in Each Country"
    filter_under = 1000
    filter_under_exit = 800
    file_name = f'./images/{title}'
    xlim = 175_000
    xlim_exit = 62_000

    plot_kwargs = dict(
        label_str_conversion=lambda x: f'{x:,.0f} Mbps', ytick_fontsize=15, text_scaling=180,
        label_gap=500, xlabel='Bandwidth in Mbps', ylabel=None,
        label_size=12, unit_conversion=1000/8, close_plot=True
        )

    country_code_plot(bandwidth_per_country,
                      data_exit=bandwidth_per_country_exit,
                      title=title, filter_under=filter_under, xlim_max=xlim,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name}.png'])

    country_code_plot(bandwidth_per_country,
                      title=title, filter_under=filter_under, xlim_max=xlim,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name} No Exit.png'])

    country_code_plot(bandwidth_per_country_exit,
                      title=title_exit, filter_under=filter_under_exit, xlim_max=xlim_exit,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name} Only Exit.png'])

    # There is a weird issue where the figure is saved differently if it is a PNG or a SVG when
    # the DPI is not 100 (the default). So I have to replot to save both the SVG and PNG.
    # For SVG the DPI obviously does not matter.
    country_code_plot(bandwidth_per_country,
                      data_exit=bandwidth_per_country_exit,
                      title=title, filter_under=filter_under, xlim_max=xlim,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name}.svg'])

    country_code_plot(bandwidth_per_country,
                      title=title, filter_under=filter_under, xlim_max=xlim,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name} No Exit.svg'])

    country_code_plot(bandwidth_per_country_exit,
                      title=title_exit, filter_under=filter_under_exit, xlim_max=xlim_exit,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name} Only Exit.svg'])

    title = "Number of Tor Relays in Each Country"
    title_exit = "Number of Tor Exit Relays in Each Country"
    filter_under = 20
    filter_under_exit = 7
    xlim = 1500
    xlim_exit = 400
    label_gap = 5
    label_gap_exit = 2
    file_name = f'./images/{title}'

    plot_kwargs = dict(
        label_str_conversion=lambda x: f'{x:,.0f}', ytick_fontsize=15, text_scaling=1.5,
        xlabel='Number of Nodes', ylabel=None, label_size=12, close_plot=True
        )

    country_code_plot(count_per_country,
                      data_exit=count_per_country_exit,
                      title=title, filter_under=filter_under, xlim_max=xlim, label_gap=label_gap,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name}.png'])

    country_code_plot(count_per_country,
                      title=title, filter_under=filter_under, xlim_max=xlim, label_gap=label_gap,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name} No Exit.png'])

    country_code_plot(count_per_country_exit,
                      title=title_exit, filter_under=filter_under_exit,
                      xlim_max=xlim_exit, label_gap=label_gap_exit,
                      **plot_kwargs, dpi=png_dpi, save_names=[f'{file_name} Only Exit.png'])

    country_code_plot(count_per_country,
                      data_exit=count_per_country_exit,
                      title=title, filter_under=filter_under, xlim_max=xlim, label_gap=label_gap,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name}.svg'])

    country_code_plot(count_per_country,
                      title=title, filter_under=filter_under, xlim_max=xlim, label_gap=label_gap,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name} No Exit.svg'])

    country_code_plot(count_per_country_exit,
                      title=title_exit, filter_under=filter_under_exit,
                      xlim_max=xlim_exit, label_gap=label_gap_exit,
                      **plot_kwargs, svg_fix=svg_fix, save_names=[f'{file_name} Only Exit.svg'])


if __name__ == '__main__':
    main()
