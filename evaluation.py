from helper import *
import Levenshtein
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

Mypatch = "/home/yanjie/AutoPatch/MyPatch/"
GeneratePatch = "/data/sdc/yanjie/AutoPatch_generatePatch2"


def LevenshteinRatio(a, b):
    if not a or not b:
        return 0
    return Levenshtein.ratio(a, b)

def draw_api_num(box, savefile):

    labels = ["Levenshtein Ratio"]
    print(len(box))
    plt.figure(figsize=(8, 1))  # 设置画布的尺寸
    # vert=False:水平箱线图；showmeans=True：显示均值
    plt.boxplot([box], labels=labels, vert=False, showmeans=True, showfliers=False)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    # plt.xlim((10, 11))

    plt.tight_layout()
    plt.savefig(savefile)
    plt.close()

def draw_api_num2(box, box2, savefile):
    labels = ["AutoPatch", "Transformer"]
    print(len(box))
    plt.figure(figsize=(8, 4))  # 设置画布的尺寸
    # vert=False:水平箱线图；showmeans=True：显示均值
    if len(box) > len(box2):
        box = box[:len(box2)]
    else:
        box2 = box2[:len(box)]
    plt.boxplot([box, box2], labels=labels, vert=False, showmeans=True, showfliers=False)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    # plt.xlim((10, 11))

    plt.tight_layout()
    plt.savefig(savefile)
    plt.close()

def clean(s):
    pattern = re.compile(r'[\d\s|@]+')
    s = re.sub(pattern, "", s, 0)
    return s

def evaluate_patches(file1, file2):
    with open(file1, 'r') as fr1:
        p1 = fr1.read()
    with open(file2, 'r') as fr2:
        p2 = fr2.read()
    p1 = clean(p1)
    p2 = clean(p2)
    return LevenshteinRatio(p1, p2)

def evaluate_DL(file1, file2):
    all_ld = []
    count_match = 0
    count_error = 0
    with open(file1, 'r') as fr1:
        lines1 = fr1.read().split("\n")
    with open(file2, 'r') as fr2:
        lines2 = fr2.read().split("\n")

    for i in range(len(lines1)):
        p1 = clean(lines1[i])
        p2 = clean(lines2[i])
        s = LevenshteinRatio(p1, p2)
        all_ld.append(s)
        if s > 0.8:
            count_match += 1
        else:
            count_error += 1
    return all_ld, count_match, count_error


def solve_autopatch(file1, all_prefix):
    results = []
    PairPath = "AutoPatch_Pairs.txt"
    API_Old_dic, API_new_dic = loadPair(PairPath)
    PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch2"
    all_patches_dic = {}
    all_patches = getFileList(PatchOutputPath, ".patch")
    for item in all_patches:
        num1 = os.path.split(item)[-1].split("_")[0]
        if num1 in all_patches_dic:
            all_patches_dic[num1].append(item)
        else:
            all_patches_dic[num1] = [item]

    all = {}
    with open(file1, 'r') as fr1:
        lines1 = fr1.read().split("\n")
    for line in lines1:
        if not line:
            continue
        old_api = line.split("|/|")[0]
        if old_api in all:
            all[old_api] += 1
        else:
            all[old_api] = 1

    for old_api in all:
        length = all[old_api]
        num = str(API_Old_dic[old_api])
        if num not in all_patches_dic:
            print(num)
            continue
        autopatches = all_patches_dic[num][:length]
        humanpatch = all_prefix[num]
        for item in autopatches:
            ld = evaluate_patches(humanpatch, item)
            results.append(ld)

    return results

if __name__ == '__main__':
    Evaluate = 0
    if Evaluate == 0:
        all_ld, count_match, count_error = evaluate_DL("yanjie/prediction_beam_1.txt", "yanjie/after.txt")
        print(count_match, count_error)

        myfiles = getFileList(Mypatch, ".patch")
        all_prefix = {}
        for file in myfiles:
            prefix = os.path.split(file)[-1].split("_")[0]
            all_prefix[prefix] = file

        all_ld2 = solve_autopatch("yanjie/before.txt", all_prefix)

        draw_api_num2(all_ld2, all_ld, "boxplot_transformer_ld.pdf")
        print("auto mean: ", np.mean(all_ld2))
        print("auto median: ", np.median(all_ld2))
        print("mean: ", np.mean(all_ld))
        print("median: ", np.median(all_ld))

    else:
        myfiles = getFileList(Mypatch, ".patch")
        allfiles = getFileList(GeneratePatch, ".patch")
        all_prefix = {}
        for file in myfiles:
            prefix = os.path.split(file)[-1].split("_")[0]
            all_prefix[prefix] = file

        all_ds = []
        count_0 = 0
        for file2 in allfiles:
            prefix = os.path.split(file2)[-1].split("_")[0]
            if prefix in all_prefix:
                correct = all_prefix[prefix]
                ds = evaluate_patches(correct, file2)
                all_ds.append(ds)
                if ds == 1:
                    count_0 += 1


        print(len(all_ds))
        print("correct patches: ", count_0)
        draw_api_num(all_ds, "boxplot_all_ld.pdf")
        print("mean: ", np.mean(all_ds))
        print("median: ", np.median(all_ds))
        counts = np.bincount(all_ds)
        print("mode: ", np.argmax(counts))






