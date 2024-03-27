import os
import json
import subprocess
import zipfile
import sys
import re
import concurrent.futures
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import parse_getout_nearfunc_c_plus
import traceback

with open('/new_data/Last/ReposVul_function_c.jsonl', 'r', encoding = "utf-8") as r:
    content = r.readlines()
changed_content = list()
for i in content:
    json_line_1 = json.loads(i)
    if not 'line_numbers' in json_line_1:
        continue
    if_break = False
    for j in range(len(json_line_1['line_numbers'])):
        if 'line_change' in json_line_1['line_numbers'][j]:
            if_break = True
            break
    if if_break:
        changed_content.append(i)

def process_content(lock, line, new_list):
    try:
        json_file = json.loads(line)
        if json_file['function_id'] in new_list:
            return
        print('begin')
        function_id = json_file['function_id']
        final_output_json = dict()
        final_output_json['function_id'] = function_id
        final_output_json['caller'] = json_file['caller']
        final_output_json['callee'] = json_file['callee']
        final_output_json['caller_of_change'] = dict()
        final_output_json['callee_of_change'] = dict()
        if len(json_file['caller']) == 0 and len(json_file['callee']) == 0:
            print('all zero-{}'.format(function_id))
            with lock:
                with open('/new_data/Challenge/newest/output/output_c_final.jsonl', 'a') as w1:
                    w1.write(json.dumps(final_output_json) + '\n')
            return
        pre_json_line = dict()
        for i in content:
            json_line = json.loads(i)
            if json_line['function_id'] == function_id:
                pre_json_line = json_line
                break
        file_name = pre_json_line['file_name']
        if len(json_file['caller']) > 0:
            print('caller activate {}'.format(function_id))
            publish_date = pre_json_line['file_path'].replace('\\', '/').split('/')[1]
            commit_id = pre_json_line['parents'][0]['commit_id_before']
            path_before = '/new_data/Challenge/REEF-scripit-own/repos_before/{}/{}.zip'.format(publish_date, commit_id)
            if pre_json_line['file_target'] == '-1':
                return
            with zipfile.ZipFile(path_before, 'r') as zip_ref:
                contents = zip_ref.namelist()
            folder_name = contents[0][:-1]
            path_after = '/new_data/Challenge/unzip_tmp'
            print(folder_name)
            unzip_code_path = '{}/{}/{}'.format(path_after, folder_name, file_name)
            print(unzip_code_path)
            if 'line_numbers' in pre_json_line:
                for i in range(len(pre_json_line['line_numbers'])):
                    line_start = int(pre_json_line['line_numbers'][i]['line_start'])
                    line_end = int(pre_json_line['line_numbers'][i]['line_end'])
                    print('line_start is {}, line_end is {}'.format(line_start, line_end))
                    print('json_file["caller"] is {}'.format(json_file['caller']))
                    final_output_json['caller_of_change'].update(parse_getout_nearfunc_c_plus.choose_caller(unzip_code_path, line_start, line_end, json_file['caller']))
                print('final_output_json["caller_of_change"] is {}'.format(final_output_json['caller_of_change']))
                if len(final_output_json['caller_of_change']) > 0:
                    print('caller has at least 1.')
        if len(json_file['callee']) > 0:
            print('callee activate {}'.format(function_id))
            callee_len = len(json_file['callee'])
            # for i in content:
            #     if i in new_list:
            #         continue
            #     if callee_len == 0:
            #         break
            #     json_line_1 = json.loads(i)
            #     if not 'line_numbers' in json_line_1:
            #         continue
            #     if_break = False
            for cc in changed_content:
                if callee_len == 0:
                    break
                json_line_1 = json.loads(cc)
                if not json_file['function_id'].startswith(json_line_1['commit_id']):
                    continue
                print('function_id is {} and commit_id is {}'.format(json_file['function_id'], json_line_1['commit_id']))
                file_name_1 = json_line_1['file_name']
                func_name = parse_getout_nearfunc_c_plus.get_func_name_from_code(json_line_1['function'])
                if func_name is None:
                    continue
                func_abs_name = '.'.join(file_name.replace('/', '.').split('.')[:-1]) + '.' + func_name
                print('func_abs_name = {}'.format(func_abs_name))
                if not func_abs_name in json_file['callee']:
                    continue
                final_output_json['callee_of_change'][func_abs_name] = json_file['callee'][func_abs_name]
                callee_len -= 1
            print('final_output_json["callee_of_change"] is {}'.format(final_output_json['callee_of_change']))
            if len(final_output_json['callee_of_change']) > 0:
                print('callee has at least 1.')
    except Exception as e:
        print('Error:{}'.format(e))
        traceback.print_exc()

    with lock:
        with open('/new_data/Challenge/newest/output/output_c_final.jsonl', 'a') as w1:
            w1.write(json.dumps(final_output_json) + '\n')


with open('/new_data/Challenge/newest/output/output_c.jsonl', 'r', encoding = 'utf-8') as r1:
    new_content = r1.readlines()
with open('/new_data/Challenge/newest/output/output_c_final.jsonl', 'r', encoding = 'utf-8') as r2:
    output_json = r2.readlines()
new_list = list()
for new_line in output_json:
    json_file_new = json.loads(new_line)
    new_list.append(json_file_new['function_id'])
with multiprocessing.Manager() as manager:
    lock = manager.Lock()
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()//2) as executor:
        futures = [
            executor.submit(process_content, lock, line, new_list)
            for line in new_content
        ]
        for future in concurrent.futures.as_completed(futures):
            processed_line = future.result()
