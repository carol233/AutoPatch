import re

file1 = "/Users/yzha0544/PycharmProjects/AutoPatch/RQ1/replacement-30.txt"
file2 = "/Users/yzha0544/PycharmProjects/AutoPatch/RQ1/From_29_to_30"
file3 = "30.txt"

if __name__ == '__main__':
    selected = {}
    output = []
    with open(file2, "r") as fr:
        lines = fr.read().split("\n")
        for line in lines:
            m = re.findall(r'<\S+:\s+\S+\s+[\w<>]+\(.*\)>', line)
            if m:
                methodsig= m[0]
                selected[methodsig] = 1

    with open(file1, "r") as fr2:
        lines = fr2.read().split("\n")
        for line in lines:
            method = line.split("|")[0]
            if method in selected:
                output.append(line)

    with open(file3, "w") as fw:
        for line in output:
            fw.write(line)
            fw.write("\n")
