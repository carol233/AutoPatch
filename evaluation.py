from helper import *
import Levenshtein

def clean(s):
    pattern = re.compile(r'[\d\s|@]+')
    s = re.sub(pattern, "", s, 0)
    return s

def evaluate_patches(file1, file2):
    with open(file1, 'r') as fr1:
        p1 = fr1.read()
    with open(file2, 'r') as fr2:
        p2 = fr2.read()
    p1 = clean(p1)
    p2 = clean(p2)
    if Levenshtein.distance(p1, p2) < 2:
        print(p1)
        print("\n\n")
        print(p2)
        return True
    else:
        return False

def evaluate_DL(file1, file2):
    count_match = 0
    count_error = 0
    with open(file1, 'r') as fr1:
        lines1 = fr1.read().split("\n")
    with open(file2, 'r') as fr2:
        lines2 = fr2.read().split("\n")

    for i in range(len(lines1)):
        p1 = clean(lines1[i])
        p2 = clean(lines2[i])
        if Levenshtein.distance(p1, p2) < 10:
            print(p1)
            print(p2)
            count_match += 1
        else:
            count_error += 1
    return count_match, count_error

if __name__ == '__main__':
    count_match, count_error = evaluate_DL("test2/prediction_beam_1.txt", "test2/test/after.txt")
    print(count_match, count_error)