import glob
import sys
import xml.etree.ElementTree as etree
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

DF_COLS_DICT = ["lat", "lon"]
MIN_FILES = 4


def strip_namespaces(tag_elem: Any) -> Any:
    """ Strip all namespaces from the gpx """
    idx = tag_elem.rfind("}")
    if idx != -1:
        tag_elem = tag_elem[idx + 1 :]
    return tag_elem


def parse_xml(xml_file: str, df_cols: list) -> pd.DataFrame:
    """ Parse raw gpx into a dataframe """
    rows = []
    for event, elem in etree.iterparse(xml_file, events=("start", "end")):
        tag_names = strip_namespaces(elem.tag)
        if event == "start":
            if tag_names == "trkpt":
                res = []
                res.append(elem.attrib[df_cols[0]])
                res.append(elem.attrib[df_cols[1]])
                rows.append({df_cols[i]: float(res[i]) for i, _ in enumerate(df_cols)})

    gpx_df = pd.DataFrame(rows, columns=df_cols)
    return gpx_df


def main():
    """ Print small multiples from gpx files """
    if sys.version_info <= (3, 6, 0):
        print("Needs Python >3.6")
        sys.exit(1)

    if len(sys.argv) != 2:
        print(
            "Usage: small_multiples.py [path] \n"
            "Example: python small_multiples.py d:\\activities\\*.gpx"
        )
        sys.exit(1)
    else:
        filenames = glob.glob(sys.argv[1])
        if len(filenames) <= MIN_FILES:
            print(f"You need at least {MIN_FILES} files")
            sys.exit(1)
        else:
            file_num = len(filenames)
            start_time = datetime.now()
            print("-" * 100)
            print(f"File(s) found: {file_num}")
            df_list = [
                parse_xml(filenames[index], DF_COLS_DICT) for index in range(file_num)
            ]
            rows_count = int(pd.np.sqrt(file_num))
            cols_count = int(file_num / rows_count) + 1
            print(f"Grid Layout: ({ rows_count }, { cols_count }) ")
            grid_layout = [divmod(x, rows_count) for x in range(file_num)]
            fig, ax = plt.subplots(cols_count, rows_count)
            for ax_i in pd.np.ravel(ax):
                ax_i.axis("off")
            for i in range(file_num):
                ax[grid_layout[i]].plot(df_list[i]["lon"], df_list[i]["lat"])

    end_time = datetime.now()
    print(f"Total time: [{str(end_time - start_time).split('.')[0]}]")
    plt.show()


if __name__ == "__main__":
    main()
