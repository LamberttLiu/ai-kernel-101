cmake_minimum_required(VERSION 3.16)
project(host_device_transfer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_path(ASCENDCL_INCLUDE_DIR acl/acl.h
    HINTS "$ENV{ASCEND_HOME_PATH}"
    PATH_SUFFIXES aarch64-linux/include x86_64-linux/include include)
find_library(ASCENDCL_LIBRARY ascendcl
    HINTS "$ENV{ASCEND_HOME_PATH}"
    PATH_SUFFIXES aarch64-linux/lib64 x86_64-linux/lib64 lib64)

if(NOT ASCENDCL_INCLUDE_DIR OR NOT ASCENDCL_LIBRARY)
    message(FATAL_ERROR "Cannot find acl/acl.h or libascendcl.so; source the CANN set_env.sh first")
endif()

add_executable(transfer_bench main.cpp)
target_include_directories(transfer_bench PRIVATE "${ASCENDCL_INCLUDE_DIR}")
target_link_libraries(transfer_bench PRIVATE "${ASCENDCL_LIBRARY}")
