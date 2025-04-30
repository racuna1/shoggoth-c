__author__ = "Mitchell Buckner"
__author__ = "Ruben Acuna"

import subprocess
import time

TIMEOUT = 5

class ConsoleProgramRunner:
    """
    Class to run a program

    :function push_runtime_cmd: add a string representing an input to write to the stdin during program execution.
        No newline chars needed
    :function push_program_arg: add arguments to execute the program with, pass this an array of strings.
        Each string is an argument piece. ex: ['-i', 'fileName.bmp']
    :function run: executes the program, do this once you've supplied all the args and commands you want

    NOTE: All file pathing is based upon the root directory of the python program, not the submissions folder where the code is!

    """

    def __init__(self, program_path):
        self.program_path = program_path
        self.runtime_commands = []
        self.args = []

    def push_runtime_cmd(self, command):
        self.runtime_commands.append(command)

    def push_program_arg(self, arg):
        self.args.append(arg)

    def push_program_args(self, args):
        self.args += args

    def run(self) -> dict:
        """
        :return: dict for the result data, contains stdin, stdout, stderr, and the exit_code
        """
        process = subprocess.Popen([self.program_path] + self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        start_time = time.time()
        while True:
            if process.poll() is not None:  # If process is done
                break
            if time.time() - start_time > TIMEOUT:  # TIMEOUT-second timeout
                process.terminate()
                raise TimeoutError("The process took too long and was terminated.")

            # Write the required input for the process
            try:
                for cmd in self.runtime_commands:
                    process.stdin.write(cmd + "\n")

                process.stdin.flush()  # Make sure to flush the buffer
            except BrokenPipeError:
                # This exception occurs when the process has already terminated and no longer accepts input.
                break

            time.sleep(0.1)  # Sleep briefly to avoid hogging CPU

        # Wait for the process to finish
        process.wait()

        # grabbed stderr and added it to result dict. This never actually returns anything though, as it gets stuck in the buffer
        stdout, stderr = process.communicate()

        result = {
            "stdin": self.runtime_commands[:],
            "stdout": stdout.splitlines(),
            "stderr": stderr,
            "exit_code": process.returncode,
        }

        return result