include (LibMPI)

#==============================================================================
#  PREPARE FOR TESTING
#==============================================================================

file (COPY "./input.nl" 
      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file (COPY "./not_netcdf.ieee" 
      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
      
#==============================================================================
#  DEFINE THE TARGETS AND TESTS
#==============================================================================

set (SRCS basic_tests.F90
          driver.F90
          global_vars.F90
          ncdf_tests.F90
          nc_set_log_level2.c)
	
add_executable (pio_unit_test EXCLUDE_FROM_ALL ${SRCS})
target_link_libraries (pio_unit_test piof)
if ("${CMAKE_Fortran_COMPILER_ID}" STREQUAL "GNU")
    target_compile_options (pio_unit_test
        PRIVATE -ffree-line-length-none)
endif()

add_executable (test_nc4 EXCLUDE_FROM_ALL test_nc4.c)
target_link_libraries (test_nc4 pioc)

if (CMAKE_Fortran_COMPILER_ID STREQUAL "NAG")
   set ( CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -mismatch_all" )
#    target_compile_options (gptl
#        PRIVATE -mismatch_all)
endif ()

add_dependencies (tests test_nc4)
add_dependencies (tests pio_unit_test)

# Test Timeout (4 min = 240 sec)
set (DEFAULT_TEST_TIMEOUT 240)

if (PIO_USE_MPISERIAL)
    add_test(NAME test_nc4
        COMMAND test_nc4)
    add_test(NAME pio_unit_test
        COMMAND pio_unit_test)
    set_tests_properties(pio_unit_test
        PROPERTIES TIMEOUT ${DEFAULT_TEST_TIMEOUT})
else ()
    add_mpi_test(test_nc4
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_nc4
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(pio_unit_test
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/pio_unit_test
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
endif ()

if (PIO_HDF5_LOGGING) 
    target_compile_definitions (pio_unit_test 
        PUBLIC LOGGING)
endif ()