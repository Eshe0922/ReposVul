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
        if n.type == 'identifier':
            return n.text.decode('utf-8')
    return None

# def traverse_api(node, res = None):
#     if res is None:
#         res = list()
#     if node.type == 'call':
#         res.append(node)
#     if isinstance(node.children, list):
#         for n in node.children:
#             res.extend(traverse_api(n, None))
#     return res

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
    # print(prefix)
    if language == 'py':
        language = 'python'
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

    if len(func_node) == 0:
        func_node.append('')
    
    print('func_node:{}'.format(func_node))
    for fun in func_node:
        class_prefix = ''
        if fun and fun.parent and fun.parent.parent and fun.parent.parent.type == 'class_definition':
            class_prefix = fun.parent.parent.children[1].text.decode('utf-8') + '.'
        if fun and fun.parent and fun.parent.parent and fun.parent.parent.parent and fun.parent.parent.parent.type == 'class_definition':
            class_prefix = fun.parent.parent.parent.children[1].text.decode('utf-8') + '.'
        if not isinstance(fun, str):
            tmp = class_prefix + get_func_name(fun)
        else:
            tmp = ''
        if tmp is not None:
            if tmp != '':
                func_name.append((prefix + '.' + tmp).replace('.__init__', ''))
            else:
                func_name.append(prefix.replace('.__init__', ''))
    print('func_name:{}'.format(func_name))
    return func_name

def get_code(code_path, func_name):
    print(code_path)
    root_name = '/'.join(code_path.split('/')[:6]) + '/' + func_name.replace('.','/')
    root_name = root_name.split('/')
    if_exists = False
    res_code = ''
    for i in range(1,len(root_name) - 6):
        py_path = '/'.join(root_name[:len(root_name) - i]) + '.py'
        remaining_part = root_name[len(root_name) - i:]
        print(remaining_part)
        print(py_path)
        if os.path.exists(py_path):
            print(py_path)
            LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'python')
            parser = Parser()
            parser.set_language(LANGUAGE)
            with open(py_path, 'rb') as r1:
                file = r1.read()
            tree = parser.parse(file)
            if len(remaining_part) == 1:
                func_name = remaining_part[0]
                out_func = traverse_outfunc(tree.root_node)
                for of in out_func:
                    if func_name == get_func_name(of):
                        res_code = of.text.decode('utf-8')
                        if_exists = True
                        print('res_code:{}'.format(res_code))
                        break
            elif len(remaining_part) == 2:
                class_name = remaining_part[0]
                func_name = remaining_part[1]
                out_class = traverse_outclass(tree.root_node)
                for oc in out_class:
                    if class_name == get_func_name(oc):
                        class_func = traverse_outfunc(oc)
                        for cf in class_func:
                            if get_func_name(cf) == func_name:
                                res_code = cf.text.decode('utf-8')
                                if_exists = True
                                print('res_code:{}'.format(res_code))
            break
    return if_exists, res_code


# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/cobbler-36c2ba149f8ba005ea30a94439562fd6fd4e9b67/scripts/migrate-data-v2-to-v3.py', 'python', 90, 99)
# , start_line is 62, end_line is 69
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/integration-jira-cloud-fa838db45f1ae5581a47e1965f74919c12488cf5/tenable_jira/cli.py', 'python', 62, 69)
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/apkleaks-8577b7af6224bf0a5455b552963c46721308d2ff/apkleaks/apkleaks.py', 'python', 90, 92)
# get_outfunc_and_nearfunc('/new_data/Challenge/unzip_tmp/rdiffweb-a5d0bca218bd83c2e131767c061b0872969e9d23/rdiffweb/controller/page_pref_general.py', 'python', 144, 170)
# get_code('/new_data/Challenge/unzip_tmp/lemur-f5c0c643ab2cfee2c672b0059702759bfc29913b/lemur/tests/conf.py', 'lemur.tests.conf.get_random_secret')
# get_code('/new_data/Challenge/unzip_tmp/lemur-f5c0c643ab2cfee2c672b0059702759bfc29913b/lemur/tests/factories.py', 'lemur.tests.factories.CertificateFactory.user')