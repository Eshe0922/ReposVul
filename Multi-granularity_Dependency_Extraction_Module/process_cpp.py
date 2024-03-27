import os
import json
import subprocess
import zipfile
import sys
import re
import concurrent.futures
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import parse_getout_nearfunc_cpp
import traceback

def process_content(lock, line, new_list):
    json_file = json.loads(line)
    if json_file['function_id'] in new_list:
        return
    publish_date = json_file['file_path'].replace('\\', '/').split('/')[1]
    function_id = json_file['function_id']
    final_output_json = dict()
    final_output_json['function_id'] = function_id
    final_output_json['caller'] = dict()
    final_output_json['callee'] = dict()
    try:
        commit_id = json_file['parents'][0]['commit_id_before']
        file_name = json_file['file_name']
        path_before = '/new_data/Challenge/REEF-scripit-own/repos_before/{}/{}.zip'.format(publish_date, commit_id)
        if json_file['file_target'] == '-1':
            return
        with zipfile.ZipFile(path_before, 'r') as zip_ref:
            contents = zip_ref.namelist()
        folder_name = contents[0][:-1]
        path_after = '/new_data/Challenge/unzip_tmp'
        print(folder_name)
        unzip_code_path = '{}/{}/{}'.format(path_after, folder_name, file_name)
        print(unzip_code_path)
        run_code = 'timeout 300 cflow -T -d 2 --omit-symbol-names -r $(find {}/{} -type f -name "*.cc") $(find {}/{} -type f -name "*.cpp")'.format(path_after, folder_name, path_after, folder_name)
        dir_path = '{}/{}'.format(path_after, folder_name)
        result1 = subprocess.run(run_code, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=dir_path)
        if result1.returncode == 0:
            result_arr = result1.stdout.splitlines()
            start_line = json_file['function_numbers']['function_start']
            end_line = json_file['function_numbers']['function_end']
            print('file_name is {}, start_line is {}, end_line is {}'.format(unzip_code_path, start_line, end_line))
            tmp = parse_getout_nearfunc_cpp.get_outfunc_and_nearfunc(unzip_code_path, 'cpp', start_line, end_line)
            for t in tmp:
                func_name = t.split('.')[-1]
                for i in range(len(result_arr)):
                    if result_arr[i].startswith('+-{}'.format(func_name)) and unzip_code_path in result_arr[i]:
                        callee_raw = list()
                        cnt = i
                        while True:
                            cnt += 1
                            if cnt == len(result_arr):
                                break
                            if result_arr[cnt].startswith('  '):
                                callee_raw.append(result_arr[cnt])
                            else:
                                break
                        for cr in callee_raw:
                            if_exists, func_abs_name, raw_code = parse_getout_nearfunc_cpp.get_code(cr)
                            if if_exists:
                                final_output_json['callee'][func_abs_name] = raw_code
                run_code1 = 'timeout 300 cflow -T -m {} -d 2 --omit-symbol-names $(find {}/{} -type f -name "*.cc") $(find {}/{} -type f -name "*.cpp")'.format(func_name, path_after, folder_name, path_after, folder_name)
                result2 = subprocess.run(run_code1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=dir_path)
                if result2.returncode == 0:
                    result_arr1 = result2.stdout.splitlines()
                    for i in range(len(result_arr1)):
                        if result_arr1[i].startswith('+-{}'.format(func_name)) and unzip_code_path in result_arr1[i]:
                            caller_raw = list()
                            cnt = i
                            while True:
                                cnt += 1
                                if cnt == len(result_arr1):
                                    break
                                if result_arr1[cnt].startswith('  '):
                                    caller_raw.append(result_arr1[cnt])
                                else:
                                    break
                            for cr in caller_raw:
                                if_exists, func_abs_name, raw_code = parse_getout_nearfunc_cpp.get_code(cr)
                                if if_exists:
                                    final_output_json['caller'][func_abs_name] = raw_code
    except Exception as e:
        print('Error reason: {}'.format(e))
        traceback.print_exc()
    with lock:
        with open('/new_data/Challenge/newest/output/output_cpp.jsonl', 'a') as w1:
            w1.write(json.dumps(final_output_json) + '\n')

with open('/new_data/Last/ReposVul_function_cpp.jsonl', 'r', encoding = "utf-8") as r:
    content = r.readlines()
with open('/new_data/Challenge/newest/output/output_cpp.jsonl', 'r', encoding = 'utf-8') as r1:
    new_content = r1.readlines()
new_list = list()
for new_line in new_content:
    json_file_new = json.loads(new_line)
    new_list.append(json_file_new['function_id'])
with multiprocessing.Manager() as manager:
    lock = manager.Lock()
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()//2) as executor:
        futures = [
            executor.submit(process_content, lock, line, new_list)
            for line in content
        ]
        for future in concurrent.futures.as_completed(futures):
            processed_line = future.result()