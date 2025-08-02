from tree_sitter import Language, Parser
from graphviz import Digraph
import logging

logging.basicConfig(level=logging.DEBUG)

import tree_sitter_python as ts_python

PY_LANGUAGE = Language(ts_python.language())
parser = Parser(PY_LANGUAGE)

class CodeAnalyzer:
    def __init__(self):
        self.parser = parser

    def analyze_code(self, file_path):
        with open(file_path, "r", encoding="utf8") as f:
            code = f.read()
        code_bytes = code.encode("utf8")
        tree = self.parser.parse(code_bytes)
        root_node = tree.root_node

        functions = []
        imports = []

        def traverse(node):
            if node.type in ['import_statement', 'import_from_statement']:
                imports.append(code_bytes[node.start_byte:node.end_byte].decode("utf8"))
            elif node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    function_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
                    functions.append(function_name)
            for child in node.children:
                traverse(child)
        traverse(root_node)

        print("Complete AST:")
        def print_tree(node, src, indent=""):
            node_text = src[node.start_byte:node.end_byte].decode("utf8")
            print(f"{indent}{node.type} [{node.start_point} - {node.end_point}] '{node_text}'")
            for child in node.children:
                print_tree(child, src, indent + "  ")
        print_tree(root_node, code_bytes)
        return {'filePath': file_path, 'functions': functions, 'imports': imports}