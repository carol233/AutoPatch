from helper import *

txt27000 = "27000record.txt"
COUNT_DIR = "/data/sdc/yanjie/AutoPatch_count"

all_27k = {}
all_depre_apis_count = {}
protected_depre_apis_count = {}
noprotected_depre_apis_count = {}
files_noProtection = {}


def parse_single_name(single_name):
    seen_apis = {}
    return_protection = 1
    with open(single_name, "r") as fr:
        reader = csv.reader(fr)
        for line in reader:
            if not line:
                continue
            if len(line) > 2:
                apisig = line[2].strip("\" ")
                if "No" in line[1]:
                    if_protect = 0
                else:
                    if_protect = 1

            else:
                apisig = line[1].strip("\" ")
                if "No" in line[0]:
                    if_protect = 0
                else:
                    if_protect = 1

            if apisig in seen_apis:
                continue
            else:
                seen_apis[apisig] = 1

            if if_protect == 1:
                if apisig in protected_depre_apis_count:
                    protected_depre_apis_count[apisig] += 1
                else:
                    protected_depre_apis_count[apisig] = 1
            else:
                return_protection = 0
                if apisig in noprotected_depre_apis_count:
                    noprotected_depre_apis_count[apisig] += 1
                else:
                    noprotected_depre_apis_count[apisig] = 1

            if apisig in all_depre_apis_count:
                all_depre_apis_count[apisig] += 1
            else:
                all_depre_apis_count[apisig] = 1

    return return_protection


if __name__ == '__main__':
    with open(txt27000, "r") as fr:
        lines = fr.read().split("\n")
        for line in lines:
            sha256 = line.replace("[+] PreSolving ", "").strip()
            if sha256:
                all_27k[sha256] = 1

    for sha256 in all_27k:
        single_name = os.path.join(COUNT_DIR, sha256 + ".csv")
        if os.path.exists(single_name):
            return_protection = parse_single_name(single_name)
            if return_protection == 0:
                files_noProtection[sha256] = 1
        else:
            print("No exist" + sha256)

    print("files with noprotection ", str(len(files_noProtection)))
    nolst = dic2list(noprotected_depre_apis_count)[:10]
    yeslst2 = dic2list(protected_depre_apis_count)[:10]

    print("\nno----------------")
    print(nolst)
    print("\nyes----------------")
    print(yeslst2)

    print(len(all_depre_apis_count), len(noprotected_depre_apis_count), len(protected_depre_apis_count))








