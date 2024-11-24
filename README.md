<div align="center">
    <p>
    <h1>
    ReposVul
    </h1>
    <img src="logo.png" alt="ReposVul Logo" style="width: 200px; height: 200px;">
    </p>
    <p>
    (Logo generated by DALL·E 3)
    </p>
    <a href="https://github.com/ddlBoJack/MT4SSL"><img src="https://img.shields.io/badge/Platform-linux-lightgrey" alt="version"></a>
    <a href="https://github.com/ddlBoJack/MT4SSL"><img src="https://img.shields.io/badge/Python-3.8+-orange" alt="version"></a>
    <a href="https://github.com/ddlBoJack/MT4SSL"><img src="https://img.shields.io/badge/License-MIT-red.svg" alt="mit"></a>
</div>

<div align="center">
  <a href="https://arxiv.org/abs/2401.13169">
    <b><em>ReposVul: A Repository-Level High-Quality Vulnerability Dataset</em></b>
  </a>
  <br></br>
  <p>
    <b><em>ICSE 2024 Challenge Track</em></b>
  </p>
</div>
<hr>

## 🙂 Vulnearability Detection Competition
- We have released the training, validation, and test datasets in C and C++ programming languages, which includes repository-level, function-level and line-level information.
```bash
https://drive.google.com/file/d/1sQynG6Fe2h2zmZ7MFGtAHGIhL3PAZuXF/view?usp=drive_link
```
  
## 🔥 News
- *Feb 3th, 2024*: ReposVul is accepted to ICSE 2024 Challenge Track! 🎉

## 📥 Load Data

ReposVul is available at:

### Download Data via Google Drive
1. Download the all data from [Google Drive](https://drive.google.com/file/d/1szQ9FnIC_onQRu_TjZ2uofkjv9z_s4pv/view?usp=drive_link), or simply use the following links:
```bash
https://drive.google.com/file/d/1szQ9FnIC_onQRu_TjZ2uofkjv9z_s4pv/view?usp=drive_link
```

> [NOTE]
> &#128712; For each programming language, we also provide the divided data: .
- `[Programming Language: C]`:
```bash
https://drive.google.com/file/d/1UNHKaEU1Hls5fmOFLW2YefGN1FqGeOrA/view?usp=drive_link
```
- `[Programming Language: C++]`:
```bash
https://drive.google.com/file/d/1jYwIOXJUHhbTA0UkKVLQYyuxKBlv2kKO/view?usp=drive_link
```

- `[Programming Language: Java]`:
```bash
https://drive.google.com/file/d/18pkURdURNzQItFy2DdA0b7lNhfGCnEdZ/view?usp=drive_link
```

- `[Programming Language: Python]`:
  
```bash
https://drive.google.com/file/d/1-KOYI9h5G-UDB1UCBpitPq-6OWCy6YRa/view?usp=drive_link
```

## 🚨 Abstract
- [ReposVul: A Repository-Level High-Quality Vulnerability Dataset](https://arxiv.org/abs/2401.13169)

In this paper, we propose an automated data collection framework and construct the first repository-level high-quality vulnerability dataset named **ReposVul**. The proposed framework mainly contains three modules: (1) A vulnerability untangling module, aiming at distinguishing vulnerability-fixing related code changes from tangled patches, in which the Large Language Models (LLMs) and static analysis tools are jointly employed. (2) A multi-granularity dependency extraction module, aiming at capturing the inter-procedural call relationships of vulnerabilities, in which we construct multiple-granularity information for each vulnerability patch, including repository-level, file-level, function-level, and line-level. (3) A trace-based filtering module, aiming at filtering the outdated patches, which leverages the file path trace-based filter and commit time trace-based filter to construct an up-to-date dataset.

The constructed repository-level ReposVul encompasses 6,134 CVE entries representing 236 CWE types across 1,491 projects and four programming languages. Thorough data analysis and manual checking demonstrate that ReposVul is high in quality and alleviates the problems of tangled and outdated patches in previous vulnerability datasets.



## 🛠️ Data Collection Framework
🤯**Raw Data Crawling:** The creation of the initial dataset involves three steps: 1) crawling vulnerability entries from open-source databases, 2) fetching patches associated with the vulnerability entry from multiple platforms, and 3) obtaining detailed information on changed files involved in the patch.

📅 **Vulnerability Untangling Module:** We propose to integrate the decisions of Large Language Models (LLMs) and static analysis tools to distinguish the vulnerability-fixing related files within the patches, given their strong contextual understanding capability and domain knowledge, respectively.

🔔 **Multi-granularity Dependency Extraction Module:** We extract the inter-procedural call relationships of vulnerabilities among the whole repository, aiming to construct multi-granularity information for each vulnerability patch, including file-level, function-level, and line-level information.

⚖️ **Trace-based Filtering Module:** We first track the submission history of patches based on file paths and commit time. Through analyzing historical information on the patches, we then identify outdated patches by tracing their commit diffs.

> [WARNING]
> The code is not well-organized and fully tested. If you encounter any issues, please feel free to raise issues or submit PRs. Thanks!

## 🔍 Data Description

    .
    +-- index
    +-- cve_id
    +-- cwe_id
    +-- cve_language
    +-- cve_description
    +-- cvss
    +-- publish_date
    +-- AV
    +-- AC
    +-- PR
    +-- UI
    +-- S
    +-- C
    +-- I
    +-- A
    +-- commit_id
    +-- commit_message
    +-- commit_date
    +-- project
    +-- url
    +-- html_url
    +-- outdated
    +-- cwe_description
    +-- cwe_consequence
    +-- cwe_method
    +-- cwe_solution
    +-- details
    |   +-- raw_url
    |   +-- code
    |   +-- code_before
    |   +-- patch
    |   +-- file_path
    |   +-- file_language
    |   +-- file_name
    |   +-- outdated_file_modify
    |   +-- outdated_file_before
    |   +-- outdated_file_after
    |   +-- llm_check
    |   +-- static_check
    |   +-- static
        |   +-- flawfinder
        |   +-- rats
        |   +-- semgrep
        |   +-- cppcheck
    |   +-- target
    |   +-- function_before
        |   +-- function
        |   +-- target
    |   +-- function_after
        |   +-- function
        |   +-- target
    +-- windows_before
    |   +-- commit_id
    |   +-- commit_date
    |   +-- commit_message
    |   +-- files_name
    +-- windows_after
    |   +-- commit_id
    |   +-- commit_date
    |   +-- commit_message
    |   +-- files_name
    +-- parents
    |   +-- commit_id_before
    |   +-- url_before
    |   +-- html_url_before

## 📝 Citation

If you use ReposVul in your research, please consider citing us:

```bibtex
@article{wang2024repository,
  title={A Repository-Level Dataset For Detecting, Classifying and Repairing Software Vulnerabilities},
  author={Xinchen Wang, Ruida Hu, Cuiyun Gao, Xin-Cheng Wen, Yujia Chen, and Qing Liap},
  journal={arXiv preprint arXiv:2401.13169},
  year={2024}
}
```



