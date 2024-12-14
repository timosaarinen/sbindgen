#include <stdio.h>
#define LUA_IMPL
#include "minilua.h"
#include "test.h"
#include "bind.h"

// TODO: better way to check if all binded functions are called? # of binds from sbindgen?
#define NUM_BINDED_FUNCTIONS 3
static int test_num_binded_functions_called = 0; 
static int test_num_failed_expects = 0;

#define TEST_BINDED_FUNC_COMPLETED() \
    test_num_binded_functions_called++

#define TEST_EXPECT(expr, msg) do { \
    if (!(expr)) { \
        test_num_failed_expects++; \
        printf("%s✗ TEST FAILED:%s %s\n", RED, RESET, msg); \
    } \
} while(0)

#define TEST_ASSERT(expr, msg) do { \
    if (!(expr)) { \
        printf("%s✗ TEST FAILED:%s %s\n", RED, RESET, msg); \
        exit(1); \
    } \
} while(0)

// Terminal color codes
#ifdef _WIN32
    #define RED ""
    #define GREEN ""
    #define RESET ""
#else
    #define RED "\033[1;31m"
    #define GREEN "\033[1;32m"
    #define RESET "\033[0m"
#endif

//--------------------------------
// Functions binded to Lua
//--------------------------------
void hello(void) {
    printf("Hello from C!\n");
    TEST_BINDED_FUNC_COMPLETED();
}

int get_answer(void) {
    TEST_BINDED_FUNC_COMPLETED();
    return 42;
}

void print_answer(int answer) {
    printf("The answer is: %d\n", answer);
    TEST_EXPECT(answer == 42, "Answer should be 42");
    TEST_BINDED_FUNC_COMPLETED();
}

//--------------------------------
// Main
//--------------------------------
int main(void) {
    lua_State* L = luaL_newstate();
    luaL_openlibs(L);
    sbind_init(L);
    luaL_dostring(L,
        "hello()\n"
        "local answer = get_answer()\n"
        "print_answer(answer)"
    );
    lua_close(L);

    TEST_ASSERT(test_num_failed_expects == 0, "Not all tests completed successfully");
    TEST_ASSERT(test_num_binded_functions_called == NUM_BINDED_FUNCTIONS, "Not all binded functions were called");
    printf("%s✓ TEST PASSED:%s [Binding Test] All %d binded functions were called successfully\n", 
           GREEN, RESET, NUM_BINDED_FUNCTIONS);
    return 0;
}
