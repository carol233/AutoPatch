import csv
import scipy.stats as stats
import matplotlib
import pandas as pd
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import numpy as np
import pylab as pl

INPUT_CSV = "/data/sdc/yanjie/AutoPatch_evaluation_1k"


def getFileList(rootDir, pick_str):
    """
    :param rootDir:  root directory of dataset
    :return: A filepath list of sample
    """
    filePath = []
    for parent, dirnames, filenames in os.walk(rootDir):
        for filename in filenames:
            if filename.endswith(pick_str):
                file = os.path.join(parent, filename)
                filePath.append(file)
    return filePath


def draw_boxplot(labels, boxes, filename, xlabel, ylabel, fontsize, boo, x, y, z, du):
    plt.figure(figsize=(x, y))  # 设置画布的尺寸
    # vert=False:水平箱线图；showmeans=True：显示均值
    plt.boxplot(boxes, labels=labels, vert=boo, showmeans=True, showfliers=False)
    pl.xticks(rotation=du)
    plt.xticks(fontsize=z)
    plt.yticks(fontsize=z)
    plt.xlabel(xlabel, fontsize=fontsize)
    plt.ylabel(ylabel, fontsize=fontsize)
    # plt.gca().xaxis.set_major_formatter(FuncFormatter(to_percent))
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def analysis(file):
    patches = []
    android_locations = []
    other_locations = []
    all_locations = []
    android_succ = []
    other_succ = []
    all_succ = []
    android_pot = []
    other_pot = []
    all_pot = []
    size = 0
    time = 0

    with open(file, "r") as fr:
        reader = csv.reader(fr)
        for line in reader:
            # count patch num_line


            keyword = line[0]
            API = line[1].strip("\"")
            issuetype = line[2]
            method = line[3].strip("\"")
            patch_name = line[6]

            if keyword == "TimeRecord":
                time = int(line[4])
                size = int(line[5])

            if patch_name not in patches:
                patches.append(patch_name)

            if keyword == "Localization":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_locations.append(line)
                else:
                    other_locations.append(line)
                all_locations.append(line)

            if keyword == "Success":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_succ.append(line)
                else:
                    other_succ.append(line)
                all_succ.append(line)

            if keyword == "Potential":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_pot.append(line)
                else:
                    other_pot.append(line)
                all_pot.append(line)

        return patches, android_locations,other_locations,all_locations, \
               android_succ,other_succ,all_succ,android_pot,other_pot,all_pot, time*0.001,size*0.000001


if __name__ == '__main__':
    # # count the num of the patchlist
    files = getFileList(INPUT_CSV, ".csv")
    all_length = 0
    all_size = 0
    num = 0
    labels_num = ["1-2", "3-4", "5-6", "7-8", "9-10", "11-12", "13-14", "15-16", "17-18",
                  "19-20", "21+"]
    labels_size = ["0-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40", "41-45",
                   "46-50", "51+"]

    box_num = []
    box_size = []

    xxxx = []
    x1 = [] # num
    x2 = [] # size
    y = [] # time

    for i in range(len(labels_num)):
        box_num.append([])
    for i in range(len(labels_size)):
        box_size.append([])

    for file in files:
        patches, android_locations, other_locations, all_locations, \
        android_succ, other_succ, all_succ, android_pot, other_pot, all_pot, time, size = analysis(file)
        issue_num = len(all_locations)

        if issue_num > 0 and size > 0 and time > 0:
            x1.append(len(all_locations))
            x2.append(size)
            y.append(time)

            a = int(size / 5)
            if a < len(labels_size):
                box_size[a].append(time)
            else:
                box_size[-1].append(time)

            if issue_num >= 21:
                box_num[-1].append(time)
            else:
                b = int(issue_num + 1 / 2) - 1

                if b < len(labels_num):
                    box_num[b].append(time)


    # draw_boxplot(labels_num, box_num, "boxplot_patch_time.pdf", "# Located Issues (per app)", "Time(s)", 20, True, 6, 5, 17, 45)
    # draw_boxplot(labels_size, box_size, "boxplot_size_time.pdf", "The size of the DEX file (MB)", "Time(s)", 20, True, 6, 5, 17, 45)
    #
    # print("num_time:", stats.pearsonr(x1, y))
    # print("size_time:", stats.pearsonr(x2, y))

    x0 = []
    y0 = []
    box_succ = []

    labels_num2 = ["Located Issues", "Fixed Issues"]

    for i in range(len(labels_num2)):
        box_succ.append([])

    for file in files:
        patches, android_locations, other_locations, all_locations, \
        android_succ, other_succ, all_succ, android_pot, other_pot, all_pot, time, size = analysis(file)
        if len(all_locations) > 0:
            a = len(all_locations)
            b = len(all_succ)
            x0.append(len(all_locations))  # heng
            y0.append(len(all_succ))  # zong

            box_succ[0].append(a)
            box_succ[1].append(b)

    draw_boxplot(labels_num2, box_succ, "boxplot_succ.pdf", "", "", 15, False, 8, 3, 14, 0)
    print(np.mean(box_succ[0]), np.median(box_succ[0]))
    print(np.mean(box_succ[1]), np.median(box_succ[1]))








