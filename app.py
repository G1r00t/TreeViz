from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
import os
from main import CodeAnalyzer, PY_LANGUAGE, parser
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app)

class InteractiveCodeAnalyzer(CodeAnalyzer):
    def __init__(self):
        super().__init__()  
    def analyze_code_content(self, code_content, clean_level="clean"):
        """Analyze code content and return AST data suitable for interactive visualization"""
        code_bytes = code_content.encode("utf8")
        tree = self.parser.parse(code_bytes)
        root_node = tree.root_node
        functions = []
        imports = []
        classes = []
        def traverse_extended(node):
            if node.type in ['import_statement', 'import_from_statement']:
                imports.append(code_bytes[node.start_byte:node.end_byte].decode("utf8").strip())
            elif node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    function_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
                    functions.append(function_name)
            elif node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
                    classes.append(class_name)
            for child in node.children:
                traverse_extended(child)
        traverse_extended(root_node)
        nodes = []
        links = []
        node_counter = 0
        def should_include_node(node, src):
            """Filter out noise nodes that clutter the visualization"""
            if clean_level == "full":
                return True  
            node_text = src[node.start_byte:node.end_byte].decode("utf8").strip()
            base_skip = {
                ':', '(', ')', '[', ']', '{', '}', ',', ';', '.', 
                '+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|',
                'comment', 'string_start', 'string_end', 'string_content',
                'indent', 'dedent', 'newline', 'escape_sequence',
            }
            if clean_level in ["clean", "ultra"]:
                base_skip.update({
                    'binary_operator', 
                    'module',
                    'parenthesized_expression',
                    'expression_statement',
                })
            if clean_level == "ultra":
                base_skip.update({
                    'block',
                    'argument_list',
                    'parameter_list',
                    'arguments',  
                })
            if node.type in base_skip:
                return False
            punctuation_chars = {':', '(', ')', '[', ']', '{', '}', ',', ';', '.', '=', '+', '-', '*', '/', '%', '<', '>', '!', '&', '|'}
            if node_text in punctuation_chars:
                return False
            if len(node_text.strip()) <= 1 and node_text in '()[]{},:;.+-*/=<>!&|':
                return False
            if not node_text or node_text.isspace():
                return False
            if clean_level == "ultra" and node.child_count == 1:
                child = node.children[0]
                child_text = src[child.start_byte:child.end_byte].decode("utf8").strip()
                if node_text == child_text and node.type != child.type:
                    return False

            return True

        def build_interactive_tree(node, src, parent_id=None):
            nonlocal node_counter
            if not should_include_node(node, src):

                for child in node.children:
                    build_interactive_tree(child, src, parent_id)
                return parent_id
            current_id = node_counter
            node_counter += 1

            node_text = src[node.start_byte:node.end_byte].decode("utf8")
            if len(node_text) > 100:
                node_text = node_text[:97] + "..."

            display_text = node_text.strip()
            if node.child_count == 0 and len(display_text) > 30:
                display_text = display_text[:27] + "..."

            node_label = node.type
            if node.type == 'call' and node.child_count > 0:

                first_child = node.children[0]
                if first_child.type == 'identifier':
                    func_name = src[first_child.start_byte:first_child.end_byte].decode("utf8").strip()
                    node_label = f"call: {func_name}"
            elif node.type == 'string' and len(display_text) > 20:

                node_label = f"string: {display_text[:15]}..."
            elif node.type == 'identifier':

                node_label = f"id: {display_text}"
            node_data = {
                'id': current_id,
                'type': node.type,
                'label': node_label,  
                'text': display_text,
                'full_text': node_text.strip(),  
                'start_point': [node.start_point.row, node.start_point.column],
                'end_point': [node.end_point.row, node.end_point.column],
                'is_leaf': node.child_count == 0,
                'child_count': node.child_count
            }

            if node.type in ['function_definition', 'class_definition']:
                node_data['color'] = '#e74c3c'  
                node_data['size'] = 18
            elif node.type in ['import_statement', 'import_from_statement']:
                node_data['color'] = '#1abc9c'  
                node_data['size'] = 16
            elif node.type in ['if_statement', 'for_statement', 'while_statement', 'try_statement', 'with_statement']:
                node_data['color'] = '#3498db'  
                node_data['size'] = 16
            elif node.type in ['call']:
                node_data['color'] = '#f39c12'  
                node_data['size'] = 14
            elif node.type in ['attribute']:
                node_data['color'] = '#e67e22'  
                node_data['size'] = 12
            elif node.type in ['identifier']:
                node_data['color'] = '#27ae60'  
                node_data['size'] = 11
            elif node.type in ['string', 'integer', 'float', 'true', 'false', 'none']:
                node_data['color'] = '#2ecc71'  
                node_data['size'] = 10
            elif node.type in ['parameters', 'arguments']:
                node_data['color'] = '#9b59b6'  
                node_data['size'] = 13
            elif node.type in ['return_statement', 'assignment']:
                node_data['color'] = '#8e44ad'  
                node_data['size'] = 13
            else:
                node_data['color'] = '#95a5a6'  
                node_data['size'] = 10
            nodes.append(node_data)
            if parent_id is not None:
                links.append({
                    'source': parent_id,
                    'target': current_id
                })
            for child in node.children:
                build_interactive_tree(child, src, current_id)
            return current_id
        build_interactive_tree(root_node, code_bytes)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print("Complete AST:")
            def print_tree(node, src, indent=""):
                node_text = src[node.start_byte:node.end_byte].decode("utf8")
                print(f"{indent}{node.type} [{node.start_point} - {node.end_point}] '{node_text}'")
                for child in node.children:
                    print_tree(child, src, indent + "  ")
            print_tree(root_node, code_bytes)
        return {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'functions': functions,
                'imports': imports,
                'classes': classes,
                'total_nodes': len(nodes)
            }
        }
analyzer = InteractiveCodeAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        code_content = data.get('code', '')
        clean_level = data.get('clean_level', 'clean')
        if not code_content.strip():
            return jsonify({'error': 'No code provided'}), 400
        result = analyzer.analyze_code_content(code_content, clean_level)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_file', methods=['POST'])
def analyze_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.py'):
            return jsonify({'error': 'Only Python files are supported'}), 400
        code_content = file.read().decode('utf-8')
        result = analyzer.analyze_code_content(code_content)
        result['filename'] = file.filename
        return jsonify(result)
    except Exception as e:
        logging.error(f"File analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    import os
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)