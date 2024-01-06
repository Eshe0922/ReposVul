from bs4 import BeautifulSoup
import re
import os
import json
import time
import random
from urllib.request import Request, urlopen
import sys
import ssl
import subprocess
from tqdm import tqdm

def step_one(Year, Month):
    YM = Year + '_' + Month
    filename = 'logs/' + YM + '.log'
    res_filename = 'results/' + YM + '.jsonl'

    if not os.path.exists(filename):

        url = "https://www.mend.io/vulnerability-database/full-listing/"+Year+"/"+Month 
        soup = BeautifulSoup(urlopen(Request(url,
                             headers={'User-Agent': 'Mozilla/5.0'})).read(),
                             'html.parser')

        links = []
        try:
            max_pagenumber = int(soup.find_all("li", class_="vuln-pagination-item")[-2].text.strip())
        except Exception as e:
            max_pagenumber = 1

        for link in soup.find_all("a", href=re.compile("^/vulnerability-database/CVE")):
            name = link.text
            href = link.get("href")
            links.append((name, href))
        if max_pagenumber > 1:
            for i in range(2,max_pagenumber+1):

                url = "https://www.mend.io/vulnerability-database/full-listing/"+Year+"/"+ Month + '/'+str(i)
                soup = BeautifulSoup(urlopen(Request(url,
                             headers={'User-Agent': 'Mozilla/5.0'})).read(),
                             'html.parser')
                for link in soup.find_all("a", href=re.compile("^/vulnerability-database/CVE")):
                    name = link.text
                    href = link.get("href")
                    links.append((name, href))

        with open(filename,'w') as f:
            for name, href in links:
                f.write(href+'\n')

    with open(filename,'r') as f:
        content = f.readlines()
    prefix = 'https://www.mend.io'

    max_num = 1  

    already_query_qid = 0
    if os.path.exists(res_filename):
        with open(res_filename, 'r', encoding='utf-8') as f2:
            queried = f2.readlines()
            already_query_qid = json.loads(queried[-1])["q_id"] if len(queried) != 0 else 0
            print('already query {}'.format(already_query_qid))

    for i in range(len(content)):
        try:
            random_time = random.uniform(0.1, 1)
            one_res = {"q_id":i ,"cve_id": content[i].strip().split('/')[-1], "language":None, "date":None, "resources": [], "CWEs": [] ,"cvss": None, "description":None, "AV":None, "AC":None, "PR":None, "UI":None, "S":None, "C":None, "I":None, "A":None}
            if i <= already_query_qid:
                continue

            fullweb_url = prefix + content[i].strip()
            soup = BeautifulSoup(urlopen(Request(fullweb_url,
                             headers={'User-Agent': 'Mozilla/5.0'})).read(),
                             'html.parser')

            for tag in soup.find_all(["h4"]):
                if tag.name == "h4":
                    if "Date:" in tag.text:
                        date = tag.text.strip().replace("Date:", "").strip()

                    elif "Language:" in tag.text:
                        language = tag.text.strip().replace("Language:", "").strip()
            
            div = soup.find("div", class_="single-vuln-desc no-good-to-know")
            if div:
                desc = div.find("p")
                description = desc.text.strip()
                one_res["description"] = description
            
            div = soup.find("div", class_="single-vuln-desc")
            if div:
                desc = div.find("p")
                description = desc.text.strip()
                one_res["description"] = description

            one_res["date"] =  date
            one_res["language"] =  language

            reference_links = []
            for div in soup.find_all("div", class_="reference-row"):
                for link in div.find_all("a", href=True):
                    reference_links.append(link["href"])
            one_res["resources"] =  reference_links

            severity_score = ""
            div = soup.find("div", class_="ranger-value")
            if div:
                label = div.find("label")
                if label:
                    severity_score = label.text.strip()
            one_res["cvss"] =  severity_score

            table = soup.find("table", class_="table table-report")
            if table:
                for tr in table.find_all("tr"):
                    th = tr.find('th').text.strip()
                    td = tr.find('td').text.strip()
                    if "Attack Vector" in th:
                        one_res["AV"] = td
                    elif "Attack Complexity" in th:
                        one_res["AC"] = td
                    elif "Privileges Required" in th:
                        one_res["PR"] = td
                    elif "User Interaction" in th:
                        one_res["UI"] = td
                    elif "Scope" in th:
                        one_res["S"] = td
                    elif "Confidentiality" in th:
                        one_res["C"] = td
                    elif "Integrity" in th:
                        one_res["I"] = td
                    elif "Availability" in th:
                        one_res["A"] = td

            if div:
                label = div.find("label")
                if label:
                    severity_score = label.text.strip()
            one_res["cvss"] =  severity_score

            cwe_numbers = []
            for div in soup.find_all("div", class_="light-box"):
                for link in div.find_all("a", href=True):
                    if "CWE" in link.text:
                        cwe_numbers.append( link.text)
            one_res["CWEs"] =  cwe_numbers

            if (one_res["cve_id"] is not None) and (one_res["language"] is not None) and (one_res["date"] is not None) and ( \
                    one_res["resources"] != []) and (one_res["CWEs"] != []) and (one_res["cvss"] is not None):
                print("correct! all info is done for case", content[i])
                with open(res_filename, 'a', encoding='utf-8') as f2:
                    jsonobj = json.dumps(one_res)
                    f2.write(jsonobj + '\n')
            else:
                if one_res["resources"] == []:
                    print('no source ,therefore give it up ',content[i])
                else:
                    print("Wrong! At least one item in one_res is empty, see case ",content[i])
        except Exception as e:
            print(e)

