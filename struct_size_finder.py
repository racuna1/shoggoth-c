from enum import EnumType

from pycparser import c_ast
from pycparser.c_ast import IdentifierType

import ast_generator
from helpers import submission_dir


class StructVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.structs = []
        self.typedefs = {}

    def visit_Struct(self, node):
        if node.name:

            if node.decls:
                self.structs.append(node)

    def visit_Typedef(self, node):
        if isinstance(node.type, c_ast.Struct):
            if node.decls:
                self.structs.append(node)

        contents_type = node.type.type
        has_type = True

        while not isinstance(contents_type, IdentifierType):
            if isinstance(contents_type, c_ast.Enum):
                self.typedefs[node.name] = "enum"
                return

            if(hasattr(contents_type, "type")):
                contents_type = contents_type.type
            else:
                has_type = False
                break

        if has_type:
            self.typedefs[node.name] = " ".join(contents_type.names)
        else:
            pass


def find_struct_sizes(ast, arch=64) -> dict:
    """
    Finds and returns the size of a struct based on the datatypes of the contents of the struct.
    Represents the size of a struct if you were to malloc one
    """
    types = {
        'char': 1,
        'short': 2,
        'int': 4,
        'long': 8,
        'long long': 8,
        'unsigned char': 1,
        'unsigned short': 2,
        'unsigned int': 4,
        'unsigned long': 8,
        'unsigned long long': 8,
        'float': 4,
        'double': 8,
        'long double': 16,
        '_Bool': 1,
        'wchar_t': 4,
        'size_t': 8,
        'ptrdiff_t': 8,
        'enum': 4
    }



    visitor = StructVisitor()
    visitor.visit(ast)

    struct_dict = {
        'count': len(visitor.structs),
        'sizes': []
    }

    # print(visitor.typedefs)

    for struct in visitor.structs:
        size = 0
        things = []
        for decl in struct.decls:
            if isinstance(decl.type, c_ast.PtrDecl):
                things.append("pointer")
                # pointer size varies based on architecture and are never packed so this needs to be accounted for
                if arch == 64:
                    # round up
                    size = ((size + 7) // 8) * 8
                    size += 8
                elif arch == 32:
                    # round up
                    size = ((size + 3) // 4) * 4
                    size += 4
            elif isinstance(decl.type, c_ast.TypeDecl):
                if isinstance(decl.type.type, c_ast.IdentifierType):
                    things.append("Identifier")
                    # print(decl)
                    name = " ".join(decl.type.type.names)

                    if name in types:
                        size += types[name]
                    elif name in visitor.typedefs:
                        def_type = visitor.typedefs[name]
                        if def_type in types:
                            size += types[def_type]
                        else:
                            print("ERROR")
                else:
                    print("This should not happen!")
            elif isinstance(decl.type, c_ast.ArrayDecl):
                things.append("array")
                contents_type = decl.type

                array_size = 1
                while isinstance(contents_type, c_ast.ArrayDecl):
                    array_size *= int(contents_type.dim.value)

                    contents_type = contents_type.type

                array_size *= types[" ".join(contents_type.type.names)]

                size += array_size
            else:
                print("ELSE")
                print(decl.type)

        # apply padding, nearest 8 or 4
        if arch == 64:
            size = ((size + 7) // 8) * 8
        elif arch == 32:
            size = ((size + 3) // 4) * 4
        struct_dict['sizes'].append((struct.name, size))
        print(things)

    # print("HELLO")
    # print(struct_dict)

    return struct_dict


if __name__ == "__main__":
    ast_generator.find_structs(submission_dir + "/CompletedScheduler.c")