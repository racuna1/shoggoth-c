import importlib
import json
import re
import shutil

import subprocess
import os
import sys
import glob

import helpers
from check_iface_tests import did_iface_tests_compile

from helpers import submission_dir, source_dir, results_dir

__author__ = "Mitchell Buckner"
__author__ = "Ruben Acuna"


# Create the version of the file that tracks malloc and free
def create_tracker_files(file_names):
    lines = [
        "#include \"mallocHooks.h\"\n",
        "#define malloc(size) my_malloc(size, __FILE__, __LINE__)\n",
        "#define free(ptr) my_free(ptr, __FILE__, __LINE__)\n",
        "#define calloc(elements, size) my_calloc(elements, size, __FILE__, __LINE__)\n",
        "#define realloc(ptr, size) my_realloc(ptr, size, __FILE__, __LINE__)\n"
    ]
    for file_name in file_names:
        with open(os.path.join(submission_dir, file_name), 'r') as file:
            content = file.readlines()

        last_include = 0
        for i, line in enumerate(content):
            if "#include" in line:
                last_include = i

        content[last_include:last_include] = lines

        name, extension = file_name.split('.')
        new_name = f"{name}Logger.{extension}"

        with open(os.path.join(submission_dir, new_name), 'w') as file:
            file.writelines(content)


