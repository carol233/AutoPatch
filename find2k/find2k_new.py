import os
import re
import csv
CSVfiles = "/data/sdc/yanjie/APIRecommendation/Presolved_filtered"
APKPath = "/data/sdc/yanjie/APK2020"
SELECT_APK = "Sha256_find2k_2020.txt"
Patches = "/home/yanjie/AutoPatch/MyPatch"
Exclude_files = "/home/yanjie/AutoPatch/27000record.txt"
all_patch = []
all_27k = {}
select_apks = []

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

def solve(file):
    with open(file, 'r') as fr:
        s = fr.read()
        for OldAPI in all_patch:
            if OldAPI in s:
                sha256 = os.path.split(file)[-1][:-4]
                select_apks.append(sha256)
                break

if __name__ == "__main__":
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

    collect_file_paths = []
    csv1 = getFileList(CSVfiles, ".csv")
    for file in csv1:
        sha256 = os.path.split(file)[-1][:-4]
        checkpath = os.path.join(APKPath, sha256 + ".apk")
        if os.path.exists(checkpath) and sha256 not in all_27k:
            collect_file_paths.append(file)

    print(len(collect_file_paths))

    for file in collect_file_paths:
        solve(file)

    with open(SELECT_APK, "w") as fw:
        for line in list(set(select_apks)):
            fw.write(line)
            fw.write("\n")



