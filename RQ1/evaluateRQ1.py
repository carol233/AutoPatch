import re

pairfile = "/Users/yzha0544/PycharmProjects/AutoPatch/NewPairs.txt"
file1 = "/Users/yzha0544/PycharmProjects/AutoPatch/RQ1/30.txt"

if __name__ == '__main__':
    cda = {}
    sc = {}
    with open(pairfile, "r") as fr:
        lines = fr.read().split("\n")
        for line in lines:
            if line.startswith("(30)"):
                pattern = re.compile(r'\S+(<\S+:\s+\S+\s+[\w<>]+\(.*\)>)[\s\S]+----> {1,10}(<\S+:\s+\S+\s+[\w<>]+\(.*\)>)[\s\S]+')
                m = pattern.match(line)
                if m:
                    method = m.group(1)
                    if method in cda:
                        print(line)
                    cda[method] = 1
                else:
                    print(line)

    with open(file1, "r") as fr2:
        lines = fr2.read().split("\n")
        for line in lines:
            method = line.split("|")[0]
            if method.startswith("<com.android"):
                continue
            sc[method] = 1

    matches = {}
    for item1 in cda:
        pattern1 = re.compile(r'<(\S+):\s+\S+\s+([\w<>]+)\(.*\)>')
        m1 = pattern1.match(item1)
        if m1:
            classname1 = m1.group(1).strip()
            methodname1 = m1.group(2).strip()


            for item2 in sc:
                pattern2 = re.compile(r'<(\S+):\s+\S+\s+([\w<>]+)\(.*\)>')
                m2 = pattern2.match(item2)
                if m2:
                    classname2 = m2.group(1).strip()
                    methodname2 = m2.group(2).strip()

                    if classname1 == classname2 and methodname1 == methodname2:
                        matches[item1] = item2
                        break

    print(len(matches), len(cda), len(sc))
    for item in cda.keys() - matches.keys():
        print(item)




