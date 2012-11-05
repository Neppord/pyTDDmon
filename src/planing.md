# Features 
 * Multiple guis
 * Time for single test
 * Time for single file
 * Total time for all tests
 * Watching files


# Objects Types 
 * Event
 * UI                       - Listens to update Events from Tests
 * File trigger             - Trigger Events on file Changes
 * Test Object              - Fire events on Tests start and completion
 * TestLog                  - Save info from a test runn


# Messages 
 * Regular File Found       - Path to file
 * Python File Found        - Path to file, and module name
 * Files Changed            - Files found, files Changed
 * Found Tests              - Tests found
 * Starting Test            - Name of test
 * One Test Finished        - time it took
 * All tests have bean run  - The log object


# Emiters
 * File Finder              - From path specs emits found files
 * File Watcher             - From a list of files emits changes
 * Test Finder              - From a list of src files emits tests
 * Test Runner              - From a list o tests emits test start/stop
                            - Also returns when all tests has been run


# Consumers
 * UI                       - Listen for all Messages
 * File Watcher             - Listens for added Files
 * Test Finder              - Listens for added Files
 * Test Runner              - Listens for added sourcfiles
                            - Listens for file changes

