from tree_sitter import Language, Parser
import json
import re
import subprocess
import os
import sys

# enter your path to execute the script
root_path = '/data/Static'
data_path = '/data/your_data_path'

def extract_addresses(input_str, after_real_path, language='py'):
    lines = input_str.strip().split('\n')
    result = []
    current_block = []
    skip_flag = False
    true_i = 0
    for i in range(len(lines)):
        if i != true_i:
            continue
        if lines[i].startswith(after_real_path):
            result.append(lines[i] + '\n' + lines[i+1])
            true_i = i + 2
        else:
            tmp = ''
            for j in range(i, len(lines)):
                if not lines[j].startswith(after_real_path):
                    if not tmp == '':
                        tmp += '\n'
                    tmp += lines[j]
                else:
                    true_i = j
                    break
            result.append(tmp)

    for i in range(len(result)):
        if result[i].startswith(after_real_path):
            for j in range(i+1,len(result)):
                if not result[j].startswith(after_real_path):
                    result[i] += '\n'
                    result[i] += result[j]
                    break
    result = [r for r in result if r.startswith(after_real_path)]
    return result

def extract_number_from_string(input_str, after_real_path, language='py'):
    pattern = f'{after_real_path}:(\d+)'
    match = re.match(pattern, input_str)

    if match:
        return match.group(1)
    else:
        return None

def func(language, file_name, write_name):  
    if language == 'c':
        language_choice = ['c', 'h']
    elif language == 'cpp':
        language_choice = ['cpp', 'h', 'cc']
    elif language == 'java':
        language_choice = ['java']
    elif language == 'python':
        language_choice = ['py']
    with open(file_name, "r",encoding = "utf-8") as r:
        content = r.readlines()
    for idx in range(len(content)):

        record_dict = json.loads(content[idx])
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
            real_path = '{}/{}'.format(data_path,file_path[6:]).replace('\\','/')
            after_real_path = f'{root_path}/tmp/{}.{}'.format(file_path[6:].replace('\\','_').replace('/','_'), file_language)
            if not os.path.exists(real_path):
                print('No path exists!')
                continue
            os.system(f'cp {real_path} {after_real_path}')
            if file_language == 'c' or file_language == 'cpp' or file_language == 'py' or file_language == 'h' or file_language == 'cc' or file_language == 'java':
                is_find = False
                find_message = list()
                cppcheck_command = f'rats --context --resultsonly {after_real_path}'
                cppcheck_result = subprocess.run(cppcheck_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
                os.system(f'rm -rf {after_real_path}')
                if cppcheck_result.returncode == 0:
                    error_message = cppcheck_result.stdout
                    print("Command output:\n", cppcheck_result.stdout)
                    if not error_message.strip() == '':
                        result_array = extract_addresses(error_message, after_real_path, file_language)
                        print(result_array)
                        for result in result_array:
                            print('------------------------')
                            print(result)
                            print(patch_old_line)
                            line_no = int(extract_number_from_string(result, after_real_path, file_language))
                            for i in range(len(patch_old_line)):
                                if line_no >= patch_old_line[i][0] and line_no < patch_old_line[i][0] + patch_old_line[i][1]:
                                    is_find = True
                                    find_message.append(result)
                                    print('find!!!!!')
                                    print(result)
                else:
                    print('Execute Error!!!!!!!!!!!')

                if 'static' not in details[idx1]:
                    details[idx1]['static'] = dict()
                if 'rats' not in details[idx1]['static']:
                    details[idx1]['static']['rats'] = list()
                details[idx1]['static']['rats'] = [is_find, find_message]

                record_dict['details'] = details

        if language == 'c':
            with open(write_name, "a", encoding = "utf-8") as rf:
                rf.write(json.dumps(record_dict)+'\n')
        elif language == 'cpp':
            with open(write_name, "a", encoding = "utf-8") as rf:
                rf.write(json.dumps(record_dict)+'\n')
        elif language == 'python':
            with open(write_name, "a", encoding = "utf-8") as rf:
                rf.write(json.dumps(record_dict)+'\n')
  
def main():
    
    language = "c"
    file_name = f'{root_path}/new_output/flawfinder_1/merge_C_new.jsonl' 
    write_name = f'{root_path}/new_output/rats_2/merge_C_new.jsonl'  
    func(language, file_name, write_name)
    
    language = "cpp"
    file_name = f'{root_path}/new_output/flawfinder_1/merge_C++_new.jsonl'  
    write_name = f'{root_path}/new_output/rats_2/merge_C++_new.jsonl'  
    func(language, file_name, write_name)

    # language = "java"
    # file_name = f'{root_path}/language/merge_Java.jsonl'  
    # write_name = f'{root_path}/language_new/merge_Java.jsonl'  
    # func(language, file_name, write_name)

    language = "python"
    file_name = f'{root_path}/language/merge_Python.jsonl' 
    write_name = f'{root_path}/new_output/rats_2/merge_Python_new.jsonl'  
    func(language, file_name, write_name)

if __name__ == "__main__":
    main()