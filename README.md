# Shoggoth-c
A Gradescope compatible tool for performing automatic assessment of C homework, using static and dynamic analysis. Focuses on providing generic features for assessing systems-level aspects of code submissions.

## Authors
* Mitchell Buckner
* Ruben Acuña


### Config
The config.json is what you need to configure this.

- package_whitelist should contain a list of packages that are allowed, include the chevrons (<>) around the package name
- required_files are all c files the student must submit
- required_headers are all header files the student must submit<br>
- the suite contains all of the test cases. Each one will have a module (name of the python file the test is in), a method (the name of the method running the test or tests), then the list of tests the method runs.
  - Each test must contain a name and the number of points that the test is worth.
- Each test method has an attribute called 'file_version' which represents which version of the student submission shall be used.
  - By default, there are 2 options:
    - 'base' which is exactly the file the student submitted
    - 'logger' which contains macro definitions to route memory calls to the logger functions that log all memory calls (frees, mallocs, etc)
  - You may add more versions, just update the list in the config