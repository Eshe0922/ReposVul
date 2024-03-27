from tree_sitter import Language, Parser
import os

Language.build_library(
    # Store the library in the `build` directory
    "/new_data/Challenge/my_treesitter/build/my-languages.so",
    # Include one or more languages
    [
        "/new_data/Challenge/my_treesitter/tree-sitter-c",
        "/new_data/Challenge/my_treesitter/tree-sitter-cpp",
        "/new_data/Challenge/my_treesitter/tree-sitter-java",
        "/new_data/Challenge/my_treesitter/tree-sitter-python"
        ]
)

def traverse_outfunc(node, res = None):
    if res is None:
        res = list()
    if node.type == 'function_definition':
        res.append(node)
    else:
        if isinstance(node.children, list):
            for n in node.children:
                res.extend(traverse_outfunc(n, None))
    return res

def traverse_outclass(node, res = None):
    if res is None:
        res = list()
    if node.type == 'class_definition':
        res.append(node)
    else:
        if isinstance(node.children, list):
            for n in node.children:
                res.extend(traverse_outclass(n, None))
    return res

def get_func_name(node):
    for n in node.children:
        if n.type == 'function_declarator':
            return n.text.decode('utf-8').split('(')[0].strip()
    return None

def get_api_name(node):
    return node.text.decode('utf-8').split('(')[0]

def traverse(node):
    print('type = {}, text = {}'.format(node.type, node.text))
    if node.type == 'function_definition':
        print('parent is {}'.format(node.parent.parent.children[1].text.decode('utf-8')))
        if node.parent.parent.children[1].type == 'decorated_definition':
            print(node.parent.parent.parent.children[1].text.decode('utf-8'))
    for i in node.children:
        traverse(i)

def get_outfunc_and_nearfunc(file_path, language, start_line, end_line):
    prefix = '.'.join(file_path[:-3].split('/')[6:])
    LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', language)
    parser = Parser()
    parser.set_language(LANGUAGE)
    with open(file_path, 'rb') as r1:
        file = r1.read()
    file_arr = file.splitlines()
    tree = parser.parse(file)
    # traverse(tree.root_node)
    ret_func = traverse_outfunc(tree.root_node)
    func_node = list()
    func_name = list()
    for i in range(len(ret_func)):
        if ret_func[i].start_point[0] > end_line or ret_func[i].end_point[0] < start_line:
            continue
        func_node.append(ret_func[i])

    # if len(func_node) == 0:
    #     func_node.append('')
    
    print('func_node:{}'.format(func_node))
    for fun in func_node:
        tmp = get_func_name(fun)
        if tmp:
            func_name.append(tmp)
        # class_prefix = ''
        # if fun and fun.parent and fun.parent.parent and fun.parent.parent.type == 'class_definition':
        #     class_prefix = fun.parent.parent.children[1].text.decode('utf-8') + '.'
        # if fun and fun.parent and fun.parent.parent and fun.parent.parent.parent and fun.parent.parent.parent.type == 'class_definition':
        #     class_prefix = fun.parent.parent.parent.children[1].text.decode('utf-8') + '.'
        # if not isinstance(fun, str):
        #     tmp = class_prefix + get_func_name(fun)
        # else:
        #     tmp = ''
        # if tmp != '':
        #     func_name.append(prefix + '.' + tmp)
        # else:
        #     func_name.append(prefix)
    print('func_name:{}'.format(func_name))
    return func_name

def get_code(code_statement):
    if_exists = False
    func_abs_name = ''
    res_code = ''
    if code_statement.startswith('  +-') or code_statement.startswith('  \-'):
        if ' at ' in code_statement:
            code_statement = code_statement[4:]
            func_name = code_statement.split('(')[0]
            code_statement = code_statement.split(' at ')[1]
            file_path = code_statement.split(':')[0]
            LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'cpp')
            parser = Parser()
            parser.set_language(LANGUAGE)
            with open(file_path, 'rb') as r1:
                file = r1.read()
            tree = parser.parse(file)
            out_func = traverse_outfunc(tree.root_node)
            for of in out_func:
                if func_name == get_func_name(of):
                    res_code = of.text.decode('utf-8', errors='ignore')
                    if_exists = True
                    print('res_code:{}'.format(res_code))
                    break
            func_abs_name = '.'.join(file_path.split('/')[6:]) + func_name
            func_abs_name = '.'.join(func_abs_name.split('.')[:-1]) + '.' + func_abs_name.split('.')[-1][1:]
    return if_exists, func_abs_name, res_code

# def get_start_end(unzip_code_path, func_code):
#     LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'c')
#     parser = Parser()
#     parser.set_language(LANGUAGE)
#     with open(unzip_code_path, 'rb') as r1:
#         file1 = r1.read()
#     file_arr1 = file1.splitlines()
#     tree1 = parser.parse(file1)

#     with open(func_code, 'rb') as r2:
#         file2 = r2.read()
#     file_arr2 = file2.splitlines()
#     tree2 = parser.parse(file2)

#     for t in tree2.children:
#         print(t.type)
#         print(t.text)

# get_start_end('')

# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/cobbler-36c2ba149f8ba005ea30a94439562fd6fd4e9b67/scripts/migrate-data-v2-to-v3.py', 'python', 90, 99)
# , start_line is 62, end_line is 69
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/integration-jira-cloud-fa838db45f1ae5581a47e1965f74919c12488cf5/tenable_jira/cli.py', 'python', 62, 69)
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/apkleaks-8577b7af6224bf0a5455b552963c46721308d2ff/apkleaks/apkleaks.py', 'python', 90, 92)
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/rdiffweb-a5d0bca218bd83c2e131767c061b0872969e9d23/rdiffweb/controller/page_pref_general.py', 'python', 144, 170)
# get_code('/new_data/Challenge/unzip_tmp/lemur-f5c0c643ab2cfee2c672b0059702759bfc29913b/lemur/tests/conf.py', 'lemur.tests.conf.get_random_secret')
# get_code('/new_data/Challenge/unzip_tmp/lemur-f5c0c643ab2cfee2c672b0059702759bfc29913b/lemur/tests/factories.py', 'lemur.tests.factories.CertificateFactory.user')
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/accel-ppp-c8575ff09416c967aa6907b5b4e9b187d4a78d14/accel-pppd/backup/backup_file.c', 'c', 54,60)
# print(get_code('  \-ssl_lock_init() <void (void) at /new_data/Challenge/unzip_tmp/accel-ppp-c8575ff09416c967aa6907b5b4e9b187d4a78d14/accel-pppd/main.c:62>'))