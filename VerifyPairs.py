import re


def loadpairs(Path):
    API_Old_dic = {}
    API_new_dic = {}
    num = 1
    with open(Path, "r") as f:
        lines = f.readlines()
        for line in lines:
            pattern = re.compile(r'\S+<\S+:\s(\S+)\s[\w<>]+\((.*)\)>[\s\S]+----> {1,10}(<\S+:\s(\S+)\s[\w<>]+\((.*)\)>)[\s\S]+')
            m = pattern.match(line)
            if m:
                sin_type1 = m.group(1)
                sin_type2 = m.group(3)
                para_type_s1 = m.group(2)
                para_type_s2 = m.group(4)

                paras = para_type_s1.split(",")
                paras.extend(para_type_s2.split(","))
                paras.append(sin_type1)
                paras.append(sin_type2)

                for item in paras:
                    if "." not in item:
                        flag = 1
                        for word in ["int","float","long","byte","void","boolean","","char","double"]:
                            if word == item or word + "[]" == item:
                                flag = 0
                                break

                        if flag == 1:
                            print(item)
                            print(line)


            else:
                print("Load error", line)

    return API_Old_dic, API_new_dic


if __name__ == "__main__":
    loadpairs("AutoPatch_Pairs.txt")