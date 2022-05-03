import csv
import shlex
import threadpool
import threading
from subprocess import Popen, PIPE
from threading import Timer

from nltk.sem.chat80 import items

from helper import *

DEBUG = 0
if DEBUG:
    print("[-] Debug mode...")
    CSVInputPath = "test"
    PatchOutputPath = "testOutput"
else:
    CSVInputPath = "/data/sdc/yanjie/AutoPatch_dataset2"
    PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch2"

PairPath = "AutoPatch_Pairs.txt"
RECORD_TXT = "RawPatch_Parsed.txt"
Filed_File = "framework_fields.txt"
all_solved = {}
API_Old_dic = {}
API_new_dic = {}
fields = {}


class Analysis:
    def __init__(self):
        self.max_jobs = 15
        self.lock = threading.Lock()

    def clean(self, s):
        pattern = re.compile(r'[\s\'()<>"]+')
        s = re.sub(pattern, "", s, 0)
        return s

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
                    pattern = re.compile(r'<\S+:\s\S+\s(\S+)\(.*\)>')
                    m = pattern.match(line[0])
                    if not m:
                        continue
                    method_name = m.group(1)
                    savePath = os.path.join(PatchOutputPath, str(given_num) + "_"
                                            + method_name + "_" + str(file_number) + ".patch")

                    if DEBUG:
                        if not "setView" in savePath:
                            continue

                    new_PatchDenotation, SDK_VERSION_INT, all_variable_types, SEARCH_variables = self.solveLine(Old_API,
                                                                                                                New_API,
                                                                                                                Stmts)

                    ss_ = " ".join(new_PatchDenotation)
                    if Old_API not in ss_ or New_API not in ss_ or \
                            " 512 " in ss_ or SDK_VERSION_STR not in ss_:
                        continue

                    newPatch = self.BuildPatch(new_PatchDenotation, SDK_VERSION_INT, Old_API, New_API,
                                               all_variable_types, SEARCH_variables)

                    # filter
                    flag_ifSave = 1
                    m5 = re.findall(r'<.*?>', " ".join(newPatch))
                    for s in m5:
                        if not (s.startswith("<android") or s.startswith("<java")
                                or s.startswith("< ") or s.startswith("<label")
                                or s.startswith("<= ")):
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
        return "$y" + str(num)

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
            if all_variable_types[item] != -1 and item.startswith("$"):
                newline = item + " := " + all_variable_types[item]
                if item in SEARCH_variables:
                    if SEARCH_variables[item] != -1:
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
                paraVars3 = re.findall(r'\$?[a-z]\d+', tmpline)
                if paraVars3:
                    for var in paraVars3:
                        if var == "v4" and var == "v7":
                            continue
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var

        for line in sentences:
            line = line.strip().replace("'", "")
            if line.startswith("if "):
                pattern = re.compile(r'if (\$?[a-z]\d+) (<=?) (\d+) goto (.*)')
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

            elif ":= @caughtexception" in line:
                continue

            elif re.compile(r'\$?[a-z]\d+ = [-.\d]+').match(line):
                m = re.compile(r'(\$?[a-z]\d+) = ([-.\d]+)').match(line)
                var = m.group(1)
                value = m.group(2)
                all_variables[var] = value
                continue

            elif re.compile(r'\$?[a-z]\d+ = null').match(line):
                continue

            elif STATE == "READ_NEW" and (TargetStmt not in line or FLAG_ifnext):
                FLAG_ifnext = 0
                allVars = re.findall(r'\$?[a-z]\d+', line)
                if allVars:
                    for var in allVars:
                        if var == "v4" and var == "v7":
                            continue
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var

                        line = line.replace(var, new_var)

                # means there is a method call
                if "invoke " in line:
                    # static invoke
                    pattern = re.compile(r'(\$?[a-z]\d+) = staticinvoke <(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
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
                            if rtnVar2:
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
                        if var == "v4" and var == "v7":
                            continue
                        if var in all_variables:
                            new_var = all_variables[var]
                        else:
                            new_var = self.getNewVar(len(all_variables))
                            all_variables[var] = new_var

                        line = line.replace(var, new_var)

                # means there is a method call
                if "invoke " in line:
                    # static invoke
                    pattern = re.compile(r'(\$?[a-z]\d+) = staticinvoke <(\S+): (\S+) (\S+)\((.*)\)>\((.*)\)')
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

                flagg = 0
                for item1 in new_PatchDenotation_part1[:]:
                    clean1 = item1.replace("+ ", "").strip()
                    if line.strip() == clean1:
                        flagg = 1
                        new_PatchDenotation_part1.remove(item1)
                        allVars2 = re.findall(r'\$?[a-z]\d+', clean1)
                        if allVars2:
                            for var2 in allVars2:
                                all_variable_types[var2] = -1
                        break

                if flagg == 0:
                    newStmt = "[Stmt] " + line
                    new_PatchDenotation_part2.append(newStmt)

        new_PatchDenotation = new_PatchDenotation_part1 + new_PatchDenotation_part2
        newStmt3 = "+ " + Label_Next
        new_PatchDenotation.append(newStmt3)

        # start clean
        clean_PatchDenotation0 = []
        for item in new_PatchDenotation:
            if item.startswith("+ \"") or item.startswith("+ \'"):
                continue
            if SDK_VERSION_STR in item:
                if SDK_VERSION_STR in "".join(clean_PatchDenotation0):
                    clean_PatchDenotation0 = []
            clean_PatchDenotation0.append(item)

        clean_PatchDenotation1 = clean_PatchDenotation0
        stack1 = []
        var_forNew = {}
        for item in clean_PatchDenotation0:
            if New_API in item:
                paraVars = re.findall(r'\$[a-z]\d+', item)
                if not paraVars:
                    continue
                for param in paraVars:
                    var_forNew[param] = 1
                break
            if "goto <label_original>" not in item and SDK_VERSION_STR not in item:
                stack1.append(item)

        for i in range(len(stack1)):
            flag_remove = 1
            s = stack1.pop()
            for var in var_forNew:
                if var in s:
                    flag_remove = 0
                    continue
            if flag_remove:
                clean_PatchDenotation1.remove(s)
            else:
                paraVars = re.findall(r'\$[a-z]\d+', s)
                if not paraVars:
                    continue
                for param in paraVars:
                    var_forNew[param] = 1

        # collect seen vars
        for item in clean_PatchDenotation1:
            if item.startswith("+"):
                if "=" in item:
                    s = item.split("=")[0]
                    paraVars = re.findall(r'\$[a-z]\d+', s)
                    if not paraVars:
                        continue
                    for param in paraVars:
                        collect_seen_vars[param] = 1
            else:
                paraVars = re.findall(r'\$[a-z]\d+', item)
                if not paraVars:
                    continue
                for param in paraVars:
                    collect_seen_vars[param] = 1

        # decide which to search
        for item in clean_PatchDenotation1:
            if item.startswith("+"):
                if "=" in item:
                    s = item.split("=")[1]
                else:
                    s = item
                paraVars = re.findall(r'\$[a-z]\d+', s)
                if not paraVars:
                    continue
                for param in paraVars:
                    if param not in collect_seen_vars:
                        SEARCH_variables[param] = 1
                    else:
                        SEARCH_variables[param] = -1

        # collect constants
        collect_seen_constants = {}
        constants_to_variable = {}
        for line in clean_PatchDenotation1:
            if not line.startswith("[Stmt]"):
                continue
            pattern = re.compile(r'[\S\s]+<\S+: \S+ \S+\((.*)\)>\((.*)\)')
            m = pattern.match(line)
            if m:
                paraVars_s = m.group(2)
                paraTypes_s = m.group(1)
                paraVars = paraVars_s.split(",")
                paraTypes = paraTypes_s.split(",")
                for i in range(0, len(paraVars)):
                    paraVar = paraVars[i].strip()
                    paraType = paraTypes[i].strip()
                    if "$" not in paraVar and paraVar:
                        collect_seen_constants[paraVar] = paraType

        # replacement new
        clean_PatchDenotation2 = []
        for line in clean_PatchDenotation1:
            if not line.startswith("+"):
                clean_PatchDenotation2.append(line)
                continue
            pattern = re.compile(r'[\S\s]+<\S+: \S+ \S+\((.*)\)>\((.*)\)')
            m = pattern.match(line)
            if m:
                paraVars_s = m.group(2)
                paraTypes_s = m.group(1)
                paraVars = paraVars_s.split(",")
                paraTypes = paraTypes_s.split(",")
                for i in range(0, len(paraVars)):
                    paraVar = paraVars[i].strip()
                    paraType = paraTypes[i].strip()

                    if "$" in paraVar:
                        # Todo: solve constants
                        all_variable_types[paraVar] = paraType
                        if paraVar not in collect_seen_vars:
                            if paraType == "int" or paraType == "java.lang.Integer":
                                # todo: 15_createVideoThumbnail_3986.patch
                                replaceInt = "0"
                                for constant in collect_seen_constants:
                                    type = collect_seen_constants[constant]
                                    if type == "int" or type == "java.lang.Integer":
                                        replaceInt = constant
                                line = rreplace(line, paraVar, replaceInt, 1)
                                all_variable_types[paraVar] = -1
                            elif paraType == "float":
                                line = rreplace(line, paraVar, "0.1", 1)
                                all_variable_types[paraVar] = -1
                            else:
                                SEARCH_variables[paraVar] = 1
                    else:
                        if paraVar in collect_seen_constants and paraVar:
                            if paraType == collect_seen_constants[paraVar]:
                                new_var = self.getNewVar(len(all_variables))
                                all_variables[paraVar] = new_var
                                all_variable_types[paraVar] = paraType
                                constants_to_variable[paraVar] = new_var
                                # from right to left
                                line = rreplace(line, paraVar, constants_to_variable[paraVar], 1)
            clean_PatchDenotation2.append(line)

        # replacement old
        clean_PatchDenotation3 = []
        for line in clean_PatchDenotation2:
            if not line.startswith("[Stmt]"):
                clean_PatchDenotation3.append(line)
                continue
            pattern = re.compile(r'[\S\s]+<\S+: \S+ \S+\((.*)\)>\((.*)\)')
            m = pattern.match(line)
            if m:
                paraVars_s = m.group(2)
                paraTypes_s = m.group(1)
                paraVars = paraVars_s.split(",")
                paraTypes = paraTypes_s.split(",")
                for i in range(0, len(paraVars)):
                    paraVar = paraVars[i].strip()
                    paraType = paraTypes[i].strip()
                    if "$" not in paraVar and paraVar:
                        if paraVar in constants_to_variable:
                            # from right to left
                            line = rreplace(line, paraVar, constants_to_variable[paraVar], 1)
            clean_PatchDenotation3.append(line)

        return clean_PatchDenotation3, SDK_VERSION_INT, all_variable_types, SEARCH_variables

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
