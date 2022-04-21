import hashlib
import os
import re

SDK_VERSION_STR = "<android.os.Build$VERSION: int SDK_INT>"
SDKVersionValue = -1
Label_Original = "<label_original>"
Label_Next = "<label_next>"
Declare_Variable = "@@ Variable declaration"
Declare_Location = "@@ Issue Location"
Declare_Denotation = "@@ Patch Denotation"

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

def check_and_mk_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def get_md5(s):
    m = hashlib.md5()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

def loadPair(Path):
    API_Old_dic = {}
    API_new_dic = {}
    num = 1
    with open(Path, "r") as f:
        lines = f.readlines()
        for line in lines:
            pattern = re.compile(r'\S+(<\S+:\s+\S+\s+[\w<>]+\(.*\)>)[\s\S]+----> {1,10}(<\S+:\s+\S+\s+[\w<>]+\(.*\)>)[\s\S]+')
            m = pattern.match(line)
            if m:
                old_sig = m.group(1)
                new_sig = m.group(2)
                API_Old_dic[old_sig] = num
                API_new_dic[new_sig] = num
                num += 1
            else:
                print("Load CDA error", line)
    return API_Old_dic, API_new_dic

