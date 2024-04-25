import os
import urllib.request
import json
from tqdm import tqdm
import jsonlines

outdated = 0
def merge_alldata(Year='2023', Month='1',index = 0, total = 0):
    global outdated
    YM = Year+'_'+Month
    CVEinfo_name = 'results/' + YM + '.jsonl'
    patch_name = 'crawl_result_last_add/' + YM + '_patch.jsonl'
    patcherr_name = 'crawl_result_error/' + YM + '_patch_error.txt'
    rawcode_name = 'rawcode_result_new/' + YM + '_rawcode.jsonl'
    mergefile_language = 'merge_result_new/language/merge_'
    mergefile_project = 'merge_result_new/project/merge_'
    mergefile_project_big = 'merge_result_new/project_big/merge_'
    mergefile_time = 'merge_result_new/time/merge_'

    os.makedirs('merge_result_new/language', exist_ok=True)
    os.makedirs('merge_result_new/project', exist_ok=True)
    os.makedirs('merge_result_new/project_big', exist_ok=True)
    os.makedirs('merge_result_new/time', exist_ok=True)

    if not os.path.exists(CVEinfo_name) or not os.path.exists(patch_name) or not os.path.exists(rawcode_name):
        return index, total

    CVEinfo = []
    with open(CVEinfo_name, "r", encoding = "utf-8") as rf:
        for line in rf:
            CVEinfo.append(json.loads(line))
    patches = []
    with open(patch_name, "r", encoding="utf-8") as f:
        patches = json.load(f)
    rawcode = []
    with open(rawcode_name, "r", encoding = "utf-8") as rfc:
        for line in rfc:
            rawcode.append(json.loads(line))

    patch_err = []
    with open(patcherr_name, "r", encoding = "utf-8") as rfc:
        for line in rfc:
            patch_err.append(line.replace('\n', ''))

    patch_id = 0
    CVEinfo_id = 0
    debug = 0
    while CVEinfo_id < len(CVEinfo) and patch_id < len(patches):
        for resource in CVEinfo[CVEinfo_id]['resources']:
            repo1 = (patches[patch_id]['html_url'].partition('github.com/')[2].partition('/commit'))[0]
            repo2 = (resource.partition('github.com/')[2].partition('/commit'))[0]

            url = resource.replace('/commit/', '/commits/').replace('https://github.com/', 'https://api.github.com/repos/')
            if 'commit' in resource and url not in patch_err and repo1.lower() == repo2.lower():
                merge_data = {} 
                merge_data['index'] = index
                merge_data['cve_id'] = CVEinfo[CVEinfo_id]['cve_id']
                merge_data['cwe_id'] = CVEinfo[CVEinfo_id]['CWEs']
                merge_data['cve_language'] = CVEinfo[CVEinfo_id]['language']
                merge_data['cve_description'] = CVEinfo[CVEinfo_id]['description']
                merge_data['cvss'] = CVEinfo[CVEinfo_id]['cvss']
                merge_data['publish_date'] = CVEinfo[CVEinfo_id]['date']
                merge_data['AV'] = CVEinfo[CVEinfo_id]['AV']
                merge_data['AC'] = CVEinfo[CVEinfo_id]['AC']
                merge_data['PR'] = CVEinfo[CVEinfo_id]['PR']
                merge_data['UI'] = CVEinfo[CVEinfo_id]['UI']
                merge_data['S'] = CVEinfo[CVEinfo_id]['S']
                merge_data['C'] = CVEinfo[CVEinfo_id]['C']
                merge_data['I'] = CVEinfo[CVEinfo_id]['I']
                merge_data['A'] = CVEinfo[CVEinfo_id]['A']

                merge_data['commit_id'] = patches[patch_id]['commit_id']
                merge_data['commit_message'] = patches[patch_id]['message']
                merge_data['commit_date'] = patches[patch_id]['commit_date']
                merge_data['project'] = repo1.lower()

                merge_data['url'] = patches[patch_id]['url']
                merge_data['html_url'] = patches[patch_id]['html_url']
                merge_data['windows_before'] = patches[patch_id]['windows_before']
                merge_data['windows_after'] = patches[patch_id]['windows_after']

                # try:
                merge_data['parents'] = patches[patch_id]['parents']
                # except:
                #     print('!!!')
                merge_data['details'] = []
                # 遍历当前patch_result的多个files
                for eachfile in patches[patch_id]['files']:
                    # 寻找当前file对应的多个rawcode_id
                    for rawcode_id in range(len(rawcode)):
                        if rawcode[rawcode_id]['patches_id'] == patch_id+1 and rawcode[rawcode_id]['raw_url'] == eachfile['raw_url']:
                            detail = {}
                            detail['raw_url'] = eachfile['raw_url']
                            detail['code'] = rawcode[rawcode_id]['raw_code']
                            detail['code_before'] = rawcode[rawcode_id]['raw_code_before']
                            detail['patch'] = eachfile['patch']
                            detail['file_path'] = rawcode[rawcode_id]['file_path']
                            detail['file_language'] = rawcode[rawcode_id]['language']
                            detail['file_name'] = eachfile['filename']
                            detail['outdated_file_modify'] = eachfile['outdated_file_modify']
                            detail['outdated_file_before'] = eachfile['outdated_file_before']
                            detail['outdated_file_after'] = eachfile['outdated_file_after']
                            merge_data['details'].append(detail)
                            total += 1

                if merge_data['details']:
                    merge_data['outdated'] = 0
                    for j in range(len(merge_data['details'])):
                        if merge_data['details'][j]['outdated_file_modify'] == 1 and (merge_data['details'][j]['outdated_file_before'] == 1 or merge_data['details'][j]['outdated_file_after'] == 1):
                            outdated += 1
                            merge_data['outdated'] = 1
                            break

                    merge_name = mergefile_language + merge_data['cve_language'] + '.jsonl'
                    with open(merge_name, 'a', encoding='utf-8') as f2:
                        jsonobj = json.dumps(merge_data)
                        f2.write(jsonobj+'\n')
                    merge_name = mergefile_project + merge_data['project'].replace('/','_') + '.jsonl'
                    with open(merge_name, 'a', encoding='utf-8') as f2:
                        jsonobj = json.dumps(merge_data)
                        f2.write(jsonobj + '\n')

                    merge_name = mergefile_time + YM + '.jsonl'
                    with open(merge_name, 'a', encoding='utf-8') as f2:
                        jsonobj = json.dumps(merge_data)
                        f2.write(jsonobj + '\n')

                    merge_name = mergefile_project_big + merge_data['project'].split('/')[1] + '.jsonl'
                    with open(merge_name, 'a', encoding='utf-8') as f2:
                        jsonobj = json.dumps(merge_data)
                        f2.write(jsonobj + '\n')
                    index += 1  # 写入一数据后再 增加index  
                patch_id += 1
                if patch_id >= len(patches):
                    break
        CVEinfo_id += 1

    return index,  total

def main():

    # Years = ['2018']
    # Months = ['1']

    Years = [str(year) for year in range(2001, 2024)]
    Months = [str(i) for i in range(1, 13)]

    index = 0
    total = 0
    for Year in Years:
        for Month in Months:
            index, total = merge_alldata(Year, Month, index, total)
            print(str(Year) + ' ' + str(Month) + ' ' + str(index) + ' ' + str(total))
    print('in total we merge '+str(index)+' commits')
    print('in total we merge '+str(total)+' rawcodes')
    print(outdated)

    

if __name__ == '__main__':
    main()
