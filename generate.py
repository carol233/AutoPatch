import csv
import shlex
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

from helper import *

DEBUG = 0
if DEBUG:
    CSVInputPath = "test"
    PatchOutputPath = "testOutput"
else:
    CSVInputPath = "/data/sdc/yanjie/AutoPatch_dataset"
    PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch"

PairPath = "AutoPatch_Pairs.txt"
RECORD_TXT = "RawPatch_Parsed.txt"
Filed_File = "framework_fields.txt"
all_solved = {}
API_Old_dic = {}
API_new_dic = {}
fields = {}


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
                    if Old_API == "None" or New_API == "None":
                        continue
                    Stmts = line[3].strip("\"[]")
                    given_num = API_Old_dic[Old_API]
                    pattern = re.compile(r'<\S+:\s\S+\s([\w<>]+)\(.*\)>')
                    m = pattern.match(line[0])
                    if not m:
                        continue
                    method_name = m.group(1)
                    savePath = os.path.join(PatchOutputPath, str(given_num) + "_"
                                            + method_name + "_" + str(file_number) + ".patch")

                    # for debug
                    # if DEBUG:
                    #     if not "_4.patch" in savePath:
                    #         continue

                    new_PatchDenotation, SDK_VERSION_INT, all_variable_types, SEARCH_variables = self.solveLine(Old_API,
                                                                                                                New_API,
                                                                                                                Stmts)
                    newPatch = self.BuildPatch(new_PatchDenotation, SDK_VERSION_INT, Old_API, New_API,
                                               all_variable_types, SEARCH_variables)

                    # filter
                    flag_ifSave = 1
                    m5 = re.findall(r'<.*>', " ".join(newPatch))
                    for s in m5:
                        if not (s.startswith("<android") or s.startswith("<java")):
                            flag_ifSave = 0
                            break

                    if flag_ifSave == 1:
                        with open(savePath, "w") as fw:
                            for ll in newPatch:
                                fw.write(ll)
                                fw.write("\n")

            self.lock.acquire()
            with open(RECORD_TXT, "a+") as fw:
                fw.write(sha256 + "," + str(file_number))
                fw.write("\n")
            self.lock.release()

        except Exception as e:
            print(e, sha256)
        return

    def getNewVar(self, num):
        return "$v" + str(num)

    def BuildPatch(self, new_PatchDenotation, SDK_VERSION_INT, Old_API, New_API, all_variable_types, SEARCH_variables):
        newPatch = []
        BLANK = ""
        note1 = "//(" + SDK_VERSION_INT + ")" + Old_API
        note2 = "//----> " + New_API
        newPatch.append(note1)
        newPatch.append(note2)
        newPatch.append(BLANK)

        newPatch.append(Declare_Variable)
        for item in all_variable_types:
            if all_variable_types[item] != -1:
                newline = item + " := " + all_variable_types[item]
                if item in SEARCH_variables:
                    newline = "[SEARCH] " + newline
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
        SDK_VERSION_INT = ""
        STATE = "READ_NEW"
        FLAG_ifnext = 1  # for protection
        TargetStmt = ""
        all_variables = {}
        SEARCH_variables = {}
        all_variable_types = {}
        collect_seen_vars = {}
        new_PatchDenotation_part1 = []
        new_PatchDenotation_part2 = []
        sentences = re.split(r',(?![^(]*\))', Stmts)

        for tmpline in sentences:
            tmpline = tmpline.strip()
            if Old_API in tmpline and not tmpline.startswith("if "):
                paraVars3 = re.findall(r'\$[a-z]\d+', tmpline)
                if paraVars3:
                    for var in paraVars3:
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var
                        collect_seen_vars[new_var] = 1

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
                all_variable_types[new_var] = "int"
                symbol = m.group(2)
                SDK_VERSION_INT = m.group(3)
                TargetStmt = m.group(4).strip()

                newStmt1 = "+ " + new_var + " = " + SDK_VERSION_STR
                newStmt2 = "+ if " + new_var + " " + symbol + " " + SDK_VERSION_INT \
                           + " goto " + Label_Original
                new_PatchDenotation_part1.append(newStmt1)
                new_PatchDenotation_part1.append(newStmt2)

            elif line.startswith("return"):
                continue

            elif line.startswith("goto"):
                continue

            elif STATE == "READ_NEW" and (TargetStmt not in line or FLAG_ifnext):
                FLAG_ifnext = 0
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

                            if "$" in paraVar:
                                all_variable_types[paraVar] = paraType
                                if paraVar not in collect_seen_vars:
                                    if paraType == "int" or paraType == "java.lang.Integer":
                                        line = line.replace(paraVar, "0")
                                        all_variable_types[paraVar] = -1
                                    elif paraType == "float":
                                        line = line.replace(paraVar, "0.1")
                                        all_variable_types[paraVar] = -1
                                    else:
                                        # todo: consider [SEARCH] and "null"
                                        # line = line.replace(paraVar, "null")
                                        SEARCH_variables[paraVar] = 1

                        collect_seen_vars[rtnVar] = 1

                    else:
                        rtnVar2 = ""
                        if "=" in line:
                            rtnVar2 = line.split("=")[0].strip()

                        pattern2 = re.compile(r'[\S\s]+(\S+).<(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
                        m2 = pattern2.match(line)
                        if m2:
                            rtnType2 = m2.group(3)
                            baseVar2 = m2.group(1)
                            baseType2 = m2.group(2)
                            paraVars_s2 = m2.group(6)
                            paraTypes_s2 = m2.group(5)

                            all_variable_types[baseVar2] = baseType2.strip()
                            if rtnVar2:
                                all_variable_types[rtnVar2] = rtnType2.strip()

                            paraVars2 = paraVars_s2.split(",")
                            paraTypes2 = paraTypes_s2.split(",")
                            for i in range(0, len(paraVars2)):
                                paraVar2 = paraVars2[i].strip()
                                paraType2 = paraTypes2[i].strip()

                                if "$" in paraVar2:
                                    all_variable_types[paraVar2] = paraType2
                                    if paraVar2 not in collect_seen_vars:
                                        if paraType2 == "int" or paraType2 == "java.lang.Integer":
                                            line = line.replace(paraVar2, "0")
                                            all_variable_types[paraVar2] = -1
                                        elif paraType2 == "float":
                                            line = line.replace(paraVar2, "0.1")
                                            all_variable_types[paraVar2] = -1
                                        else:
                                            # todo: consider [SEARCH] and "null"
                                            # line = line.replace(paraVar2, "null")
                                            SEARCH_variables[paraVar2] = 1
                            collect_seen_vars[rtnVar2] = 1

                # parse field
                else:
                    pattern4 = re.compile(r'(\S+) = (\S+).<(\S+):\s(\S+)\s(\S+)>')
                    m4 = pattern4.match(line)
                    if m4:
                        rtnVar4 = m4.group(1)
                        rtnType4 = m4.group(4)
                        baseVar4 = m4.group(2)
                        baseType = m4.group(3)

                        all_variable_types[rtnVar4] = rtnType4.strip()
                        all_variable_types[baseVar4] = baseType.strip()

                        if baseVar4 not in collect_seen_vars:
                            SEARCH_variables[baseVar4] = 1

                        collect_seen_vars[rtnVar4] = 1

                newStmt = "+ " + line
                new_PatchDenotation_part1.append(newStmt)

            else:
                if TargetStmt in line:
                    STATE = "END_NEW"
                # old statements <label_original>
                newStmt1 = "+ goto " + Label_Next
                newStmt2 = "+ " + Label_Original
                if newStmt1 not in new_PatchDenotation_part1:
                    new_PatchDenotation_part1.append(newStmt1)
                    new_PatchDenotation_part1.append(newStmt2)

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

                            if "$" in paraVar:
                                all_variable_types[paraVar] = paraType

                    else:
                        rtnVar2 = ""
                        if "=" in line:
                            rtnVar2 = line.split("=")[0].strip()

                        pattern2 = re.compile(r'[\S\s]+(\S+).<(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
                        m2 = pattern2.match(line)
                        if m2:
                            rtnType2 = m2.group(3)
                            baseVar2 = m2.group(1)
                            baseType2 = m2.group(2)
                            paraVars_s2 = m2.group(6)
                            paraTypes_s2 = m2.group(5)

                            all_variable_types[baseVar2] = baseType2.strip()
                            all_variable_types[rtnVar2] = rtnType2.strip()
                            paraVars2 = paraVars_s2.split(",")
                            paraTypes2 = paraTypes_s2.split(",")
                            for i in range(0, len(paraVars2)):
                                paraVar2 = paraVars2[i].strip()
                                paraType2 = paraTypes2[i].strip()

                                if "$" in paraVar2:
                                    all_variable_types[paraVar2] = paraType2

                # parse field
                else:
                    pattern4 = re.compile(r'(\S+) = (\S+).<(\S+):\s(\S+)\s(\S+)>')
                    m4 = pattern4.match(line)
                    if m4:
                        rtnVar4 = m4.group(1)
                        rtnType4 = m4.group(4)
                        baseVar4 = m4.group(2)
                        baseType = m4.group(3)
                        all_variable_types[rtnVar4] = rtnType4.strip()
                        all_variable_types[baseVar4] = baseType.strip()

                flag = 0
                for item1 in new_PatchDenotation_part1[:]:
                    clean1 = item1.replace("+ ", "").strip()
                    if line.strip() == clean1:
                        flag = 1
                        new_PatchDenotation_part1.remove(item1)
                        allVars2 = re.findall(r'\$?[a-z]\d+', clean1)
                        if allVars2:
                            for var2 in allVars2:
                                all_variable_types[var2] = -1
                        break

                if flag == 0:
                    newStmt = "[Stmt] " + line
                    new_PatchDenotation_part2.append(newStmt)

        new_PatchDenotation = new_PatchDenotation_part1 + new_PatchDenotation_part2
        newStmt3 = "+ " + Label_Next
        new_PatchDenotation.append(newStmt3)

        return new_PatchDenotation, SDK_VERSION_INT, all_variable_types, SEARCH_variables

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
                sha2561 = item.split(",")[0]
                all_solved[sha2561] = 1

    check_and_mk_dir(PatchOutputPath)
    API_Old_dic, API_new_dic = loadPair(PairPath)

    with open(Filed_File, "r") as fr:
        for line in fr.read().split("\n"):
            filed = line.split("|")[0]
            value = line.split("|")[-1].split(":")[-1]
            fields[filed] = value

    print("Load ", len(API_Old_dic), " API pairs.")
    analysis = Analysis()
    analysis.start()
