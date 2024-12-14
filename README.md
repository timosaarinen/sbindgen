# sbindgen

A simple Lua binding generator for C, implemented as a single Python script.

## Usage example
```bash
sbindgen -o bind.h -d bind.md test.h
```
This command generates bind.h and bind.md from test.h, including only functions annotated with the @sbind comment. Include bind.h in one .c file and call sbind_init() with Lua state. See the test directory for more information.

## Testing
Run the following command in the test directory:
```bash
make run
```
