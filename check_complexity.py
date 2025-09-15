import json
import sys

sys.path.extend(['.', '..'])
from pycparser import c_parser, c_ast, parse_file


# A visitor with some state information (the funcname it's looking for)
class FuncCallVisitor(c_ast.NodeVisitor):
    def __init__(self, target_func_name):
        self.target_func_name = target_func_name
        self.function_calls = []

    def visit_FuncDef(self, node):
        if node.decl.name == self.target_func_name:
            self.visit(node.body)

    def visit_FuncCall(self, node):
        """ Capture function call names """
        if isinstance(node.name, c_ast.ID):  # Ensure it's an identifier (function name)
            self.function_calls.append(node.name.name)


# A simple visitor for FuncDef nodes that prints the names and
# locations of function definitions.
class FuncDefVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.functions = []

    def visit_FuncDef(self, node):
        func_info = {
            "name": node.decl.name,
            "node": node
        }
        self.functions.append(func_info)

    def find_loops(self, node):
        # do while loops count as while loops
        if isinstance(node, c_ast.For) or isinstance(node, c_ast.While):
            return True
        for _, child in node.children():
            if self.find_loops(child):
                return True
        return False


class FindFuncDef(c_ast.NodeVisitor):
    def __init__(self, target_func_name):
        self.target_func_name = target_func_name
        self.target_node = None  # Store the found function node

    def visit_FuncDef(self, node):
        if node.decl.name == self.target_func_name:
            self.target_node = node  # Store the function definition node

    def get_function_node(self, ast):
        """Visit the AST and return the function node if found."""
        self.visit(ast)
        return self.target_node


def loop_check(loop_depth, node, function_def_list, parent_name):
    if isinstance(node, c_ast.For) or isinstance(node, c_ast.While) or isinstance(node, c_ast.DoWhile):
        loop_depth += 1

    # check if this is a function call and then check that function for loop
    if isinstance(node, c_ast.FuncCall) and isinstance(node.name, c_ast.ID):
        print(f"Function call to: {node.name.name}")
        # this means recursion is present
        if node.name.name == parent_name:
            return sys.maxsize
        else:
            # no recursion, but another user defined function is called
            for function in function_def_list:
                if function['name'] == node.name.name:
                    # call to user defined function
                    function_depth = loop_check(loop_depth, function['node'], function_def_list, parent_name)
                    loop_depth = max(loop_depth, function_depth)
    max_depth = loop_depth

    for _, child in node.children():
        child_depth = loop_check(loop_depth, child, function_def_list, parent_name)
        max_depth = max(child_depth, max_depth)

    return max_depth


# https://www.dii.uchile.cl/~daespino/files/Iso_C_1999_definition.pdf
# supposedly what pycparser uses, go to page 402
def complexity_check(ast, funcname) -> int:
    """
    Returns the time complexity of the provided function.
    If recursion is found, returns -1
    """
    target_func_node = FindFuncDef(funcname).get_function_node(ast)
    # print(target_func_node)

    # get all function declaration nodes:
    dv = FuncDefVisitor()
    dv.visit(ast)

    complexity = loop_check(0, target_func_node, dv.functions, funcname)
    if complexity == sys.maxsize:
        complexity = -1

    return complexity
