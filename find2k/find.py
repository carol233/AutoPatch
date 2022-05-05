import os
import re

APK_FOLDER1 = "/data/sdc/yanjie/APK2021"
APPPreAnalysis = "/data/sdc/yanjie/AutoPatch_count"
Android_jar = "/home/yanjie/android-sdk-linux/platforms"
SELECT_APK = "APKList_find2k.txt"
Patches = "/home/yanjie/AutoPatch/MyPatch"
Exclude_files = "/home/yanjie/AutoPatch/27000record.txt"
all_patch = []
collected_apk_list = []
all_27k = {}


def getFileList(rootDir, pickstr):
    """
    :param rootDir:  root directory of dataset
    :return: A filepath list of sample
    """
    filePath = []
    for parent, dirnames, filenames in os.walk(rootDir):
        for filename in filenames:
            if filename.endswith(pickstr):
                file = os.path.join(parent, filename)
                filePath.append(file)
    return filePath


def solveFile(file):
    sha256 = os.path.split(file)[-1][:-4]
    with open(file, "r") as fr:
        s = fr.read()
        for OldAPI in all_patch:
            if "NoProtection," + OldAPI in s:
                collected_apk_list.append(sha256)
                break


if __name__ == '__main__':
    files = getFileList(Patches, ".patch")
    for patch in files:
        with open(patch, "r") as fr:
            firstline = fr.read().split("\n")[0].strip()
            pattern = re.compile(r'[\S\s]+(<\S+:\s\S+\s\S+\(.*\)>)')
            m = pattern.match(firstline)
            if m:
                oldAPI = m.group(1)
                all_patch.append(oldAPI)
    print(len(all_patch))

    with open(Exclude_files, "r") as fr:
        lines = fr.read().split("\n")
        for line in lines:
            sha256 = line.replace("[+] PreSolving ", "").strip()
            if sha256:
                all_27k[sha256] = 1

    all_files = getFileList(APPPreAnalysis, ".csv")
    for file in all_files:
        sha256 = os.path.split(file)[-1][:-4]
        if sha256 not in all_27k:
            solveFile(file)

    with open(SELECT_APK, "w") as fw:
        for line in collected_apk_list:
            fw.write(line)
            fw.write("\n")




