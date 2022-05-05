import csv
import scipy.stats as stats
import matplotlib
import pandas as pd
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

INPUT_CSV = "/data/sdc/yanjie/find2k_evaluation_1k_4"


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


def analysis(file, issuetype111):

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

    with open(file, "r") as fr:
        reader = csv.reader(fr)
        for line in reader:
            # count patch num_line

            keyword = line[0]
            API = line[1].strip("\"")
            issuetype = line[2]
            method = line[3].strip("\"")
            time = line[4]
            size = line[5]
            patch_name = line[6]

            if issuetype != issuetype111:
                continue

            if patch_name not in patches:
                patches.append(patch_name)

            if keyword == "Localization":
                if method.lower().startswith("<android.") or \
                        method.lower().startswith("<androidx.") or \
                        method.lower().startswith("<com.google.android"):
                    android_locations.append(line)
                else:
                    # if issuetype == "OS" and patch_name == "OSPatches/2_setAudioStreamType.patch":
                    #     print(line)
                    other_locations.append(line)
                all_locations.append(line)

            if keyword == "Success" or "Success" in keyword:
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

        return patches, android_locations, other_locations,all_locations,\
               android_succ, other_succ, all_succ,android_pot, other_pot,all_pot


def m(f):
    files = getFileList(INPUT_CSV, ".csv")

    patch_app = {}
    patch_loc = {}
    patch_pot = {}
    patch_suc = {}

    for file in files:

        patches, android_locations, other_locations, all_locations, \
        android_succ, other_succ, all_succ, android_pot, other_pot, all_pot = analysis(file, f)

        for patch in patches:
            if patch not in patch_app:
                patch_app[patch] = []
            if patch not in patch_loc:
                patch_loc[patch] = 0
            if patch not in patch_pot:
                patch_pot[patch] = 0
            if patch not in patch_suc:
                patch_suc[patch] = 0
            if file not in patch_app[patch]:
                patch_app[patch].append(file)

        for line in other_locations:
            patch_name = line[6]
            patch_loc[patch_name] += 1

        for line in other_succ:
            patch_name = line[6]
            patch_suc[patch_name] += 1

        for line in other_pot:
            patch_name = line[6]
            patch_pot[patch_name] += 1

    map_elememt_to_num_sort = sorted(patch_suc.items(), key=lambda d: d[1], reverse=True)
    for item in map_elememt_to_num_sort[:10]:
        patch = item[0]
        print(patch, len(patch_app[patch]), patch_pot[patch], patch_loc[patch], item[1])

    pot_all = 0
    loc_all = 0
    suc_all = 0
    all_apk_od_onepatch = []

    print("----------------------------------------------------------------")
    for patch in patch_loc:
        print(patch, patch_pot[patch], patch_loc[patch], patch_suc[patch])
        pot_all += patch_pot[patch]
        loc_all += patch_loc[patch]
        suc_all += patch_suc[patch]
        all_apk_od_onepatch.extend(patch_app[patch])


    # OSPatches/2_setAudioStreamType.patch 184 178 0
    # remove the 2_setAudioStreamType
    if f == "OS":
        pot_all += 184
        loc_all += 178
    print("all: ", len(list(set(all_apk_od_onepatch))), pot_all, loc_all, suc_all)
    return all_apk_od_onepatch


if __name__ == '__main__':

    apk1 = m("OS")
    print("################################################################")
    apk2 = m("DEVICE")
    print("################################################################")
    apk3 = m("CALLBACK")
    print("################################################################")

    apkall = []
    apkall.extend(apk1)
    apkall.extend(apk2)
    apkall.extend(apk3)

    newlist = list(set(apkall))
    print("all apks: ", len(newlist))

