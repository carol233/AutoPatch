import csv
import shlex
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

from helper import *

CDAPath = "CDA.txt"
# CSVInputPath = "/data/sdc/yanjie/AutoPatch_dataset"
# PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch"
CSVInputPath = "test"
PatchOutputPath = "testOutput"
RECORD_TXT = "RawPatch_Parsed.txt"
all_solved = {}
API_Old_dic = {}
API_new_dic = {}

class Analysis:
    def __init__(self):
        self.max_jobs = 12
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
        if sha256 in all_solved:
            return
        try:
            self.lock.acquire()
            all_solved[sha256] = 1
            file_number = len(all_solved)
            self.lock.release()

            with open(file, "r") as fr1:
                reader = csv.reader(fr1)
                for line in reader:
                    Old_API = line[0].strip("\"' ")
                    New_API = line[1].strip("\"' ")
                    Stmts = line[3].strip("\"[]")
                    given_num = API_Old_dic[Old_API]
                    pattern = re.compile(r'<\S+:\s\S+\s([\w<>]+)\(.*\)>')
                    m = pattern.match(line[0])
                    if not m:
                        continue
                    method_name = m.group(1)
                    savePath = os.path.join(PatchOutputPath, str(given_num) + "_"
                                            + method_name + "_" + str(file_number) + ".patch")

                    new_PatchDenotation, SDK_VERSION_INT, all_variable_types = self.solveLine(Old_API, New_API, Stmts)
                    newPatch = self.BuildPatch(new_PatchDenotation, SDK_VERSION_INT, Old_API, New_API, all_variable_types)
                    with open(savePath, "w") as fw:
                        for line in newPatch:
                            fw.write(line)
                            fw.write("\n")

            self.lock.acquire()
            with open(RECORD_TXT, "a+") as fw:
                fw.write(sha256)
                fw.write("\n")
            self.lock.release()

        except Exception as e:
            print(e, sha256)
        return

    def getNewVar(self, num):
        return "$r" + str(num)

    def BuildPatch(self, new_PatchDenotation, SDK_VERSION_INT, Old_API, New_API, all_variable_types):
        newPatch = []
        BLANK = ""
        note1 = "//(" + SDK_VERSION_INT + ")" + Old_API
        note2 = "//----> " + New_API
        newPatch.append(note1)
        newPatch.append(note2)
        newPatch.append(BLANK)

        newPatch.append(Declare_Variable)
        for item in all_variable_types:
            newline = item + " := " + all_variable_types[item]
            newPatch.append(newline)
        newPatch.append(BLANK)
        newPatch.append(Declare_Location)
        location = "[OS] " + Old_API + " Build.VERSION.SDK_INT " + SDK_VERSION_INT
        newPatch.append(location)
        newPatch.append(BLANK)
        newPatch.append(Declare_Denotation)
        newPatch.extend(new_PatchDenotation)

        return newPatch


    def solveLine(self, Old_API, New_API, Stmts):
        TargetStmt = ""
        SDK_VERSION_INT = ""
        STATE = "READ_NEW"
        all_variables = {}
        all_variable_types = {}
        new_PatchDenotation = []
        sentences = re.split(r',(?![^(]*\))', Stmts)

        for line in sentences:
            line = line.strip()
            if line.startswith("if "):
                pattern = re.compile(r'if (\$?[a-z]\d+) ([<>=]+) (\d+) goto (.*)')
                m = pattern.match(line)
                if not m:
                    continue
                var_sdk = m.group(1)
                new_var = self.getNewVar(len(all_variables))
                all_variables[var_sdk] = new_var
                symbol = m.group(2)
                SDK_VERSION_INT = m.group(3)
                TargetStmt = m.group(4).strip()

                newStmt1 = "+ " + new_var + " = " + SDK_VERSION_STR
                newStmt2 = "+ if " + new_var + " " + symbol + " " + SDK_VERSION_INT \
                           + " goto " + Label_Original
                new_PatchDenotation.append(newStmt1)
                new_PatchDenotation.append(newStmt2)

            elif line.startswith("return "):
                continue

            elif STATE == "READ_NEW":
                allVars = re.findall(r'\$?[a-z]\d+', line)
                if allVars:
                    for var in allVars:
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var

                        line = line.replace(var, new_var)

                # means there is a method call
                if "invoke " in line:
                    # static invoke
                    pattern = re.compile(r'(\$?[a-z]\d+) = staticinvoke <(\S+): (\S+) (\w+)\((.*)\)>\((.*)\)')
                    m = pattern.match(line)
                    if m:
                        rtnVar = m.group(1)
                        rtnType = m.group(3)
                        paraVars_s = m.group(6)
                        paraTypes_s = m.group(5)

                        all_variable_types[rtnVar] = rtnType.strip()
                        paraVars = paraVars_s.split(",")
                        paraTypes = paraTypes_s.split(",")
                        for i in range(0, len(paraVars)):
                            paraVar = paraVars[i].strip()
                            paraType = paraTypes[i].strip()

                            # if paraType == "int" or paraType == "java.lang.Integer":
                            #     line = line.replace(paraVar, "1")
                            # elif paraType == "float":
                            #     line = line.replace(paraVar, "0.1")
                            # else:
                            if "$" in paraVar:
                                all_variable_types[paraVar] = paraType

                    else:
                        pattern2 = re.compile(r'(\$?[a-z]\d+) = \w+ (\S+).<(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
                        m2 = pattern2.match(line)
                        if m2:
                            rtnVar2 = m2.group(1)
                            rtnType2 = m2.group(4)
                            baseVar2 = m2.group(2)
                            baseType2 = m2.group(3)
                            paraVars_s2 = m2.group(7)
                            paraTypes_s2 = m2.group(6)
                            all_variable_types[baseVar2] = baseType2.strip()
                            all_variable_types[rtnVar2] = rtnType2.strip()
                            paraVars2 = paraVars_s2.split(",")
                            paraTypes2 = paraTypes_s2.split(",")
                            for i in range(0, len(paraVars2)):
                                paraVar2 = paraVars2[i].strip()
                                paraType2 = paraTypes2[i].strip()

                                # if paraType2 == "int" or paraType2 == "java.lang.Integer":
                                #     line = line.replace(paraVar2, "1")
                                # elif paraType2 == "float":
                                #     line = line.replace(paraVar2, "0.1")
                                # else:
                                if "$" in paraVar2:
                                    all_variable_types[paraVar2] = paraType2

                newStmt = "+ " + line
                new_PatchDenotation.append(newStmt)

                if New_API in line:
                    # by default, new API first, old API second
                    STATE = "END_NEW"

            else:
                # old statements <label_original>
                newStmt1 = "+ goto " + Label_Next
                newStmt2 = "+ " + Label_Original
                if newStmt1 not in new_PatchDenotation:
                    new_PatchDenotation.append(newStmt1)
                    new_PatchDenotation.append(newStmt2)

                allVars = re.findall(r'\$?[a-z]\d+', line)
                if allVars:
                    for var in allVars:
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var

                        line = line.replace(var, new_var)

                # means there is a method call
                if "invoke " in line:
                    # static invoke
                    pattern = re.compile(r'(\$?[a-z]\d+) = staticinvoke <(\S+): (\S+) (\w+)\((.*)\)>\((.*)\)')
                    m = pattern.match(line)
                    if m:
                        rtnVar = m.group(1)
                        rtnType = m.group(3)
                        paraVars_s = m.group(6)
                        paraTypes_s = m.group(5)

                        all_variable_types[rtnVar] = rtnType.strip()
                        paraVars = paraVars_s.split(",")
                        paraTypes = paraTypes_s.split(",")
                        for i in range(0, len(paraVars)):
                            paraVar = paraVars[i].strip()
                            paraType = paraTypes[i].strip()

                            # if paraType == "int" or paraType == "java.lang.Integer":
                            #     line = line.replace(paraVar, "1")
                            # elif paraType == "float":
                            #     line = line.replace(paraVar, "0.1")
                            # else:
                            if "$" in paraVar:
                                all_variable_types[paraVar] = paraType

                    else:
                        pattern2 = re.compile(r'(\$?[a-z]\d+) = \w+ (\S+).<(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
                        m2 = pattern2.match(line)
                        if m2:
                            rtnVar2 = m2.group(1)
                            rtnType2 = m2.group(4)
                            baseVar2 = m2.group(2)
                            baseType2 = m2.group(3)
                            paraVars_s2 = m2.group(7)
                            paraTypes_s2 = m2.group(6)
                            all_variable_types[baseVar2] = baseType2.strip()
                            all_variable_types[rtnVar2] = rtnType2.strip()
                            paraVars2 = paraVars_s2.split(",")
                            paraTypes2 = paraTypes_s2.split(",")
                            for i in range(0, len(paraVars2)):
                                paraVar2 = paraVars2[i].strip()
                                paraType2 = paraTypes2[i].strip()

                                # if paraType2 == "int" or paraType2 == "java.lang.Integer":
                                #     line = line.replace(paraVar2, "1")
                                # elif paraType2 == "float":
                                #     line = line.replace(paraVar2, "0.1")
                                # else:
                                if "$" in paraVar2:
                                    all_variable_types[paraVar2] = paraType2

                newStmt = "[Stmt] " + line
                new_PatchDenotation.append(newStmt)

        newStmt3 = "+ " + Label_Next
        new_PatchDenotation.append(newStmt3)
        return new_PatchDenotation, SDK_VERSION_INT, all_variable_types

    def start(self):
        files = getFileList(CSVInputPath, ".csv")
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
    check_and_mk_dir(PatchOutputPath)
    API_Old_dic, API_new_dic = loadCDA(CDAPath)
    print("Load ", len(API_Old_dic), " API pairs.")
    analysis = Analysis()
    analysis.start()
