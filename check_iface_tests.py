__author__ = "Michael Deitch"

# Think of this as an "interface" that needs to be implemented for whichever
# unit-testing framework you are choosing for the automated assessment tool.
#
# This interface allows a general approach for discovering if the "iface" (interface)
# level tests ran for the AAT.
#
# You must complete the function however you see fit, as make sure it returns a boolean.
# You may:
#     - Add additional functions (if needed)
#
# You MUST make sure that the final return value in 'did_iface_tests_compile' is representative of the following:
#     - TRUE -> the unit tests you wrote were able to compile with student code, and ran with student code
#     - FALSE -> the unit tests you wrote were NOT able to compile with student code, and they did not run
#
#     Note: The TRUE and FALSE are not implications of passing all (or any) tests, but solely
#     verification that the tests were able to run successfully.



'''
TODO! Must implement for accuracy regarding compilation issues.
'''
def did_iface_tests_compile():
    return True