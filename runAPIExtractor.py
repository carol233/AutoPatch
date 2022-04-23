# coding:utf-8
import os
import random
import subprocess
import threadpool
import re
from helper import *


class PresolveAPK:
    def __init__(self, input_path, maxjob, presolve, android_jars):
        self.input = input_path
        self.max_jobs = maxjob
        self.outputpath = presolve
        self.android_jars = android_jars

    def processone(self, apk):
        apkname = os.path.split(apk)[-1][:-4]
        output = os.path.join(self.outputpath, apkname + ".csv")
        if os.path.exists(output):
            return
        try:
            print("[+] PreSolving " + apkname)

            with open(output, "w") as fw:
                fw.write("if,API_signature")

            CMD = "java -Xms2g -Xmx4g -jar APIExtractor.jar " + \
                  apk + " any " + self.android_jars + " " + output

            print(CMD)
            subprocess.run(CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding="utf-8", timeout=180)

        except subprocess.TimeoutExpired as exc:
            print("Command timed out: {}".format(exc))
            return
        except Exception as e:
            print(e)
            return


    def start(self):
        apks = getFileList(self.input, ".apk")
        random.shuffle(apks)
        print("[+] Total " + str(len(apks)) + " apks")
        args = [(apk) for apk in apks]
        pool = threadpool.ThreadPool(self.max_jobs)
        requests = threadpool.makeRequests(self.processone, args)
        [pool.putRequest(req) for req in requests]
        pool.wait()


if __name__ == '__main__':

    input_path = "/data/sdc/yanjie/APK2021"
    andro_jar = "/home/yanjie/android-sdk-linux/platforms"
    save_path = "/data/sdc/yanjie/AutoPatch_count"
    check_and_mk_dir(save_path)

    prosolve = PresolveAPK(input_path, 8, save_path, andro_jar)
    prosolve.start()

