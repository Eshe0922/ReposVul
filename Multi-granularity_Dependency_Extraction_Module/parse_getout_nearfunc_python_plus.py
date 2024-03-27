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
            return n.text.decode('utf-8').split('(')[0].strip()
    return None

def get_func_name_from_code(code):
    LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'python')
    parser = Parser()
    parser.set_language(LANGUAGE)
    byte_string = code.encode('utf-8')
    tree = parser.parse(byte_string)
    for child in tree.root_node.children:
        if child.type == 'function_definition':
            return get_func_name(child)
    # print(get_func_name(tree.root_node))
    return None
    # return get_func_name(tree.root_node)

def get_api_name(node):
    return node.text.decode('utf-8').split('(')[0].strip()

def traverse(node):
    print('type = {}, text = {}'.format(node.type, node.text))
    if node.type == 'function_definition':
        print('-------------')
        for i in node.children:
            print('type = {}, text = {}'.format(i.type, i.text))
        print('-------------')
    # if node.type == 'function_definition':
        # print('parent is {}'.format(node.parent.parent.children[1].text.decode('utf-8')))
        # if node.parent.parent.children[1].type == 'decorated_definition':
        #     print(node.parent.parent.parent.children[1].text.decode('utf-8'))
    for i in node.children:
        traverse(i)

# with open('/new_data/Challenge/newest/process_python.py', 'rb') as r1:
#     code = r1.read()
# LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'python')
# parser = Parser()
# parser.set_language(LANGUAGE)
# tree = parser.parse(code)
# traverse(tree.root_node)

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

# def get_code(code_statement):
#     if_exists = False
#     func_abs_name = ''
#     res_code = ''
#     if code_statement.startswith('  +-') or code_statement.startswith('  \-'):
#         if ' at ' in code_statement:
#             code_statement = code_statement[4:]
#             func_name = code_statement.split('(')[0].strip()
#             code_statement = code_statement.split(' at ')[1]
#             file_path = code_statement.split(':')[0]
#             LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'cpp')
#             parser = Parser()
#             parser.set_language(LANGUAGE)
#             with open(file_path, 'rb') as r1:
#                 file = r1.read()
#             tree = parser.parse(file)
#             out_func = traverse_outfunc(tree.root_node)
#             for of in out_func:
#                 if func_name == get_func_name(of):
#                     res_code = of.text.decode('utf-8', errors='ignore')
#                     if_exists = True
#                     print('res_code:{}'.format(res_code))
#                     break
#             func_abs_name = '.'.join(file_path.split('/')[6:]) + func_name
#             func_abs_name = '.'.join(func_abs_name.split('.')[:-1]) + '.' + func_abs_name.split('.')[-1][1:]
#     return if_exists, func_abs_name, res_code

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

def traverse_call(node, res = None):
    if res is None:
        res = list()
    if node.type == 'call':
        res.append(node)
    if isinstance(node.children, list):
        for n in node.children:
            res.extend(traverse_call(n, None))
    return res

def traverse_all(node):
    print('node.type = {}, node.text = {}'.format(node.type, node.text))
    for n in node.children:
        traverse_all(n)

def choose_caller(file_path, start_line, end_line, caller):
    LANGUAGE = Language('/new_data/Challenge/my_treesitter/build/my-languages.so', 'python')
    parser = Parser()
    parser.set_language(LANGUAGE)
    with open(file_path, 'rb') as r1:
        file = r1.read()
    file_arr = file.splitlines()
    tree = parser.parse(file)
    all_calls = traverse_call(tree.root_node, None)
    res = list()
    for ac in all_calls:
        if ac.start_point[0] > end_line or ac.end_point[0] < start_line:
            continue
        res.append(ac.text.decode('utf-8').split('(')[0].strip())
    res = list(set(res))
    final_res = dict()
    for cl in caller:
        func_name = cl.split('.')[-1]
        if func_name in res:
            final_res[cl] = caller[cl]
    return final_res

# print(choose_caller('/new_data/Challenge/newest/test.c', 1, 6, {'a.b.c.flush':'sldkfkd', 'a.s':'sdssssss', 'sss.sss': 'ldllsks'}))


# code = '''int main(){
#     flush();
#     ssm();
#     f = s();
#     printf("SSSS");
# }
# '''
# print(get_func_name_from_code(code))
# caller_tree = {'mono.metadata.class.mono_array_element_size': 'gint32\nmono_array_element_size (MonoClass *ac)\n{\n\tg_assert (ac->rank);\n\treturn ac->sizes.element_size;\n}', 'mono.metadata.object.mono_value_copy': 'void\nmono_value_copy (gpointer dest, gpointer src, MonoClass *klass)\n{\n\tint size = mono_class_value_size (klass, NULL);\n\tmono_gc_wbarrier_value_copy (dest, src, 1, klass);\n\tmemcpy (dest, src, size);\n}', 'mono.metadata.class.mono_class_is_subclass_of': 'gboolean\nmono_class_is_subclass_of (MonoClass *klass, MonoClass *klassc, \n\t\t\t   gboolean check_interfaces)\n{\n\tg_assert (klassc->idepth > 0);\n\tif (check_interfaces && MONO_CLASS_IS_INTERFACE (klassc) && !MONO_CLASS_IS_INTERFACE (klass)) {\n\t\tif (MONO_CLASS_IMPLEMENTS_INTERFACE (klass, klassc->interface_id))\n\t\t\treturn TRUE;\n\t} else if (check_interfaces && MONO_CLASS_IS_INTERFACE (klassc) && MONO_CLASS_IS_INTERFACE (klass)) {\n\t\tint i;\n\n\t\tfor (i = 0; i < klass->interface_count; i ++) {\n\t\t\tMonoClass *ic =  klass->interfaces [i];\n\t\t\tif (ic == klassc)\n\t\t\t\treturn TRUE;\n\t\t}\n\t} else {\n\t\tif (!MONO_CLASS_IS_INTERFACE (klass) && mono_class_has_parent (klass, klassc))\n\t\t\treturn TRUE;\n\t}\n\n\t/* \n\t * MS.NET thinks interfaces are a subclass of Object, so we think it as\n\t * well.\n\t */\n\tif (klassc == mono_defaults.object_class)\n\t\treturn TRUE;\n\n\treturn FALSE;\n}', 'mono.metadata.object.mono_value_copy_array': 'void\nmono_value_copy_array (MonoArray *dest, int dest_idx, gpointer src, int count)\n{\n\tint size = mono_array_element_size (dest->obj.vtable->klass);\n\tchar *d = mono_array_addr_with_size (dest, size, dest_idx);\n\tmono_gc_wbarrier_value_copy (d, src, count, mono_object_class (dest)->element_class);\n\tmemmove (d, src, size * count);\n}'}
# print(choose_caller('/new_data/Challenge/unzip_tmp/mono-035c8587c0d8d307e45f1b7171a0d337bb451f1e/mono/metadata/icall.c', 772, 784, caller_tree))