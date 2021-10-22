import slow
import os
import sys

def main():
    interpreter = slow.SlowInterpreter("Original")

    # The script should parse the file. 
    if (len(sys.argv) > 1):
        for line in open(sys.argv[1], "r"):
            interpreter.interpret_line(line)

    while True:
        interpreter.interpret_line(input("slow>"))


if (__name__ == "__main__"):
    main()