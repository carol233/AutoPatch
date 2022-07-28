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

INPUT_CSV = "AutoPatch_evaluation_1k"
INPUT_CSV2 = "runningLog"


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
                    android_locations.append(str(line[:-1]))
                else:
                    other_locations.append(str(line[:-1]))
                all_locations.append(str(line[:-1]))

            if keyword == "Success":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_succ.append(str(line[:-1]))
                else:
                    other_succ.append(str(line[:-1]))
                all_succ.append(str(line[:-1]))

            if keyword == "Potential":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_pot.append(str(line[:-1]))
                else:
                    other_pot.append(str(line[:-1]))
                all_pot.append(str(line[:-1]))

        return patches, android_locations,other_locations,all_locations, \
               android_succ,other_succ,all_succ,android_pot,other_pot,all_pot,time*0.001,size*0.000001


if __name__ == '__main__':
    num_Potential = 0
    num_Located = 0
    num_Success = 0

    box_succ = []

    labels_num2 = ["Located Issues", "Fixed Issues"]

    for i in range(len(labels_num2)):
        box_succ.append([])

    files1 = getFileList(INPUT_CSV, ".csv")
    files2 = getFileList(INPUT_CSV2, ".csv")

    for file2 in files2:
        sha256 = os.path.split(file2)[-1][:-4]
        patches, android_locations, other_locations, all_locations, \
        android_succ, other_succ, all_succ, android_pot, other_pot, all_pot, time, size = analysis(file2)

        for file1 in files1:
            sha256_1 = os.path.split(file1)[-1][:-4]
            if sha256 == sha256_1:
                patches1, android_locations1, other_locations1, all_locations1, \
                android_succ1, other_succ1, all_succ1, android_pot1, other_pot1, all_pot1, time1, size1 = analysis(file1)

                all_locations.extend(all_locations1)
                all_succ.extend(all_succ1)
                all_pot.extend(all_pot1)

                break


        all_locations = list(set(all_locations))
        all_succ = list(set(all_succ))
        all_pot = list(set(all_pot))

        num_Potential += len(all_pot)
        num_Located += len(all_locations)
        num_Success += len(all_succ)

        if len(all_locations) > 0:
            a = len(all_locations)
            b = len(all_succ)

            box_succ[0].append(a)
            box_succ[1].append(b)

    draw_boxplot(labels_num2, box_succ, "boxplot_succ333.pdf", "", "", 15, False, 8, 3, 14, 0)
    print(np.mean(box_succ[0]), np.median(box_succ[0]))
    print(np.mean(box_succ[1]), np.median(box_succ[1]))
    print(len(box_succ[0]))
    print(num_Potential)
    print(num_Located)
    print(num_Success)