def step_two(Year, Month):
    
    YM = Year+'_'+Month
    res_filename = 'results/' + YM + '.jsonl'
    patch_name = 'crawl_result/' + YM + '_patch.jsonl'
    error_file = 'crawl_result/' + YM + '_patch_error.txt'

    if not os.path.exists(res_filename):
        return

    CVES = [json.loads(line) for line in open(res_filename, "r",encoding = "utf-8")]
    querys = []
    fetchs = []
    for CVE in CVES:
        for res in CVE['resources']:
            if "commit" in res and "github" in res:
                querys.append(res.replace('/commit/', '/commits/').replace('https://github.com/', 'https://api.github.com/repos/'))
    try:
        total = len(querys)
        i = 0
        errors = []
        for query in querys:
            i += 1
            data = {}
            try:
                output = bytes.decode(subprocess.check_output(["curl", "--request", "GET" ,"-H", "Authorization: Bearer TODO", "-H", "X-GitHub-Api-Version: 2022-11-28", "-u", "KEY:", query]))
                data = json.loads(output)
            except Exception as e:
                print(e)
                continue
            if 'url' in data and 'html_url' in data and 'commit' in data and 'files' in data:    
                fetchs.append({
                    'url': data['url'],
                    'html_url': data['html_url'],
                    'message': data['commit']['message'], 
                    'files': data['files'],
                    'commit_id': data['sha'],
                    'commit_date': data['commit']['committer']['date']
                })
            else:
                print("Wrong! Data is NULL, see case ", query)
                print(data)
                errors.append(query)    
            time.sleep(1)
    except Exception:
        with open(patch_name, "w", encoding = "utf-8") as rf:
            rf.write(json.dumps(fetchs, sort_keys=True, indent=4, separators=(',', ': ')))
    except KeyboardInterrupt:
        with open(patch_name, "w", encoding = "utf-8") as rf:
            rf.write(json.dumps(fetchs, sort_keys=True, indent=4, separators=(',', ': ')))
    
    with open(patch_name, "w", encoding = "utf-8") as rf:
        rf.write(json.dumps(fetchs, indent=4, separators=(',', ': ')))
    with open(error_file, "w", encoding = "utf-8") as rf:
        for err in errors:
            rf.write(err+'\n')

