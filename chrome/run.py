import json
import time
import subprocess
import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import git
cnt = 0
def cve_info(CVE, index):
    merge_data = {}
    merge_data['index'] = index
    merge_data['cve_id'] = CVE['cve_id']
    merge_data['cwe_id'] = CVE['CWEs']
    merge_data['cve_language'] = CVE['language']
    merge_data['cve_description'] = CVE['description']
    merge_data['cvss'] = CVE['cvss']
    merge_data['publish_date'] = CVE['date']
    merge_data['AV'] = CVE['AV']
    merge_data['AC'] = CVE['AV']
    merge_data['PR'] = CVE['PR']
    merge_data['UI'] = CVE['UI']
    merge_data['S'] = CVE['S']
    merge_data['C'] = CVE['C']
    merge_data['I'] = CVE['I']
    merge_data['A'] = CVE['A']
    return merge_data

def fetch(Year='2023', Month='1'):
    global cnt
    YM = Year+'_'+Month
    res_filename = 'merge_result/time_commit/' + YM + '.jsonl'
    write_filename = 'merge_result/time/' + YM + '.jsonl'
    if not os.path.exists(res_filename):
        return 0, 0

    patch_index = 0
    file_index = 0
    CVES = []
    with open(res_filename, "r", encoding = "utf-8") as rf:
        for line in rf:
            CVES.append(json.loads(line))

    with open(write_filename, 'w', encoding='utf-8') as f:
        for CVE in CVES:
            # for resource in CVE['resources']:
            #     if "http://code.google.com/p/chromium/issues/detail?id=" in resource:
                    
            #         merge_data = cve_info(CVE, patch_index)
            #         local_path = './repos_now'
          
            #         detail_id = resource.partition('http://code.google.com/p/chromium/issues/detail?id=')[2]
            #         pattern = f"BUG={detail_id}" + '\\b\|' + f"Bug={detail_id}" + '\\b\|' + f"bug={detail_id}" + '\\b\|' + \
            #                   f"BUG:{detail_id}" + '\\b\|' + f"Bug:{detail_id}" + '\\b\|' + f"bug:{detail_id}" + '\\b\|' + \
            #                   f"BUG = {detail_id}" + '\\b\|' + f"Bug = {detail_id}" + '\\b\|' + f"\bbug = {detail_id}" + '\\b\|' + \
            #                   f"BUG: {detail_id}" + '\\b\|' + f"Bug: {detail_id}" + '\\b\|' + f"bug: {detail_id}"

            #         try:
            #             command = ['git', 'log', f'--grep={pattern}', '--format=%H']
            #             commit_ids = subprocess.check_output(command, cwd=local_path, universal_newlines=True, errors='ignore').splitlines()
            #             print(commit_ids)
            #         except subprocess.CalledProcessError as e:
            #             print(e)
            #             continue

            #         for commit_id in commit_ids:

            #             merge_data['commit_id'] = commit_id
            #             merge_data['url'] = ''
            #             merge_data['html_url'] = resource
            #             merge_data['project'] = 'Chrome'
            #             cnt += 1

            merge_data = CVE
            commit_id = merge_data['commit_id']
            local_path = './repos_now'

            try:
                # 获取提交日期
                date_command = ['git', 'show', '-s', '--format=%ci', commit_id]
                commit_date = subprocess.check_output(date_command, cwd=local_path, universal_newlines=True, errors='ignore').strip()
                merge_data['commit_date'] = commit_date
            except subprocess.CalledProcessError as e:
                print(f"Error executing Git command: {e}")
                merge_data['commit_date'] = ''

            try:
                # 获取提交信息
                message_command = ['git', 'show', '-s', '--format=%B', commit_id]
                commit_message = subprocess.check_output(message_command, cwd=local_path, universal_newlines=True, errors='ignore').strip()
                merge_data['commit_message'] = commit_message
            except subprocess.CalledProcessError as e:
                print(f"Error executing Git command: {e}")
                merge_data['commit_message'] = ''

            merge_data['parents'] = []
            try:
                # 获取父亲信息
                parent_command = ['git', 'show', '-s', '--format=%P', commit_id]
                parent_result = subprocess.check_output(parent_command, universal_newlines=True, cwd=local_path, errors='ignore').strip()
                for parent_id in parent_result.split():
                    parent = {}
                    parent['commit_id_before'] = parent_id
                    parent['url_before'] = ''
                    parent['html_url_before'] = ''
                    merge_data['parents'].append(parent)
                
            except subprocess.CalledProcessError as e:
                print(f"Error executing Git command: {e}")
            
            merge_data['details'] = []
            try:
                # 使用subprocess执行git命令
                result = subprocess.run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_id], cwd=local_path, capture_output=True, text=True, check=True, errors='ignore')
                # 解析结果，获取修改的文件列表
                modified_files = result.stdout.splitlines()

                detail = {}
                for modified_file in modified_files:
                    detail['raw_url'] = ''
                    detail['file_name'] = modified_file
                    detail['file_language'] = modified_file.split('.')[-1]
                    merge_data['details'].append(detail)                    

            except subprocess.CalledProcessError as e:
                print(f"Error executing Git command: {e}")
                

            for idx, detail in enumerate(merge_data['details']):
                try:
                    # 使用subprocess执行git命令
                    file_name = detail['file_name']
                    result = subprocess.run(['git', 'show', f'{commit_id}^:{file_name}'], cwd=local_path, capture_output=True, text=True, check=True, errors='ignore')
                    file_index += 1
                    # 获取文件内容
                    code = result.stdout
                    merge_data['details'][idx]['code'] = code
                    dir_path = "files/" + YM
                    os.makedirs(dir_path, exist_ok=True)
                    file_path =  os.path.join(dir_path, str(file_index))
                    merge_data['details'][idx]['file_path'] = file_path

                    with open(file_path, 'w') as file:
                        file.write(code)

                except subprocess.CalledProcessError as e:
                    print(f"Error executing git command: {e}")

            for idx,detail in enumerate(merge_data['details']):
                try:
                    # 使用subprocess执行git命令
                    file_name = detail['file_name']
                    result = subprocess.run(['git', 'show', f'{commit_id}^:{file_name}'], cwd=local_path, capture_output=True, text=True, check=True, errors='ignore')

                    # 获取文件内容
                    code_before = result.stdout
                    merge_data['details'][idx]['code_before'] = code_before
                    dir_path = "files_before/" + YM
                    os.makedirs(dir_path, exist_ok=True)
                    try:
                        file_id = detail['file_path'].split('/')[2]
                    except:
                        file_id = detail['file_path'].split('/')[1].split('\\')[1]
                    file_path =  os.path.join(dir_path, str(file_id))
                    with open(file_path, 'w') as file:
                        file.write(code_before)

                except subprocess.CalledProcessError as e:
                    print(f"Error executing git command: {e}")

            for idx,detail in enumerate(merge_data['details']):
                try:
                    # 使用subprocess执行git命令
                    file_name = detail['file_name']
                    result = subprocess.run(['git', 'diff', f'{commit_id}^', commit_id, '--', file_name], cwd=local_path, capture_output=True, text=True, check=True, errors='ignore')
                    # 获取文件差异内容
                    patch = result.stdout
                    merge_data['details'][idx]['patch'] = patch

                except subprocess.CalledProcessError as e:
                    print(f"Error executing git command: {e}")

            patch_index += 1
        
            jsonobj = json.dumps(merge_data)
            f.write(jsonobj + '\n')
        
    return patch_index, file_index


def main():


    Years = [str(year) for year in range(2001, 2024)]
    print(Years)
    
    Months = [str(month) for month in range(1, 13)]
    print(Months)

    patch_index = 0
    file_index = 0
    global cnt
    for Year in Years:
        for Month in Months:
            patch_index_add, file_index_add = fetch(Year, Month)
            patch_index += patch_index_add
            file_index += file_index_add
            print(patch_index)


if __name__ == '__main__':
    main()