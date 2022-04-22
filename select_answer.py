from helper import *
import os
PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch"
selected_path = "/data/sdc/yanjie/AutoPatch_generatePatch_selected"

all_saved = {}


check_and_mk_dir(selected_path)
files = getFileList(PatchOutputPath, "")
print(len(files))
for file in files:
    short_name = os.path.split(file)[-1]
    API_num = short_name.split("_")[0]
    if API_num not in all_saved:
        all_saved[API_num] = 1
        newPath = os.path.join(selected_path, short_name)
        cmd = "cp " + file + " " + newPath
        os.popen(cmd)



