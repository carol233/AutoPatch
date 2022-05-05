import os
import shlex
import csv
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

JAR_PATH = "RepairDroid.jar"
APK_FOLDER1 = "/data/sdc/yanjie/APK2020/"
APK_FOLDER2 = "/mnt/fit-Knowledgezoo-vault/vault/apks/"
CDA_file = "CALLBACK.csv"
Android_jar = "/home/yanjie/android-sdk-linux/platforms"
RECORD_TXT = "record_evaluate_cb.txt"
APPPreAnalysis = "/data/sdc/yanjie/find2k_os"
SAVEResults_DIR = "/data/sdc/yanjie/find2k_evaluation_cb"

all_solved = {}

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
        self.max_jobs = 12
        self.lock = threading.Lock()
        self.map_api2patch = {}

    def readMap(self):
        with open(CDA_file, "r") as fr:
            reader = csv.reader(fr)
            for line in reader:
                api = line[0].strip("\"")
                patchPath = line[1]
                self.map_api2patch[api] = patchPath

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
        file = args
        sha256 = os.path.split(file)[-1][:-4]
        if sha256 in all_solved:
            return
        output_file = os.path.join(SAVEResults_DIR, sha256 + ".csv")
        if os.path.exists(output_file):
            return

        apk_file1 = os.path.join(APK_FOLDER1, sha256 + ".apk")
        apk_file2 = os.path.join(APK_FOLDER2, sha256 + ".apk")
        if os.path.exists(apk_file1):
            apk_path = apk_file1
        else:
            apk_path = apk_file2

        try:
            self.lock.acquire()
            with open(RECORD_TXT, "a+") as fw:
                fw.write(sha256)
                fw.write("\n")
            self.lock.release()

            # patchlist = []
            # with open(file, "r") as fr:
            #     reader = csv.reader(fr)
            #     for line in reader:
            #         api = line[2].strip("\"")
            #         patch1 = self.map_api2patch[api]
            #         if patch1 not in patchlist:
            #             patchlist.append(patch1)

            patchlist = ["CallBackPatches/onAttach_1.patch"]

            mode = 3
            for sematicPatch in patchlist:
                # xxx.apk platforms testoutput CDA.txt output.csv testoutput
                print("[+] PreSolving " + sha256, sematicPatch)
                CMD = "java -Xms2048m -Xmx4096m -XX:MaxNewSize=4096m " \
                      "-jar " + JAR_PATH + " " + str(mode) + " " + sematicPatch + " " + \
                      Android_jar + " " + apk_path + " " + output_file
                print(CMD)
                self.run(CMD, 300)

        except Exception as e:
            print("[-] Error ", e, sha256)

        return

    def start(self):
        self.readMap()
        files = getFileList(APPPreAnalysis, ".csv")
        print("[+] Analysing {} files".format(len(files)))
        args = [file for file in files]
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

    analysis = Analysis()
    analysis.start()