# build the json file after the tests run
def build_json(test_results):
    data = {
        "tests": []
    }

    submission_score = 0
    # weights points relative to the default norm of 30
    SUBMISSION_WEIGHT = 1

    for result in test_results:
        for i, piece in enumerate(result[0]):
            print(result[1][i], result[0][i], result[3][i])

            test = {
                "max_score": (result[1][i] * SUBMISSION_WEIGHT),
                "name": f"{result[2][i]}) {result[0][i]}",
                "number": result[2][i],
                "output": result[4][i]
            }

            if result[3][i] is True:
                submission_score += (result[1][i] * SUBMISSION_WEIGHT)
                test["score"] = (result[1][i] * SUBMISSION_WEIGHT)
            else:
                test["score"] = 0

            data["tests"].append(test)

    data["tests"].sort(key=lambda x: x["name"])

    with open(os.path.join(results_dir, 'results.json'), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

def build_json_on_compilation_fail(test_results):
    data = {
        "output": "Project failed to build (failure to build with C unit tests). Make sure to follow the project outline.",
        "stdout_visibility": "visible",
        "tests": [],

    }

    submission_score = 0
    # weights points relative to the default norm of 30
    SUBMISSION_WEIGHT = 1

    for result in test_results:
        for i, piece in enumerate(result[0]):
            print(result[1][i], result[0][i], result[3][i])

            test = {
                "max_score": (result[1][i] * SUBMISSION_WEIGHT),
                "name": result[0][i],
                # "number": result[2][i],
                "output": result[3][i]
            }

            if result[2][i] is True:
                submission_score += (result[1][i] * SUBMISSION_WEIGHT)
                test["score"] = (result[1][i] * SUBMISSION_WEIGHT)
            else:
                test["score"] = 0

            data["tests"].append(test)

    data["tests"].sort(key=lambda x: x["name"])

    with open(os.path.join(results_dir, 'results.json'), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

    with open(os.path.join(results_dir, 'results.json'), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

# builds the json file for when the autograder fails
def build_json_on_fail(error):

    if("variable length array" in error):
        error = "You have used variable length arrays in your code which have been disallowed for this assignment. Please allocate all variably sized memory in the heap.\n" + error

    data = {
        "score": 0,
        "output": error
    }

    with open(os.path.join(results_dir, 'results.json'), 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)


# looks for all files listed in the required files section of the config
def validate_files(file_list):
    missing_files = []
    for file in file_list:
        if not os.path.exists(os.path.join(submission_dir, file)):
            missing_files.append(file)

    if len(missing_files) > 0:
        build_json_on_fail("Error: Cannot find required file(s): " + str(missing_files))
        print("Error: Cannot find " + str(missing_files) + " files")
        sys.exit(0)


# finds disallowed packages across all the source files
def validate_libraries(files, allowed):
    disallowed_packages = []
    for file_name in files:
        with open(os.path.join(submission_dir, file_name), 'r') as file:
            # may want to replace regex with something more robust
            regex = "#include (?P<name><.*>)"
            found = re.finditer(regex, file.read())

            packages_found = [i.group("name") for i in found if i.group("name") not in allowed]
            disallowed_packages += packages_found

    if len(disallowed_packages) > 0:
        build_json_on_fail("Error: Found Disallowed Libraries: " + ", ".join(disallowed_packages))
        print("Error: Found Disallowed Libraries: " + ", ".join(disallowed_packages))
        sys.exit(0)


# compiles the list of submission_files into a program named program_name
def compile_files(submission_files, program_name, allow_vla, c_version):
    vla_str = ""
    if not allow_vla:
        vla_str = "-Werror=vla "

    # compile each c file into an o file
    for file in submission_files:
        compile_submission_file = f"cd {submission_dir} && gcc -c -std=c{c_version} -O0 {vla_str}{file} -o {file[:-2]}.o"
        result = subprocess.run(compile_submission_file, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            build_json_on_fail("Compilation error compiling {}: ".format(file) + result.stderr)
            print("Compilation error compiling {}: ".format(file) + result.stderr)
            sys.exit(0)

    # get names of every o file from c file names
    o_files = [os.path.splitext(c_file)[0] + ".o" for c_file in submission_files]
    #run compilation
    compile_program = f"cd {submission_dir} && gcc -std=c{c_version} -O0 {' '.join(o_files)} -o {program_name}"
    result = subprocess.run(compile_program, shell=True, capture_output=True, text=True)
    # fail if there was a compilation issue
    if result.returncode != 0:
        build_json_on_fail("Compilation error compiling {}: ".format(o_files) + result.stderr)
        print("Compilation error compiling {}: ".format(o_files) + result.stderr)
        sys.exit(0)


# compiles the student submission
# example is given
def compile_submission(submission_files, allow_vla, c_version):

    compile_files(submission_files, "StudentProgramBase", allow_vla, c_version)

    # copy the mallocHooks files into the submission directory so that they can easily be found
    shutil.copy('mallocHooks.c', submission_dir)
    shutil.copy('mallocHooks.h', submission_dir)

    submission_malloc_files = ['mallocHooks.c']
    for file in submission_files:
        tracker_file = file.replace(".", "Logger.")
        submission_malloc_files.append(tracker_file)
    compile_files(submission_malloc_files, "StudentProgramLogger", allow_vla, c_version)


if __name__ == '__main__':

    # grabs data from config
    with open('config.json', 'r') as file:
        data = json.load(file)

    # compiles file list
    all_files = data['required_files'] + data['required_headers']
    validate_files(all_files)

    # updates file versions list for variations of student files
    helpers.FILE_VERSIONS = data['file_versions']
    print(helpers.FILE_VERSIONS)

    # gets package listing and looks for disallowed packages
    allowed = data['package_whitelist']
    validate_libraries(data['required_files'], allowed)

    create_tracker_files(data['required_files'])

    compile_submission(data['required_files'], data['allow_vla'], data['c_version'])

    results = []

    for method in data["suite"]:
        # remove the malloc log before running each method
        helpers.remove_file("malloc_log.csv")

        result = [[], [], []]
        for test in method["tests"]:
            # print(test)
            result[0].append(test["name"])
            result[1].append(test["points"])
            result[2].append(test["number"])

        module = importlib.import_module(method["module"])

        # calls the methods
        success_list, message_list = helpers.call_or_timeout(getattr(module, method["method"]), len(method["tests"]), method["file_version"])
        result.append(success_list)
        result.append(message_list)

        results.append(result)

        # Check to see that there was no compilation error with the unit tests (if unit testing was used)
        unit_tests_present = data['interface_testing']

        if unit_tests_present:
            unit_tests_ran = did_iface_tests_compile()

            if unit_tests_ran:
                build_json(results)
            else:
                build_json_on_compilation_fail(results)

        elif not unit_tests_present:
            build_json_on_fail(results)

    # remove this at the end just in case
    helpers.remove_file("malloc_log.csv")

