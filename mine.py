import os
import shutil
import shlex
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

JAR_PATH = "AutoPatch.jar"
APK_FOLDER = "/data/sdc/yanjie/APK2021"
SAVECSV_DIR = "/data/sdc/yanjie/AutoPatch_dataset2"
SAVEAPI_DIR = "/data/sdc/yanjie/AutoPatch_APIindex2"
Android_jar = "/home/yanjie/android-sdk-linux/platforms"
CDAPath = "AutoPatch_Pairs.txt"
RECORD_TXT = "record_0501.txt"

all_solved = {}
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
        if sha256 not in all_27k:
            return
        if sha256 in all_solved:
            return
        output_file = os.path.join(SAVECSV_DIR, sha256 + ".csv")

        try:
            self.lock.acquire()
            with open(RECORD_TXT, "a+") as fw:
                fw.write(sha256)
                fw.write("\n")
            self.lock.release()

            # xxx.apk platforms testoutput CDA.txt output.csv testoutput
            print("[+] PreSolving " + sha256)
            CMD = "java -Xms2048m -Xmx4096m " \
                  "-jar " + JAR_PATH + " " + file + " " + Android_jar \
                  + " " + output_file + " " + SAVEAPI_DIR + " " + CDAPath
            self.run(CMD, 180)

        except Exception as e:
            print(e, sha256)

        return

    def start(self):
        files = getFileList(APK_FOLDER, ".apk")
        print("[+] Analysing {} files".format(len(files)))
        args = [file for file in files]
        pool = threadpool.ThreadPool(self.max_jobs)
        requests = threadpool.makeRequests(self.process_one, args)
        [pool.putRequest(req) for req in requests]
        pool.wait()


if __name__ == '__main__':

    with open("27000record.txt", "r") as fr:
        lines = fr.read().split("\n")
        for line in lines:
            sha256 = line.replace("[+] PreSolving ", "").strip()
            if sha256:
                all_27k[sha256] = 1

    if os.path.exists(RECORD_TXT):
        with open(RECORD_TXT, "r") as fr:
            solved = fr.read().split("\n")
            for item in solved:
                all_solved[item] = 1

    if not os.path.exists(SAVECSV_DIR):
        os.mkdir(SAVECSV_DIR)
    if not os.path.exists(SAVEAPI_DIR):
        os.mkdir(SAVEAPI_DIR)
    analysis = Analysis()
    analysis.start()

