import argparse
import glob
import sys
import xml.etree.cElementTree as etree
from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from typing import Any, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DF_COLS_DICT = ["lat", "lon", "ele", "dist"]
MIN_FILES = 4
R = 6373.0


def strip_namespaces(tag_elem: str) -> str:
    """ Strip all namespaces from the gpx """
    idx = tag_elem.rfind("}")
    if idx != -1:
        tag_elem = tag_elem[idx + 1 :]
    return tag_elem


def get_filenames(args: argparse.Namespace) -> Tuple[List[str], int]:
    """ Collect filenames glob """
    print(type(args))
    filenames = glob.glob(args.dir)
    file_num = len(filenames)
    return filenames, file_num


def parse_gpx(xml_file: str, df_cols: list) -> pd.DataFrame:
    """ Parse gpx files into dataframe """
    trkpt_count = -1
    rows: "List[Any]" = []
    trkpt_lst: "List[float]" = []
    prev_trkpt_lst: "List[float]" = [0, 0, 0]
    got_coords = False
    total_distance: float = 0
    distance_delta: float = 0

    for event, elem in etree.iterparse(xml_file, events=("start", "end")):
        tag_names = strip_namespaces(elem.tag)  # strips all namespaces from input file
        if event == "start":
            if tag_names == "wpt":
                pass
            elif tag_names == "trkpt":
                trkpt_lst = []  # clear trkpt_lst at the start of the next loop
                trkpt_lst.append(float(elem.attrib[df_cols[1]]))
                trkpt_lst.append(float(elem.attrib[df_cols[0]]))
                trkpt_count += 1
                got_coords = True
            elif (tag_names == "ele") and got_coords is True:
                if elem.text is not None:
                    trkpt_lst.append((float(elem.text)))  # ele
                    if prev_trkpt_lst[0] == 0:
                        trkpt_lst.append(0)
                    else:
                        dlon = radians(trkpt_lst[0]) - radians(prev_trkpt_lst[0])
                        dlat = radians(trkpt_lst[1]) - radians(prev_trkpt_lst[1])

                        a = (
                            sin(dlat / 2) ** 2
                            + cos(radians(prev_trkpt_lst[1]))
                            * cos(radians(trkpt_lst[1]))
                            * sin(dlon / 2) ** 2
                        )
                        c = 2 * atan2(np.sqrt(a), sqrt(1 - a))

                        distance_delta = R * c * 1000

                        total_distance = round(total_distance + distance_delta, 2)
                        trkpt_lst.append(total_distance)
                    prev_trkpt_lst = trkpt_lst[:]
                    rows.append(
                        {df_cols[i]: trkpt_lst[i] for i, _ in enumerate(df_cols)}
                    )
    gpx_dataframe = pd.DataFrame(rows, columns=df_cols)
    print(round(gpx_dataframe["dist"].iloc[-1] / 1000, 2), "km")
    return gpx_dataframe


def create_outer_dataframe(filenames: "List[str]") -> List:
    """ Fill dataframe with parsed data """
    if len(filenames) <= MIN_FILES:
        print(f"None or too few gpx files found. You need at least 5 files")
        sys.exit(1)
    else:
        print(f"{len(filenames)} file(s) found. Parsing GPX files...")
        parsed_dataframe = [
            parse_gpx(filenames[index], DF_COLS_DICT) for index in range(len(filenames))
        ]
    return parsed_dataframe


def create_grid(file_num: int) -> Tuple[int, int, List[Tuple[int, int]]]:
    """ Create the grid for the small multiples to be arranged """
    rows_count = int(np.sqrt(file_num))
    cols_count = int(file_num / rows_count) + 1
    print(f"Grid layout: ({ rows_count }, { cols_count }) ")

    grid_layout = [divmod(x, rows_count) for x in range(file_num)]
    print("Creating plot(s)...")
    return cols_count, rows_count, grid_layout


def plot_graph(
    cols_count: int,
    rows_count: Any,
    file_num: int,
    grid_layout: List[Any],
    parsed_dataframe: List[Any],
    mode: Tuple[str, str],
):
    """ Plot grid without decorations """
    fig, ax = plt.subplots(cols_count, rows_count)
    for ax_i in np.ravel(ax):
        ax_i.axis("off")
    for i in range(file_num):
        ax[grid_layout[i]].plot(
            parsed_dataframe[i][mode[0]], parsed_dataframe[i][mode[1]]
        )


def main():
    """ Print small multiples from gpx files """
    start_time = datetime.now()

    if sys.version_info <= (3, 6, 0):
        print("This script needs Python >3.6")
        sys.exit(1)

    args_parser = argparse.ArgumentParser()
    args_parser.add_argument(
        dest="dir",
        metavar="gpx_directory",
        type=str,
        help="A directory containing at least {MIN_FILES} gpx files",
    )
    args_parser.add_argument(
        "-e", "--elevation", help="Plot the elevation graphs", action="store_true"
    )
    args_parser.add_argument(
        "-t", "--tracks", help="Plot the track outlines", action="store_true"
    )
    args = args_parser.parse_args()

    filenames, file_num = get_filenames(args)
    parsed_dataframe = create_outer_dataframe(filenames)
    cols_count, rows_count, grid_layout = create_grid(file_num)
    if args.elevation:
        mode = ("dist", "ele")
        plot_graph(
            cols_count, rows_count, file_num, grid_layout, parsed_dataframe, mode
        )
    if args.tracks:
        mode = ("lat", "lon")
        plot_graph(
            cols_count, rows_count, file_num, grid_layout, parsed_dataframe, mode
        )
    end_time = datetime.now()
    print(f"Total time: {str(end_time - start_time).split('.')[0]}")

    plt.show()


if __name__ == "__main__":
    main()