def raw_code_before(raw_url, file_id, YM):

    try:
        dir_path = "files_before/" + YM
        os.makedirs(dir_path, exist_ok=True)
        file_path =  os.path.join(dir_path, str(file_id))

        if os.path.exists(file_path):
            return 

        commit_id = raw_url.partition('/raw/')[2].split('/')[0]

        history_url = raw_url.replace('/raw/'+commit_id, '/commits/'+commit_id)
        soup = BeautifulSoup(urlopen(Request(history_url,
                                headers={'User-Agent': 'Mozilla/5.0'})).read(),
                                'html.parser')
        commit_id_before = None
        for commit in soup.find_all('clipboard-copy'):
            commit_id_before = commit.get('value')
            if str(commit_id_before) != str(commit_id):
                break
    
        raw_url_before = raw_url.replace('/raw/'+str(commit_id), '/raw/'+str(commit_id_before))
   
        wget_command = "wget -O " + file_path + " " + raw_url_before
        subprocess.run(wget_command, shell=True)
    except Exception as e:
        print(e)

def add_message(file_id, YM):
    dir_path = "files_before/" + YM
    file_path =  os.path.join(dir_path, str(file_id))
    
    if not os.path.exists(file_path):
        print(file_path)
        return ''

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except:
        print('ERROR')
        return ''

def step_three(Year, Month):
    patches_id = 0 # every file patch id is unique
    files_id = 0
    YM = Year+'_'+Month
    patch_name = 'crawl_result/' + YM + '_patch.jsonl'
    rawcode_name = 'rawcode_result/' + YM + '_rawcode.jsonl'
    error_file = 'rawcode_result/' + YM + '_rawcode_error.txt'

    if not os.path.exists(patch_name):
        return

    already_patch = 0
    if os.path.exists(rawcode_name):
        with open(rawcode_name, "r", encoding = "utf-8") as rf:
            alcon = rf.readlines()
            if len(alcon) > 0:
                last = alcon[-1]
                already_patch = int(json.loads(last)['patches_id'])
    print("already_patch: ", already_patch)
    patches= []
    with open(patch_name, "r", encoding="utf-8") as f:
        patches = json.load(f)

    errors = []

    for patch in tqdm(patches):
        patches_id += 1
        if patches_id <= already_patch:
            continue
        for eachfile in patch['files']:
            try:
                if "raw_url" in eachfile:
                    files_id += 1
                    one_res = {}
                    raw_url = eachfile['raw_url']
                    if 'patch' not in eachfile:
                        continue

                    dir_path = "files/" + YM
                    os.makedirs(dir_path, exist_ok=True)
                    file_path =  os.path.join(dir_path, str(files_id))
                    wget_command = "wget -O " + file_path + " " + raw_url
                    subprocess.run(wget_command, shell=True)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                    if content!=None:
                        one_res['patches_id'] = patches_id
                        one_res['files_id'] = files_id
                        one_res['language'] = eachfile['filename'].split('.')[-1]
                        one_res['raw_url'] = raw_url  # url for identification

                        # 修改后的代码
                        one_res['raw_code'] = content # raw code
                        one_res['file_path'] = file_path
                        one_res['raw_code'] = str(content,encoding='utf-8') # raw code
                        # 添加修改前的代码
                        raw_code_before(raw_url, file_id, YM)
                        one_res['raw_code_before'] = add_message(file_id, YM)
                        one_res['patch'] = eachfile['patch']
                    with open(rawcode_name, 'a', encoding='utf-8') as f2:
                        jsonobj = json.dumps(one_res)
                        f2.write(jsonobj + '\n')
                else:
                    print("Wrong! raw_url not exist, see case ", patches_id)
                    errors.append(patches_id) 
            except Exception as e:
                print(e)
                print("case is wrong ", patches_id)
                continue
   
    with open(error_file, "w", encoding = "utf-8") as rf:
        for err in errors:
            rf.write(err+'\n')
    print('in total we have got {}'.format(patches_id))

