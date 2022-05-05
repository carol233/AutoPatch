import os
import random
import shlex
import csv
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

JAR_PATH = "RepairDroid.jar"
# APK_FOLDER = "/data/sdc/yanjie/APPForRepairDroid"
APK_FOLDER = "/data/sdc/yanjie/APK2021"
patch_os = "OSPatches"
patch_device = "DevicePatches"
patch_callback = "CallBackPatches"

Exclude_files = "/home/yanjie/AutoPatch/27000record.txt"

Android_jar = "/home/yanjie/android-sdk-linux/platforms"
RECORD_TXT = "record_run1k_2.txt"
SAVEResults_DIR = "/data/sdc/yanjie/AutoPatch_evaluation_1k_2"
SELECT_APK = "APKList_find2k.txt"

all_solved = {}
all_APK = []
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


class Analysis:

    def __init__(self):
        self.max_jobs = 15
        self.lock = threading.Lock()
        self.map_api2patch = {}

    def run(self, cmd, timeout_sec):
        proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
        timer = Timer(timeout_sec, proc.kill)
        try:
            timer.start()
            # stdout, stderr = proc.communicate()
            print(proc.stdout.readlines())
        finally:
            timer.cancel()

    def process_one(self, args):
        apk_path = args
        sha256 = os.path.split(apk_path)[-1][:-4]
        if sha256 in all_solved:
            return
        output_file = os.path.join(SAVEResults_DIR, sha256 + ".csv")
        if os.path.exists(output_file):
            return

        try:
            self.lock.acquire()
            with open(RECORD_TXT, "a+") as fw:
                fw.write(sha256)
                fw.write("\n")
            self.lock.release()

            print("[+] PreSolving " + sha256)
            CMD = "java -Xms2048m -Xmx4096m -XX:MaxNewSize=4096m " \
                  "-jar " + JAR_PATH + " " + patch_os + " " + patch_device + " " + patch_callback + " " \
                  + Android_jar + " " + apk_path + " " + output_file
            print(CMD)
            self.run(CMD, 300)

        except Exception as e:
            print("[-] Error ", e, sha256)

        return

    def select(self, files):
        special = []
        newfiles = []
        for file in files:
            flag_os = 0
            flag_cb = 0
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

                    if issuetype == "DEVICE":
                        continue

                    if issuetype == "OS":
                        flag_os = 1

                    if issuetype == "CALLBACK":
                        flag_cb = 1

                    if patch_name not in patches:
                        patches.append(patch_name)

                    if keyword == "Localization":
                        if method.startswith("<android."):
                            android_locations.append(line)
                        else:
                            other_locations.append(line)
                        all_locations.append(line)

                    if keyword == "Success" or keyword == "OneMethodSuccess":
                        if method.startswith("<android."):
                            android_succ.append(line)
                        else:
                            other_succ.append(line)
                        all_succ.append(line)

                    if keyword == "Potential":
                        if method.startswith("<android."):
                            android_pot.append(line)
                        else:
                            other_pot.append(line)
                        all_pot.append(line)

            if flag_cb:
                special.append(file)
                continue
            elif flag_os and len(all_succ):
                newfiles.append(file)
                continue

        return list(set(newfiles)), list(set(special))


    def start(self, all_APK):
        files = []
        for sha256 in all_APK:
            file = os.path.join(APK_FOLDER, sha256 + ".apk")
            files.append(file)
        random.shuffle(files)
        # files = getFileList(APK_FOLDER, ".apk")
        selected_files = files
        print("[+] Analysing {} files".format(len(selected_files)))
        # selected_files.extend(specials)
        args = [file for file in selected_files]
        pool = threadpool.ThreadPool(self.max_jobs)
        requests = threadpool.makeRequests(self.process_one, args)
        [pool.putRequest(req) for req in requests]
        pool.wait()


if __name__ == '__main__':

    if os.path.exists(RECORD_TXT):
        with open(RECORD_TXT, "r") as fr:
            solved = fr.read().split("\n")
            for item in solved:
                all_solved[item] = 1

    if not os.path.exists(SAVEResults_DIR):
        os.mkdir(SAVEResults_DIR)

    with open(SELECT_APK, "r") as fr:
        s = fr.read().split("\n")
        for item in s:
            all_APK.append(item)

    all_APK = list(set(all_APK))
    print(len(all_APK))
    analysis = Analysis()
    analysis.start(all_APK)

