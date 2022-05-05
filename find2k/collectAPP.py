
import os
import shlex
import csv
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer


APK_FOLDER1 = "/data/sdc/yanjie/APK2021/"
APK_FOLDER2 = "/mnt/fit-Knowledgezoo-vault/vault/apks/"
patch_os = "OSPatches"
newpath = "/data/sdc/yanjie/APPForAutoPatch"

def run(cmd, timeout_sec):
    proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    timer = Timer(timeout_sec, proc.kill)
    try:
        timer.start()
        # stdout, stderr = proc.communicate()
        print(proc.stdout.readlines())
    finally:
        timer.cancel()

if __name__ == '__main__':
    if not os.path.exists(newpath):
        os.mkdir(newpath)

    with open("record_run1k_4.txt", "r") as fr:
        lines = fr.readlines()
        for line in lines:
            if line:
                sha256 = line.strip()

                apk_file1 = os.path.join(APK_FOLDER1, sha256 + ".apk")
                apk_file2 = os.path.join(APK_FOLDER2, sha256 + ".apk")

                if os.path.exists(apk_file1):
                    apk_path = apk_file1
                else:
                    apk_path = apk_file2

                newfile = os.path.join(newpath, sha256 + ".apk")

                CMD = "cp " + apk_path + " " + newfile

                run(CMD, 300)