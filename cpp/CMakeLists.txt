cmake_minimum_required(VERSION 3.20)
project(chaoshash LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find pybind11 installed via pip
find_package(pybind11 CONFIG REQUIRED)

# Build the Python extension module
pybind11_add_module(chaoshash chaos_stub.cpp)

# Direct build output so it is placed into src/chaos/
set_target_properties(chaoshash PROPERTIES
    OUTPUT_NAME "chaoshash"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/chaos"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/chaos"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/chaos"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/chaos"
)

# Post-build copy to src/ so it is also available as a top-level module in editable installs
add_custom_command(TARGET chaoshash POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:chaoshash>
        "${CMAKE_CURRENT_SOURCE_DIR}/../src/"
    COMMENT "Copying chaoshash extension to src/ for top-level import"
)

install(TARGETS chaoshash
    DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}/../src/chaos"
)
