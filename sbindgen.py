import os
import re
import argparse

FUNCTION_PATTERN = re.compile(r"/\*\s*@sbind\s*\*/\s*(?P<return>\w[\w\s\*]*)\s+(?P<name>\w+)\s*\((?P<params>[^\)]*)\);")
CUSTOM_NAME_PATTERN = re.compile(r"@sbind-name\s+(\S+)")
TYPE_DEFINITION_PATTERN = re.compile(r"@sbind-type\s+(\w+)\s*\{([^}]*)\}")

def parse_params(param_str):
    params = []
    for param in param_str.split(','):
        param = param.strip()
        if param:
            parts = param.rsplit(' ', 1)
            if len(parts) == 2:
                param_type, param_name = parts
                params.append((param_type.strip(), param_name.strip()))
    return params

def parse_type_definitions(header_content):
    type_definitions = {}
    for match in TYPE_DEFINITION_PATTERN.finditer(header_content):
        type_name, fields = match.groups()
        fields = [f.strip() for f in fields.split(',') if f.strip()]
        type_definitions[type_name.strip()] = fields
    return type_definitions

def process_header_files(headers, type_definitions):
    functions = []
    for header in headers:
        with open(header, 'r') as f:
            content = f.read()

        type_definitions.update(parse_type_definitions(content))

        for match in FUNCTION_PATTERN.finditer(content):
            return_type = match.group("return").strip()
            func_name = match.group("name").strip()
            params = parse_params(match.group("params"))

            # Check for custom Lua binding name
            lua_name = func_name
            custom_name_match = CUSTOM_NAME_PATTERN.search(content[:match.start()])
            if custom_name_match:
                lua_name = custom_name_match.group(1).strip()

            functions.append((func_name, lua_name, return_type, params))
    return functions

#--------------------------------
# Header file generation
#--------------------------------
HEADER_TEMPLATE = '''\
// This is sbindgen generated file, do not edit!
#ifndef LUA_VERSION_NUM
  #error "lua.h must be included before this file"
#endif

#ifndef SBIND_GENERATED_H
#define SBIND_GENERATED_H

'''
HEADER_FOOTER = '''\

  #endif // SBIND_GENERATED_H
'''

def generate_header_file(output_file, headers, functions, type_definitions):
    with open(output_file, 'w') as f:
        f.write(HEADER_TEMPLATE)
        for header in headers:
            f.write(f'#include "{header}"\n')
        f.write("\n")
        for func_name, lua_name, return_type, params in functions:
            f.write(generate_lua_binding(func_name, return_type, params, type_definitions))
            f.write("\n\n")
        f.write(generate_init_function([(func[0], func[1]) for func in functions]))
        f.write(HEADER_FOOTER);

    print(f"Generated header file for {len(functions)} functions -> {output_file}")

def generate_lua_binding(func_name, return_type, params, type_definitions):
    lua_code = [f"int sbindfun_{func_name}(lua_State* L) {{"]

    # If no parameters are used, mark L as unused to avoid warnings
    if not params and return_type == "void":
        lua_code.append("    (void)L;  /* unused */")

    # Parse parameters from Lua stack
    for i, (ptype, pname) in enumerate(params):
        if ptype in type_definitions:
            lua_code.append(f"    luaL_checktype(L, {i + 1}, LUA_TTABLE);")
            lua_code.append(f"    {ptype} {pname} = {{}};")
            for field in type_definitions[ptype]:
                lua_code.append(f"    lua_getfield(L, {i + 1}, \"{field}\"); {pname}.{field} = lua_tonumber(L, -1); lua_pop(L, 1);")
        else:
            lua_code.append(f"    {ptype} {pname} = ({ptype})luaL_checknumber(L, {i + 1});")

    # Call the C function
    param_names = ', '.join(pname for _, pname in params)
    if return_type != "void":
        lua_code.append(f"    {return_type} result = {func_name}({param_names});")
        lua_code.append(f"    lua_pushnumber(L, result);")
        lua_code.append("    return 1;")
    else:
        lua_code.append(f"    {func_name}({param_names});")
        lua_code.append("    return 0;")

    lua_code.append("}")
    return '\n'.join(lua_code)

def generate_init_function(functions):
    lines = ["void sbind_init(lua_State* L) {"]
    for func_name, lua_name in functions:
        lines.append(f"    lua_pushcfunction(L, sbindfun_{func_name}); lua_setglobal(L, \"{lua_name}\");")
    lines.append("}")
    return '\n'.join(lines)

#--------------------------------
# Documentation generation
#--------------------------------
def generate_documentation(functions, output_file):
    with open(output_file, 'w') as f:
        f.write("# Lua bindings\n\n") # Title
        for func_name, lua_name, return_type, params in functions:
            f.write(f"### {lua_name}()\n")
            f.write(f"- **C Function:** `{func_name}`\n")
            f.write(f"- **Return Type:** `{return_type}`\n")
            f.write("- **Parameters:**\n")
            if params:
                for ptype, pname in params:
                    f.write(f"  - `{ptype} {pname}`\n")
            else:
                f.write("  - None\n")
            f.write("\n---\n\n")

    print(f"Generated documentation -> {output_file}")

#--------------------------------
# Main
#--------------------------------
def main():
    parser = argparse.ArgumentParser(description="Simple Lua Binding Generator for C headers.")
    parser.add_argument("headers", nargs='+', help="Header files to parse.")
    parser.add_argument("-o", "--output", default="bindings.h", help="Output header file.")
    parser.add_argument("-d", "--doc", help="Generate documentation as .md file.")
    args = parser.parse_args()

    type_definitions = {}

    functions = process_header_files(args.headers, type_definitions)

    if not functions:
        print("Warning: No functions to bind!")

    if args.output:
        generate_header_file(args.output, args.headers, functions, type_definitions)

    if args.doc:
        generate_documentation(functions, args.doc)

if __name__ == "__main__":
    main()