def get_repos(Year, Month):

    YM = Year+'_'+Month
    mergefile_time = 'merge_result/time/merge_'
    merge_name = mergefile_time + YM + '.jsonl'

    if not os.path.exists(merge_name):
        return

    dir_path = 'repos/' + YM
    os.makedirs(dir_path, exist_ok=True)

    with open(merge_name, encoding='utf-8') as f:
        content = f.readlines()

        for i in range(len(content)):
            js = json.loads(content[i])
            raw_url = js['html_url']
            commit_id = js['commit_id']
            
            repos_name = str(commit_id) + ".zip"
            repos_file = os.path.join(dir_path, repos_name)
            repos_url = raw_url.replace("commit/" + str(commit_id), "archive/" + str(commit_id)) + ".zip"

            # 使用subprocess运行wget命令
            try:
                subprocess.run(["wget", "-O", repos_file, repos_url], check=True)
                print("Download old repos successful!")
            except subprocess.CalledProcessError as e:
                print(f"Error downloading file: {e}")


def add_message_before(Year, Month):

    YM = Year+'_'+Month
    dir_path = 'crawl_result/'
    crawl_name = dir_path + YM + '_patch.jsonl'

    dir_path_new = 'crawl_result_new/'
    crawl_name_new = dir_path_new + YM + '_patch.jsonl'

    fetchs = []
    if not os.path.exists(crawl_name):
        return

    with open(crawl_name, "r", encoding="utf-8") as f:
        content = json.load(f)

        for i in range(len(content)):
            url = content[i]['url']

            try:
                output = bytes.decode(subprocess.check_output(["curl", "--request", "GET" ,"-H", "Authorization: Bearer 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", "-H", "X-GitHub-Api-Version: 2022-11-28", "-u", "KEY:", url]))
                data = json.loads(output)
                parents = data['parents']
                content[i]['parents'] = []
                for item in parents:
                    parent = {}
                    parent['commit_id_before'] = item['sha']
                    parent['url_before'] = item['url']
                    parent['html_url_before'] = item['html_url']
                    content[i]['parents'].append(parent)
                fetchs.append(content[i])
            except Exception as e:
                print(e)
                fetchs.append(content[i])
                continue
    
    with open(crawl_name_new, "w", encoding = "utf-8") as rf:
        rf.write(json.dumps(fetchs, indent=4, separators=(',', ': ')))

def get_repos_before(Year, Month):

    YM = Year+'_'+Month
    mergefile_time = 'merge_result/time/merge_'
    merge_name = mergefile_time + YM + '.jsonl'

    if not os.path.exists(merge_name):
        return

    dir_path = 'repos_before/' + YM
    os.makedirs(dir_path, exist_ok=True)

    with open(merge_name, encoding='utf-8') as f:
        content = f.readlines()

        for i in range(len(content)):
            js = json.loads(content[i])

            try:
                parents= js['parents']
            except:
                continue

            for parent in parents:
                raw_url = parent['html_url_before']
                commit_id = parent['commit_id_before']
            
                repos_name = str(commit_id) + ".zip"
                repos_file = os.path.join(dir_path, repos_name)
                repos_url = raw_url.replace("commit/" + str(commit_id), "archive/" + str(commit_id)) + ".zip"

                # 使用subprocess运行wget命令
                try:
                    subprocess.run(["wget", "-O", repos_file, repos_url], check=True)
                    print("Download old repos successful!")
                except subprocess.CalledProcessError as e:
                    print(f"Error downloading file: {e}")

def main():

    Years = [str(year) for year in range(2001, 2024)]
    print(Years)
    Months = [str(month) for month in range(1, 13)]
    print(Months)
    for Year in Years:
        for Month in Months:
            step_one(Year, Month)

    for Year in Years:
        for Month in Months:
            step_two(Year, Month)
    
    for Year in Years:
        for Month in Months:
            step_three(Year, Month)
            add_message(Year, Month)
    
    for Year in Years:
        for Month in Months:
            get_repos(Year, Month)
    
    for Year in Years:
        for Month in Months:
            add_message_before(Year, Month)
            get_repos_before(Year, Month)


if __name__ == '__main__':
    main()