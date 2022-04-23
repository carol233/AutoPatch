from helper import *
import os

DEBUG = 0
if DEBUG:
    PatchOutputPath = "testOutput"
    selected_path = "testPatchOutput"
else:
    PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch"
    selected_path = "/data/sdc/yanjie/AutoPatch_generatePatch_selected_2"
all_saved = {}

if __name__ == "__main__":
    check_and_mk_dir(selected_path)
    files = getFileList(PatchOutputPath, "")
    print(len(files))
    for file in files:
        short_name = os.path.split(file)[-1]
        API_num = short_name.split("_")[0]
        if API_num not in all_saved:
            with open(file, "r") as fr:
                content = fr.read()
                # filter
                flag_ifSave = 1
                # m5 = re.findall(r'<.*?>', content)
                # for s in m5:
                #     if not (s.startswith("<android") or s.startswith("<java")
                #             or s.startswith("< ") or s.startswith("<label")
                #             or s.startswith("<= ")):
                #         print(s)
                #         flag_ifSave = 0
                #         break

                if flag_ifSave == 1:
                    all_saved[API_num] = 1
                    newPath = os.path.join(selected_path, short_name)
                    cmd = "cp " + file + " " + newPath
                    os.popen(cmd)




