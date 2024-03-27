import os
import json
import subprocess
import zipfile
import sys
import re
import concurrent.futures
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import ast
import parse_getout_nearfunc_python
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
    start_line = json_file['function_numbers']['function_start']
    end_line = json_file['function_numbers']['function_end']
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
        run_code = 'find {}/{} -type f -name "*.py"'.format(path_after, folder_name)
        result = subprocess.run(run_code, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        py_file = result.stdout.splitlines()
        py3_file = list()
        for pf in py_file:
            if '.' in pf[:-3]:
                continue
            try:
                with open(pf, 'r') as r1:
                    pf_text = r1.read()
                try:
                    ast.parse(pf_text)
                    py3_file.append(pf)
                except:
                    print('python 2 file-{}'.format(pf))
            except:
                pass
        print('{}-{}'.format(folder_name, ' '.join(py3_file)))
        dir_path = '{}/{}'.format(path_after, folder_name)
        run_code1 = 'timeout 300 pycg --max-iter 1 {}'.format(unzip_code_path)
        result1 = subprocess.run(run_code1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=dir_path)
        if result1.returncode == 0:
            print('OJBK-{}-{}'.format(folder_name, result1.stdout))
            output_json = json.loads(result1.stdout)
            print('output_json is {}'.format(output_json))
            func_name = list()
            print('file_name is {}, start_line is {}, end_line is {}'.format(unzip_code_path, start_line, end_line))
            tmp = parse_getout_nearfunc_python.get_outfunc_and_nearfunc(unzip_code_path, 'python', start_line, end_line)
            for t in tmp:
                if t not in func_name:
                    func_name.append(t)
            for func in func_name:
                if func in output_json:
                    print('output is {}'.format(output_json[func]))
                    for output_json_func in output_json[func]:
                        if_exists, res_code = parse_getout_nearfunc_python.get_code(unzip_code_path, output_json_func)
                        if if_exists:
                            final_output_json['caller'][output_json_func] = res_code
                else:
                    print('output does not include {}'.format(func))
                callee = list()
                for py3 in py3_file:
                    run_code2 = 'timeout 180 pycg --max-iter 1 {}'.format(py3)
                    result2 = subprocess.run(run_code2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=dir_path)
                    if result2.returncode == 0:
                        output_json2 = json.loads(result2.stdout)
                        for oj in output_json2:
                            if func in output_json2[oj]:
                                callee.append(oj)
                                break
                callee = list(set(callee))
                print('output callee of {} is {}'.format(func, callee))
                for cl in callee:
                    if_exists, res_code = parse_getout_nearfunc_python.get_code(unzip_code_path, cl)
                    if if_exists:
                        final_output_json['callee'][cl] = res_code
        else:
            print('pycg error!!!!-{}'.format(folder_name))
            print('run_code1 of {} is {}'.format(folder_name, run_code1))
    except Exception as e:
        print('Error reason: {}'.format(e))
        traceback.print_exc()
    with lock:
        with open('/new_data/Challenge/newest/output/output_python.jsonl', 'a') as w1:
            w1.write(json.dumps(final_output_json) + '\n')

        
with open('/new_data/Last/ReposVul_function_python.jsonl', "r",encoding = "utf-8") as r:
    content = r.readlines()
with open('/new_data/Challenge/newest/output/output_python.jsonl', 'r', encoding = 'utf-8') as r1:
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