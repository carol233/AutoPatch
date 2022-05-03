from helper import *

PatchOutputPath = "/data/sdc/yanjie/AutoPatch_generatePatch2"

count = {}
map = {}
if __name__ == '__main__':
    files = getFileList(PatchOutputPath, ".patch")
    for file in files:
        shortname = os.path.split(file)[-1]
        num = shortname.split("_")[0]
        methodname = shortname.split("_")[1]
        map[num] = methodname
        if num in count:
            count[num] += 1
        else:
            count[num] = 1

    most = dic2list(count)[:10]
    for item in most:
        print(item)
        print(map[item[0]])


