from helper import *
import csv

PairPath = "AutoPatch_Pairs.txt"
CSVInputPath = "/data/sdc/yanjie/AutoPatch_dataset"
Patches = "/data/sdc/yanjie/AutoPatch_generatePatch_selected/"

Root_dir = "/data/sdc/yanjie/AutoPatch_DL/"
check_and_mk_dir(Root_dir)
Output_all = Root_dir + "input_all.txt"
Output_input = Root_dir + "input_filter.txt"
Output_GroundTruth = Root_dir + "output_filter.txt"
jishu = Root_dir + "count.txt"

API_Old_dic = {}
API_new_dic = {}
all_data = {}
filter_data = {}

if __name__ == "__main__":
    API_Old_dic, API_new_dic = loadPair(PairPath)
    files = getFileList(CSVInputPath, ".csv")
    for file in files:
        with open(file, "r") as fr1:
            reader = csv.reader(fr1)
            for line in reader:
                Old_API = line[0].strip("\"' ")
                New_API = line[1].strip("\"' ")
                if Old_API == "None" or New_API == "None":
                    continue

                Stmts = line[3].strip("\"[]")
                if Old_API in all_data:
                    all_data[Old_API].append(Stmts)
                else:
                    all_data[Old_API] = []
                    all_data[Old_API].append(Stmts)

                flag_ifSave = 1
                m5 = re.findall(r'<.*>', " ".join(Stmts))
                for s in m5:
                    if not (s.startswith("<android") or s.startswith("<java")):
                        flag_ifSave = 0
                        break

                if flag_ifSave == 1:
                    # save and count

                    if Old_API in filter_data:
                        filter_data[Old_API].append(Stmts)
                    else:
                        filter_data[Old_API] = []
                        filter_data[Old_API].append(Stmts)

    all_patches = getFileList(Patches, ".patch")
    for Old_API in filter_data:
        with open(Output_input, "a+") as fw1:
            lst = filter_data[Old_API]
            for item in lst:
                fw1.write(item)
                fw1.write("\n")

        repeat_num = len(lst)
        with open(jishu, "a+") as fw2:
            fw2.write(Old_API + "|" + str(repeat_num))
            fw2.write("\n")

        if Old_API not in API_Old_dic:
            print(Old_API)
            continue

        API_num = API_Old_dic[Old_API]
        gr = Patches + str(API_num) + "_"
        for patch in all_patches:
            if gr in patch:
                with open(patch, "r") as fr:
                    content = fr.read(patch)
                    line = content.replace('\n', '|').replace('\r', '|')

                    count = 1
                    with open(Output_GroundTruth, "a+") as fw3:
                        if count <= repeat_num:
                            fw3.write(line)
                            fw3.write("\n")
                            count += 1












