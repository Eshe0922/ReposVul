from tree_sitter import Language, Parser
import json
import re
import subprocess
import os
import sys
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import multiprocessing

# enter your path to execute the script
root_path = '/data/Static'
data_path = '/data/your_data_path'

def extract_addresses(input_string, file_path):
    result = re.split(f'(?={root_path}/tmp/{file_path[6:].replace("/","_")}(?:\.c|\.cpp|\.h):\d+)', input_string)
    result = [s for s in result if '{root_path}/tmp/' in s]
    return result


def extract_number_from_string(input_string, file_path):
    match = re.search(f'{root_path}/tmp/{file_path[6:].replace("/","_")}\.(c|h|cpp):(\d+):', input_string)

    if match:
        return match.group(2)
    else:
        return None

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function timed out")

def process_content(lock, language, file_name, write_name, idx, content_line):
    if language == 'c':
        language_choice = ['c', 'h']
    elif language == 'cpp':
        language_choice = ['cpp', 'h', 'cc']
    elif language == 'java':
        language_choice = ['java']
    elif language == 'python':
        language_choice = ['py']
    record_dict = json.loads(content_line)
    details = record_dict['details']
    for idx1, detail in enumerate(details):
        if not detail['file_language'].lower().strip() in language_choice:
            continue
        code = detail['code']
        code_before = detail['code_before']
        file_path = detail['file_path']
        file_language = detail['file_language']
        patch = detail['patch']

        pattern = re.compile(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')
        matches = pattern.findall(patch)
        
        patch_old_line = []
        for match in matches:
            old_start, old_lines, new_start, new_lines = int(match[0]), match[1], int(match[2]), match[3]
            if old_lines == '':
                old_lines = 0
            else:
                old_lines = int(old_lines)

            if new_lines == '':
                new_lines = 0
            else:
                new_lines = int(new_lines)
            patch_old_line.append([old_start, old_lines])
        real_path = '{}/{}'.format(data_path, file_path[6:]).replace('\\','/')
        after_real_path = f'{root_path}/tmp/{}.{}'.format(file_path[6:].replace('\\','_').replace('/','_'), file_language)
        if not os.path.exists(real_path):
            print('No path exists!')
            continue
        os.system(f'cp {real_path} {after_real_path}')
        if file_language == 'py' or file_language == 'java' or file_language == 'c' or file_language == 'cc' or file_language == 'cpp' or file_language == 'h':
            is_find = False
            find_message = list()
            cppcheck_command = f'timeout 10800s cppcheck --force {after_real_path}'
            cppcheck_result = subprocess.run(cppcheck_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
            os.system(f'rm -rf {after_real_path}')
            try:
                if cppcheck_result.returncode == 0:
                    error_message = cppcheck_result.stderr
                    print("Command output:\n", cppcheck_result.stdout)
                    print("error output:\n", cppcheck_result.stderr)
                    if not error_message.strip() == '':
                        result_array = extract_addresses(error_message, file_path)
                        print(result_array)
                        for result in result_array:
                            print('------------------------')
                            print(result)
                            print(patch_old_line)
                            line_no = int(extract_number_from_string(result, file_path))
                            for i in range(len(patch_old_line)):
                                if line_no >= patch_old_line[i][0] and line_no < patch_old_line[i][0] + patch_old_line[i][1]:
                                    is_find = True
                                    find_message.append(result)
                                    print('find!!!!!')
                                    print(result)
                else:
                    print('Execute Error!!!!!!!!!!!')
                    is_find = False
                    find_message = []
            except:
                print('Unkown Error!!!!')
                            
            if 'static' not in details[idx1]:
                details[idx1]['static'] = dict()
            if 'cppcheck' not in details[idx1]['static']:
                details[idx1]['static']['cppcheck'] = list()
            details[idx1]['static']['cppcheck'] = [is_find, find_message]

            record_dict['details'] = details
    with lock:
        with open(write_name, "a", encoding = "utf-8") as rf:
            rf.write(json.dumps(record_dict)+'\n')

def func(language, file_name, write_name):  
    with open(file_name, "r",encoding = "utf-8") as r:
        content = r.readlines()
    with multiprocessing.Manager() as manager:
        lock = manager.Lock()
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [
                executor.submit(process_content, lock, language, file_name, write_name, idx, content_line)
                for idx, content_line in enumerate(content)
            ]
            for future in concurrent.futures.as_completed(futures):
                processed_line = future.result()


  
def main():
    
    language = "c"
    file_name = f'{root_path}/new_output/semgrep_3/merge_C_new.jsonl' 
    write_name = f'{root_path}/new_output/cppcheck_4/merge_C_new.jsonl'  
    func(language, file_name, write_name)
    
    language = "cpp"
    file_name = f'{root_path}/new_output/semgrep_3/merge_C++_new.jsonl'  
    write_name = f'{root_path}/new_output/cppcheck_4/merge_C++_new.jsonl'  
    func(language, file_name, write_name)

    # language = "java"
    # file_name = f'{root_path}/language/merge_Java.jsonl'  
    # write_name = f'{root_path}/language_semgrep_3/merge_Java_new.jsonl'  
    # func(language, file_name, write_name)

    # language = "python"
    # file_name = f'{root_path}/language_rats_2/merge_Python_new.jsonl' 
    # write_name = f'{root_path}/language_semgrep_3/merge_Python_new.jsonl'  
    # func(language, file_name, write_name)

if __name__ == "__main__":
    main()