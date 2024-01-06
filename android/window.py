import json
import time
import subprocess
import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import git
from itertools import groupby
import re
from datetime import datetime

def git_log(local_path, date, commit_id):


    command = f"git log --since='{date}' --reverse --pretty=format:\"%H - %ad : %s\" --name-only | head -n 200 > ../../windows/{commit_id}_after.txt"
    try:
        subprocess.run(command, cwd=local_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True, check=True)
        # print(response.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'git log': {e}")
        return None
    
    command = f"git log --before='{date}' --pretty=format:\"%H - %ad : %s\" --name-only | head -n 200 > ../../windows/{commit_id}_before.txt"
    try:
        subprocess.run(command, cwd=local_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'git log': {e}")
        return None

def find(filename, windows, num):
    for i in range(num):
        if i >= len(windows):
            return 0
        filenames = windows[i]['files_name']
        for each in filenames:
            if filename == each:
                return 1
    return 0


def get_alldate():
    Years = [str(year) for year in range(2001, 2024)]
    Months = [str(i) for i in range(1, 13)]
    dict_date = {}
    CVES = []

    for Year in Years:
        for Month in Months:
            YM = Year+'_'+Month
            print(YM)
            dir_path = 'merge_result/time_last/'
            res_filename = dir_path + YM + '.jsonl'
            if not os.path.exists(res_filename):
                continue
            
            with open(res_filename, "r", encoding = "utf-8") as rf:
                for line in rf:
                    CVES.append(json.loads(line))
    print(len(CVES))
    for i in range(len(CVES)):
        record = CVES[i]
        date = record['commit_date']
        if date == '':
            continue
        format_str = "%Y-%m-%d %H:%M:%S %z"
        date = datetime.strptime(date, format_str)
        for j in range(len(record['details'])):
            filename = record['details'][j]['file_name']
            if filename in dict_date:
                dict_date[filename] = max(dict_date[filename], date)
            else:
                dict_date[filename] = date

    return dict_date


def add_message(Year='2023', Month='1'):
 
    YM = Year+'_'+Month
    res_filename = 'merge_result/time/' + YM + '.jsonl'
    write_filename = 'merge_result/time_last/' + YM + '.jsonl'
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
            patch_index += 1
            file_index += len(CVE['details'])

            commit_id = CVE['commit_id']
            date = CVE['commit_date']
            path_before = './windows/' + commit_id + '_before.txt'
            path_after = './windows/' + commit_id + '_after.txt'

            if os.path.exists(path_before) and os.path.exists(path_after):
                with open(path_before, 'r', encoding='utf-8') as file:
                    content_before = file.read()
                    CVE['windows_before'] = content_before
                with open(path_after, 'r', encoding='utf-8') as file:
                    content_after = file.read() 
                    CVE['windows_after'] = content_after

            local_path = './repos_now/' + CVE['project']
            git_log(local_path, date, commit_id)

            if not os.path.exists(path_before):
                jsonobj = json.dumps(CVE)
                f.write(jsonobj + '\n')
                continue

            with open(path_before, 'r', encoding='utf-8') as file:
                content_before = file.read()
                CVE['windows_before'] = content_before

            if not os.path.exists(path_after):
                jsonobj = json.dumps(CVE)
                f.write(jsonobj + '\n')
                continue

            with open(path_after, 'r', encoding='utf-8') as file:
                content_after = file.read() 
                CVE['windows_after'] = content_after

            windows_before = CVE['windows_before']
            windows_after = CVE['windows_after']
            
            windows_before_split = windows_before.split('\n')
            windows_after_split = windows_after.split('\n')
            
            commit_id_now = commit_id
            windows = []
            groups = [list(group) for key, group in groupby(windows_before_split, key=lambda x: x == '') if not key]
            for group in groups:
                window = {}
                commit_detail = group[0]
                pattern = re.compile(r'(?P<id>[a-f0-9]+) - (?P<date>.*?) : (?P<message>.*)')
                match = pattern.match(commit_detail)
                commit_id = match.group('id')
                if str(commit_id.strip()) == str(commit_id_now.strip()):
                    continue
                commit_date = match.group('date')
                commit_message = match.group('message')
                group.pop(0)
                window['commit_id'] = commit_id
                window['commit_date'] = commit_date
                window['commit_message'] = commit_message
                window['files_name'] = group
                windows.append(window)
            CVE['windows_before'] = windows

            windows = []    
            groups = [list(group) for key, group in groupby(windows_after_split, key=lambda x: x == '') if not key]
            for group in groups:
                window = {}
                commit_detail = group[0]
                pattern = re.compile(r'(?P<id>[a-f0-9]+) - (?P<date>.*?) : (?P<message>.*)')
                match = pattern.match(commit_detail)
                commit_id = match.group('id')
                if str(commit_id.strip()) == str(commit_id_now.strip()):
                    continue
                commit_date = match.group('date')
                commit_message = match.group('message')
                group.pop(0)
                window['commit_id'] = commit_id
                window['commit_date'] = commit_date
                window['commit_message'] = commit_message
                window['files_name'] = group
                windows.append(window)
            CVE['windows_after'] = windows
            
            windows_before = CVE['windows_before']
            windows_after = CVE['windows_after']
            for j in range(len(CVE['details'])):
                file_name = CVE['details'][j]['file_name']
                CVE['details'][j]['outdated_file_before'] = find(file_name, windows_before, 3)
                CVE['details'][j]['outdated_file_after'] = find(file_name, windows_after, 3)

            jsonobj = json.dumps(CVE)
            f.write(jsonobj + '\n')

    return patch_index, file_index

def add_message_new(Year, Month, dict_date):

    YM = Year+'_'+Month
    print(YM)

    res_filename = 'merge_result/time_last/' + YM + '.jsonl'
    write_filename = 'merge_result/time_last/' + YM + '.jsonl'

    if not os.path.exists(write_filename):
        return 0, 0

    patch_index = 0
    file_index = 0

    CVES = []
    with open(res_filename, "r", encoding = "utf-8") as rf:
        for line in rf:
            CVES.append(json.loads(line))

    with open(write_filename, "w", encoding="utf-8") as f:
        for CVE in CVES:
            patch_index += 1
            file_index += len(CVE['details'])
            date = CVE['commit_date']
            if date == '':
                jsonobj = json.dumps(CVE)
                f.write(jsonobj + '\n')
                continue
            format_str = "%Y-%m-%d %H:%M:%S %z"
            date = datetime.strptime(date, format_str)

            for j in range(len(CVE['details'])):
                filename = CVE['details'][j]['file_name']
                if filename not in dict_date:
                    CVE['details'][j]['outdated_file_modify'] = 0
                elif date < dict_date[filename]:
                    CVE['details'][j]['outdated_file_modify'] = 1
                else:
                    CVE['details'][j]['outdated_file_modify'] = 0
            jsonobj = json.dumps(CVE)
            f.write(jsonobj + '\n')

    return patch_index, file_index

outdated = 0
def add_message_last(Year, Month):
    global outdated
    YM = Year+'_'+Month
    print(YM)

    res_filename = 'merge_result/time_last/' + YM + '.jsonl'
    write_filename = 'merge_result/time_last/' + YM + '.jsonl'

    if not os.path.exists(write_filename):
        return 0, 0

    patch_index = 0
    file_index = 0

    CVES = []
    with open(res_filename, "r", encoding = "utf-8") as rf:
        for line in rf:
            CVES.append(json.loads(line))

    with open(write_filename, "w", encoding="utf-8") as f:
        for CVE in CVES:
            patch_index += 1
            file_index += len(CVE['details'])

            CVE['outdated'] = 0
            for j in range(len(CVE['details'])):
                if CVE['details'][j]['outdated_file_modify'] == 1 and (CVE['details'][j]['outdated_file_before'] == 1 or CVE['details'][j]['outdated_file_after'] == 1):
                    outdated += 1
                    CVE['outdated'] = 1
                    break
                
            jsonobj = json.dumps(CVE)
            f.write(jsonobj + '\n')

    return patch_index, file_index

def main():


    Years = [str(year) for year in range(2001, 2024)]
    print(Years)
    
    Months = [str(month) for month in range(1, 13)]
    print(Months)

    # Years = ['2020']
    # Months = ['2']

    patch_index = 0
    file_index = 0
    # for Year in Years:
    #     for Month in Months:
    #         patch_index_add, file_index_add = add_message(Year, Month)
    #         patch_index += patch_index_add
    #         file_index += file_index_add
    #         print('****************************')
    #         print(Year + Month)
    #         print(patch_index)
    #         print(file_index)


    # dict_date = get_alldate()
    # Years = [str(year) for year in range(2001, 2024)]
    # Months = [str(i) for i in range(1, 13)]
    # patch_index = 0
    # file_index = 0
    # for Year in Years:
    #     for Month in Months:
    #         patch_index_add, file_index_add = add_message_new(Year, Month, dict_date)
    #         patch_index += patch_index_add
    #         file_index += file_index_add
    #         print('****************************')
    #         print(patch_index)
    #         print(file_index)

    global outdated
    for Year in Years:
        for Month in Months:
            patch_index_add, file_index_add = add_message_last(Year, Month)
            patch_index += patch_index_add
            file_index += file_index_add
    print(outdated)
if __name__ == '__main__':
    main()