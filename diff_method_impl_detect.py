#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Objective: used to detect different implementation of the
same methods on customized and official Android base framework
"""

import os
from collections import defaultdict

def commit_id_extract():
    config_path = '/Users/pliu0032/Documents/Compatibility/android-config.txt'
    with open(config_path) as f:
        lines = [line.strip() for line in f.readlines()]
    android_dict = dict()
    custom_dict = defaultdict(set)
    for line in lines:
        splits = line.split(',')
        if len(splits) != 6:
            continue
        if splits[0].lower() == 'android':
            ### android
            android_dict[splits[-1].strip()] = (splits[4].strip() , splits[0].strip().lower())
        else:
            custom_dict[splits[-1].strip()].add((splits[4].strip() , splits[0].strip().lower()))
    return android_dict, custom_dict

def commit_id_reset(repo_path, commit_id):
    cwd = os.getcwd()
    os.chdir(repo_path)
    res = os.popen('git reset --hard ' + commit_id).read()
    os.chdir(cwd)

def diff_impl_detect():
    platform_base = '/Users/pliu0032/AndroidVersion/platforms'
    out_base = '/Users/pliu0032/Documents/Compatibility/methods'
    jar_path = '/Users/pliu0032/Documents/Github/Diff4CiD.jar'
    androids, customizations = commit_id_extract()
    for level, id_name in androids.items():
        android_path = os.path.join(platform_base, androids[level][1])
        commit_id_reset(android_path, androids[level][0])
        if level in customizations:
            for cid, name in customizations[level]:
                if name == 'resur':
                    continue
                repo_path = os.path.join(platform_base, name)
                commit_id_reset(repo_path, cid)
                cmd = 'java -jar ' + jar_path + ' ' + repo_path + ' ' + android_path
                method_diff_res = os.popen(cmd).read()
                print(cmd, level)
                if method_diff_res:
                    out_dir = os.path.join(out_base, androids[level][1] + '-' + name)
                    if not os.path.exists(out_dir):
                        os.mkdir(out_dir)
                    out_path = os.path.join(out_dir, level + '.txt')
                    with open(out_path, 'w') as f:
                        f.write(method_diff_res)

if __name__ == '__main__':
#    commit_id_extract()
    diff_impl_detect()
