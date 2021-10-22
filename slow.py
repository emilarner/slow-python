import os
import sys

def debug(what):
    print(f"DEBUG: {what}")

def get_rid_of(this, what) -> str:
    return this.replace(what, "")

def get_parentheses(keyword, line):
    encasing = line.strip(keyword + " ")
    
    # Complain
    if (not encasing.startswith("(") or not encasing.endswith(")")):
        raise AttributeError("must be completely enclosed in parentheses")

    return encasing.strip("(").strip(")")

class SlowArgument:
    def __init__(self, name):
        self.name = name
        self.type = None



def parse_arguments(line) -> [SlowArgument]:
    "Parses an argument list arg1: type1, arg2: type2, ... into an array of SlowArguments"

    if (line == ""):
        return []

    result: [SlowArgument] = []

    for arg in line.split(","):
        argument = SlowArgument(arg.strip().split(":")[0])

        if (":" in arg):
            argument.type = ":".join(arg.split(":")[1:]).lstrip()

        result.append(argument)

    return result


    
# What blocks have the end terminator?
slow_blocks = [
    "class",
    "function",
    "python",
    "while",
    "for",
    "foreach",
    "switch",
    "if",
    "else if",
    "else",
    "enum",
    "case",
    "default"
]

class SlowEndChecker:
    """While adding code to a list, make sure we do not end prematurely, by seeing if 
    that code has an end block because of a block within it. 
    """

    def __init__(self):
        self.vstack = SlowStack()

    def parse_line(self, line) -> bool:
        "Parse a line. If this function returns True, you have hit a genuine end keyword for your block."
        if (line.split(" ")[0] in slow_blocks):
            self.vstack.push(line.split(" ")[0])

        if (line == "end"):
            if (len(self.vstack) == 0):
                return True
            
            self.vstack.pop()




class SlowObjectTypes:
    "Is it an enum or a class?"

    Enum = "enum"
    Class = "class"


class SlowTypes:
    "Build-in type names"

    Bool = "bool"
    Function = "function"
    Text = "text"
    Number = "number"
    Null = "null"
    Void = "void"

primitive_types = [
    SlowTypes.Bool,
    SlowTypes.Function,
    SlowTypes.Text,
    SlowTypes.Number,
    SlowTypes.Null,
    SlowTypes.Void
]

# The return value of every recursive interpret_line() call.
class SlowEntity:
    def __init__(self, _type, value):
        self.type = _type
        self.value = value

class SlowVariable:
    def __init__(self, name, value: SlowEntity, _type = SlowTypes.Bool):
        self.value: SlowEntity = value
        self.type = _type
        self.explicit_type = None

        self.name = name
        self.constant = False
        self.castable = False

class SlowReturn:
    "This is used to differentiate an entity from an actual return value."

    def __init__(self, value):
        self.value = value


class SlowScope:
    "Superclass for describing a scoped object. This may be used standalone (as in for global variables)."

    def __init__(self):
        self.entities = {
            "variables": {},
            "objects": {},
            "functions": {}
        }

        self.checker = SlowEndChecker()



class SlowFunction(SlowScope):
    def __init__(self):
        super().__init__()

        self.name = None 
        self.ret_type = None
        self.arguments = []
        self.code = []
        self.lambda_function = False

        self.python = None

        self.defining = False
        self.implementation = None

class SlowClass(SlowScope):
    def __init__(self, name):
        super().__init__()

        self.name = name
        self.defining = False
        self.implementation = None

    def make_instance(self, init = {}):
        new = SlowClass(self.name)
        
        # Provide a separate variable space for the new class instance.
        # Function definitions and object definitions remain.

        new.entities = self.entities
        new.entities["variables"] = self.entities["variables"].copy()

        new.entities["variables"].update(init)

        new.defining = False

        return new

class SlowPythonBlock(SlowScope):
    def __init__(self):
        super().__init__()


class SlowEnum(SlowScope):
    def __init__(self, name):
        super().__init__()

        self.name = name
        self.counter = 0

        self.defining = False
        self.implementation = None


class SlowStack:
    def __init__(self):
        self.stack: list = []

    def pop(self):
        v = self.stack[0]
        self.stack.pop(0)
        return v

    def push(self, value):
        self.stack.insert(0, value)

    def __getitem__(self, index):
        return self.stack[index]

class SlowIfElseIfElse(SlowScope):
    """This class keeps track of the chains of if and else statements so that else would work properly.
    It resides on self.stack[1] whenever you're in an if, else if, or else
    """

    def __init__(self):
        super().__init__()
        self.all_lost = True
        # Assume that else will execute at first; if any condition within if or else if is true,
        # then else WILL NOT execute. 

        self.done = False

class SlowIf(SlowScope):
    def __init__(self, condition: bool):
        super().__init__()

        self.condition = condition

class SlowElseIf(SlowScope):
    def __init__(self):
        super().__init__()

        self.condition = None
        self.running = False

class SlowElse(SlowScope):
    def __init__(self):
        super().__init__()
        self.running = True


class SlowWhile(SlowScope):
    def __init__(self, condition):
        super().__init__()

        self.condition: str = condition
        self.code: [str] = []
        self.definition = True

class SlowFor(SlowScope):
    def __init__(self, initialization, condition, post):
        super().__init__()

        self.initialization = initialization
        self.condition = condition
        self.post = post

        self.code = []
        self.running = False

class SlowInterpreter:
    def __init__(self, iname):
        self.iname = iname

        self.stack = SlowStack()
        self.stack.push(SlowScope())
        self.scope = self.stack[0]

        self.path = SlowStack()

    def type_exists(self, name) -> bool:
        "Determine whether a type exists within the current scope context, as well as from primitive types."

        if (name in primitive_types):
            return True

        if (self.get_entity("objects", name) != None):
            return True

    def get_object_type(self, name):
        "Determine whether a given object is a class, enum, or something else."

        obj = self.get_entity("objects", name)
        
        if (isinstance(obj, SlowEnum)):
            return SlowObjectTypes.Enum

        if (isinstance(obj, SlowClass)):
            return SlowObjectTypes.Class

        return None
        

    def error(self, message):
        "Complain about an error in the Slow Programming Language and exit fatally."

        sys.stderr.write(f"Slow Programming Language Error: {message}\n")
        os._exit(-1)

    def warning(self, message):
        "Make a warning about a bad programming practice..."

        sys.stderr.write(f"Slow Programming Language Warning: {message}\n")

    def get_entity(self, section, name):
        "Get an entity, starting from the bottom of the stack, returning None if the item cannot be found."

        # Reverse for loop. 
        for i in range(len(self.stack.stack) - 1, -1, -1):
            if (name in self.stack[i].entities[section]):
                return self.stack[i].entities[section][name]
            
        return None

    def set_entity(self, section, name, value: SlowEntity):
        "Set an entity, starting at the start of the stack, per scope rules in Slow."
        index = 0

        if (isinstance(self.stack[0], SlowPythonBlock)):
            index = 1

        self.stack[index].entities[section][name] = value

    def get_var(self, name):
        "Get a variable, returning None if the variable could not be found."

        return self.get_entity("variables", name)

    def set_var(self, name, value: SlowVariable):
        "Set a variable; additionally, complain if the value is void."

        if (value.type == SlowTypes.Void):
            self.error("You may not use the return value of void--it doesn't mean anything!")

        self.set_entity("variables", name, value)


    def define_function(self, name, arguments: [SlowArgument], ret = None):
        "Define a function in the Slow Programming Language."

        if (ret != None):
            if (not self.type_exists(ret)):
                self.error(f"Typename '{ret}' does not exist... are you missing an import?")

        func = SlowFunction()
        func.name = name
        func.arguments = arguments
        func.ret_type = ret
        func.defining = True

        self.stack[0].entities["functions"][name] = func

        func.implementation = self.stack[0].entities["functions"][name]

        self.stack.push(func)
        
    def append_function(self, line):
        "Append a line to a function implementation on the stack."

        function = self.stack[0]
        function.implementation.code.append(line)

    
    def run_function(self, func: SlowFunction, args):
        "Run a function wthin its own scope, providing arguments and/or class pointer ('this')."
        
        # Extraneous arguments
        if (len(args) > len(func.arguments)):
            self.error("You cannot pass more arguments than the function has defined.")

        # Lacklustre amount of arguments
        if (len(args) < len(func.arguments)):
            self.error("You are missing required positional arguments for that function.")

        # Function variable space. 
        newscope = SlowFunction()

        
        # Pass the arguments into the function's variable space.
        # These are positional arguments.  
        for i in range(len(args)):
            name = func.arguments[i]
            entity = self.interpret_line(args[i])

            newscope.entities["variables"][name] = SlowVariable(name, entity, entity.type) 

        
        # If we are running inside of a class, expose the variable 'this' as a reference to the
        # current class.
        if (isinstance(self.stack[0], SlowClass)):
            class_info: SlowClass = self.stack[0]
            class_type = class_info.name

            newscope.entities["variables"]["this"] = SlowVariable("this", SlowEntity(class_type, class_info))

        self.stack.push(newscope)

        # Execute each line of code in the function
        for line in func.code:
            # We have reached a return value.
            if (isinstance((x := self.interpret_line(line)), SlowReturn)):
                if (func.ret_type != None):
                    if (x.value.type != func.ret_type):
                        self.error(f"Function returned '{x.value.type}' when it only is supposed to return '{func.ret_type}'")
            
                return x.value

        self.stack.pop()

        # By default, functions return void if they do not have a return!
        return self.void()


    def null(self):
        "Return null."

        return SlowEntity(SlowTypes.Null, None)

    def void(self):
        "Return void."

        return SlowEntity(SlowTypes.Void, None)

    def interpret_line(self, line: str):
        "Interpret a line--or segment--of code."

        line = line.strip()

        if (line == "" or line == " "):
            return self.null()


        keywords = line.split(" ")
        klen = len(keywords)
        #           ^^^ add quotation delimitation later.

        keyword = keywords[0]


        # Function definition. 
        if (isinstance(self.stack[0], SlowFunction)):

            function = self.stack[0]
            if (function.defining):
                if (keyword != "end" and not function.checker.parse_line(line)):
                    self.append_function(line)
                    return self.null()

                # When end is reached, stop defining the function. 
                function.defining = False


        # Enum definition
        if (isinstance(self.stack[0], SlowEnum)):
            enum = self.stack[0]
            if (enum.defining):
                # Every line becomes a variable within the enum, unless that line is 'end'.
                if (keyword != "end"):
                    enum.entities["variables"][keyword] = SlowVariable(None, SlowEntity(SlowTypes.Number, enum.counter), SlowTypes.Number)
                    enum.counter = enum.counter + 1
                    return self.null()
                
                enum.defining = False


        # Class definition
        if (isinstance(self.stack[0], SlowClass)):
            class_def = self.stack[0]
            if (class_def.defining):
                # Only these instructions are allowed within the definition of a class.
                if (keyword not in ["let", "end", "function", "enum", "public", "private", "static"]):
                    self.error(f"Keyword '{keyword}' not allowed within class definition.")



        # Multi-line Python definition. 
        if (isinstance(self.stack[0], SlowPythonBlock)):
            if (keyword != "end"):
                exec(line, globals().update({
                    "interpreter": self,
                    "get": self.get_entity,
                    "set": self.set_entity,
                    "get_var": self.get_var,
                    "set_var": self.set_var
                }))


                return self.null()

        # Check if we're done.
        if (isinstance(self.stack[0], SlowIfElseIfElse)):
            # If the next instruction is not an else if or an else, close the conditional block.
            # UNLESS, previously, an else block came about, terminating everything--DO NOT
            # LET THEM MAKE ANYMORE!!!!


            if (not line.startswith("else if") and keyword != "else" or self.stack[0].done):
                self.stack.pop()


            if (keyword == "if"):
                self.error("if can only be used once--did you mean 'else if'?")



        # If statement. 
        if (isinstance(self.stack[0], SlowIf)):
            if (keyword != "end"):
                # Do not run the lines of code below, if the condition is False, unless we are ending the block.
                if (not self.stack[0].condition):
                    return


        # Else if statement handler
        if (isinstance(self.stack[0], SlowElseIf)):
            if (keyword != "end" and self.stack[0].running):
                # If the previous if/else if statement evaluated to true, don't run!
                # Additionally, if the condition was true of the else if run it,
                # then ignore all subsequent attempts to evaulate any else ifs within this block.

                if (not self.stack[1].all_lost and not self.stack[0].condition):
                    return 
                
                # If the condition given to you didn't evaulate to true, don't run!
                if (not self.stack[0].condition):
                    return

        # Else--if all is lost, as I like to remind myself--handler
        if (isinstance(self.stack[0], SlowElse)):
            if (keyword != "end" or self.stack[0].running):
                self.stack[1].done = True
                
                # If any of the if/else if statements evaulated to true, DO NOT RUN THE CODE FOR ELSE.
                if (not self.stack[1].all_lost):
                    return

        # While -- Handle while
        if (isinstance(self.stack[0], SlowWhile)):
            # We're defining the code for it.
            if (self.stack[0].definition):
                if (keyword != "end"):
                    self.stack[0].code.append(line)
                    return

                # End has reached, let us actually run this shit!
                self.stack[0].definition = False

                # While the condition is True
                while self.interpret_line(self.stack[0].condition).value:

                    # Run each line of code, over and over again!
                    for line in self.stack[0].code:
                        self.interpret_line(line)

                # While is no more!
                self.stack.pop()
                return


        # For -- for detection
        # Not that important.
        if (isinstance(self.stack[0], SlowFor)):
            # We might want to execute things within the scope of the for-loop block, but
            # not necessarily add it to the code list.
            if (self.stack[0].running):
                # Add Slow code to it.
                if (keyword != "end"):
                    self.stack[0].code.append(line)
                    return

                self.stack[0].running = False

                # While the condition is true.
                while (self.interpret_line(self.stack[0].condition).value):
                    for line in self.stack[0].code:
                        self.interpret_line(line)

                    # Every time, execute our post instructions at the end.
                    self.interpret_line(self.stack[0].post)

                self.stack.pop()
                return

            

        # Text literal.
        if (line.startswith("`")):
            if (not line.endswith("`")):
                self.error("Text literal must be encased in backticks (`).")

            text = line.strip("`")
            return SlowEntity(SlowTypes.Text, text)

        # String literal -- make class 
        if (line.startswith("\"")):
            if (not line.endswith("\"")):
                self.error("String literal must be entirely encased in quotations.")

            text = line.strip("\"")
            return SlowEntity("String", self.get_entity("objects", "String").make_instance({
                "text": SlowVariable("text", SlowEntity(SlowTypes.Text, text))
            }))

        # Number literal
        if (line.isnumeric()):
            return SlowEntity(SlowTypes.Number, int(keyword))

        # Null literal
        if (keyword == "null"):
            return self.null()

        # Bool literals
        if (keyword == "true"):
            return SlowEntity(SlowTypes.Bool, True)

        if (keyword == "false"):
            return SlowEntity(SlowTypes.Bool, False)

        # Class initialization operator
        if (keyword == "new"):
            info = line.strip("new ")
            class_name = info.split("(")[0]
            argslist = info.strip(class_name)

            # Complain about the programmer not respecting the structual rigidity of the language.
            if (not argslist.startswith("(") or not argslist.endswith(")")):
                self.error("Class initialization must be encased in parentheses--no matter what!")
            

            args = [x.strip() for x in argslist.strip("(").strip(")").split(",")]
            object_type = self.get_object_type(class_name)

            # Annoying error that has an easy remedy.
            if (args == ['']):
                args = []

            # Invalid object type.
            if (object_type != SlowObjectTypes.Class):
                self.error("The 'new' operator may only be used to initialize classes--this isn't a class!")

            new_instance = self.get_entity("objects", class_name).make_instance()

            # Call ~init
            self.stack.push(new_instance)
            if ((func := self.get_entity("functions", "~init")) != None):
                self.run_function(func, args)
            else:
                self.warning("Class doesn't have a constructor.")

            self.stack.pop()

            return SlowEntity(class_name, new_instance)

        # Method/member access operator
        if ("." in keyword):
            name = line.split(".")[0]
            other = ".".join(line.split(".")[1:])

            block = self.interpret_line(name)

            # If it is not a class or an enum
            if (not isinstance(block.value, SlowEnum) and not isinstance(block.value, SlowClass)):
                self.error("The access operator (.) may not be used on objects other than classes or enums.")

            block.value.defining = False
            self.stack.push(block.value)
            val = self.interpret_line(other)

            self.stack.pop()
            return val

        # Returning a variable.
        if (self.get_var(keyword) != None):
            value = self.get_var(keyword)

            # I stress this enough: void shall not be used like that!
            if (value.type == SlowTypes.Void):
                self.error("You may not use the return value of void--it doesn't mean anything!")

            # Setting a variable!
            if ("=" in line):
                to = self.interpret_line(line.split("=")[1].strip())

                # Cannot reassign a constant variable.
                if (value.constant):
                    self.error("Reassignment of const variable is illegal.")

                value.value = to

            return value.value


        # Objects: enum and classes
        if (self.get_entity("objects", keyword) != None):
            value: SlowEnum = self.get_entity("objects", keyword)
            return SlowEntity(value.name, value)

        # Function 
        if (self.get_entity("functions", keyword) != None):
            return SlowEntity(SlowTypes.Function, self.get_entity("functions", keyword))

        # Function call
        if ("(" in keyword):

            # Arbitrary requirement for enclosing of parentheses.
            if (not line.endswith(")")):
                self.error("Function call must be completely enclosed within parentheses.")

            name = line.split("(")[0].strip()
            func = None

            # Function does not exist.
            if ((func := self.get_entity("functions", name)) == None):

                # Maybe we are calling a variable, which is a reference to a function. 
                if ((func := self.get_entity("variables", name)) == None):
                    self.error(f"Function '{name}' is uncallable: it does not exist.")

                # It is a variable... but it isn't a callable type!
                if (func.value.type != SlowTypes.Function):
                    self.error("Calling a variable not of type 'function'.")

                func = func.value.value

            # Parse positional arguments
            # TO DO: parse keyword arguments.
            args = [str.strip(x) for x in line.strip(name).strip().strip("(").strip(")").split(",")]
            
            if (args == [""]):
                args = []

            return self.run_function(func, args)


        # Print an entity and its type. This is for debugging purposes.
        if (keyword == "what"):
            expression = self.interpret_line(keywords[1])
            print(f"Value:\n{expression.value}\n\nType:\n{expression.type}")
            return expression


        # Multi-line block of Python execution.
        if (keyword == "python"):
            print("Hey")
            self.stack.push(SlowPythonBlock())
            return self.null()


        # Start defining a class. 
        if (keyword == "class"):
            name = get_rid_of(line, "class ")

            class_def = SlowClass(name)
            class_def.defining = True
            self.stack[0].entities["objects"][name] = class_def
            class_def.implementation = self.stack[0].entities["objects"][name]
            
            self.stack.push(class_def)
            return self.null()

        # Start defining an enumeration.
        if (keyword == "enum"):
            line = line.strip("enum ")
            name = line

            # Keep the enum in question associated with the scope above.
            enum = SlowEnum(name)
            self.stack[0].entities["objects"][name] = enum
            enum.implementation = self.stack[0].entities["objects"][name]
            enum.defining = True

            self.stack.push(enum)
            return self.null()

        # Do nothing: nop.
        if (keyword == "pass"):
            return self.null()


        # Start defining a function. 
        if (keyword == "function"):
            line = get_rid_of(line, "function ")
            name = line.split("(")[0].strip()
            
            arguments = line.strip("(")
            arguments = line.strip(")")
            
            arguments = [str.strip(x) 
            for x in line.strip(name).strip().strip("(").strip(")").split("->")[0].strip().split(",")]

            if (arguments == [""]):
                arguments = []


            return_type = None

            if ("->" in line):
                return_type = line.split("->")[1].strip()

            self.define_function(name, arguments, ret = return_type)
            return self.null()


        # Return a value from a function. 
        if (keyword == "return"):
            if (not isinstance(self.stack[0], SlowFunction)):
                self.error("'return' keyword used outside of function.")

            value = line.replace("return ", "")

            #if (self.stack[0].ret_type == "void"):
            #    print(self.stack[0].ret_type)
            #    if (value != ""):
            #        self.error("Returning a value from a function returning void.")
            #
            #    return SlowReturn(self.void())

            expression = self.interpret_line(value)
            return SlowReturn(expression)

        # Check if a condition evaluates to the boolean 'true'
        if (keyword == "if"):
            try:
                condition = self.interpret_line(get_parentheses("if", line))
            except AttributeError:
                self.error("The condition inside an if-statement must be encased in parentheses.")
            
            # Complain if condition did not return boolean.
            if (condition.type != SlowTypes.Bool):
                self.error("if can only operate on expressions returning a bool.")
            
            main_block = SlowIfElseIfElse()
            
            if (condition.value):
                main_block.all_lost = False

            self.stack.push(main_block)
            self.stack.push(SlowIf(condition.value))

            return self.null()

        # Let us try again before going to the else clause.         
        if (line.startswith("else if")):
            if (not isinstance(self.stack[0], SlowIfElseIfElse)):
                self.error("'else if' cannot be used without an initial 'if' statement!")

            try:
                slow_elif = SlowElseIf()
                self.stack.push(slow_elif)
                condition = SlowEntity(SlowTypes.Bool, False) if (not self.stack[1].all_lost) else self.interpret_line(get_parentheses("else if", line))
                slow_elif.condition = condition.value
            except AttributeError as error:
                self.error("The condition inside an else if statement must be encased in parentheses.")

            # Complain if condition did not return boolean.
            if (condition.type != SlowTypes.Bool):
                self.error("else if can only operate on expressions returning a bool.")

            # It's not all lost to else!
            # We evaluated to True!

            if (condition.value):
                self.stack[1].all_lost = False

            # Else If must be explicitly activated, because we have to run the interpreter
            # in order to get the conditional--if it runs while we're doing that, everything is fucked.

            self.stack[0].running = True
            return self.null()

        # else - if nothing else 
        if (line == "else"):
            if (not isinstance(self.stack[0], SlowIfElseIfElse)):
                self.error("'else' cannot be used without an initial 'if' statement, sorry.")
            
            self.stack.push(SlowElse())
            return self.null()
            

        # while - Start a while loop. 
        if (keyword == "while"):
            try:
                condition = get_parentheses("while ", line)
            except AttributeError:
                self.error("The condition inside 'while' must be encased in parentheses.")

            wh = SlowWhile(condition)
            self.stack.push(wh)
            return self.null()


        # for - For loop (initialization; condition; after)
        if (keyword == "for"):
            try:
                body = get_parentheses("for ", line)
            except AttributeError:
                self.error("The body of a for loop must be encased in parentheses.")

            init, cond, post = [x.strip() for x in body.split(";")]

            sfor = SlowFor(init, cond, post)
            self.stack.push(sfor)
            sfor.init = self.interpret_line(init)
            sfor.running = True

            return self.null()

            

        # Raw text output; only useful for debugging purposes. 
        if (keyword == "_out"):
            print(self.interpret_line(keywords[1]).value)
            return self.null()


        # Declare new variable, also returning the value of that variable. 
        if (keyword == "let"):
            if (isinstance(self.stack[0], SlowClass)):
                if (self.stack[0].defining):
                    self.stack[0].defining = False

            const = False
            castable = False
            etype = None

            name = line.split("=")[0].strip().strip("let ")

            # Check for const
            if ("const " in name):
                const = True
                name = name.replace("const ", "")

            # For castable
            if ("castable " in name):
                castable = True
                name = name.replace("castable ", "")

            # For an explicit type.
            if (":" in name):
                etype = name.split(":")[1].lstrip()
                name = name.split(":")[0].strip()

            # Check for an existing variable.            
            for section in ["variables", "objects", "functions"]:
                if (self.get_entity(section, name) != None):
                    self.error("Redefinition of variable, keyword, object, or function.")

            value = self.interpret_line(line.split("=")[1].strip())
            var: SlowVariable = SlowVariable(name, value, value.type)
            
            var.constant = const
            var.castable = castable
            var.explicit_type = etype

            self.set_var(name, var)

            # ? - It just works, though! Don't remove it!
            if (isinstance(self.stack[0], SlowClass)):
                if (not self.stack[0].defining):
                    self.stack[0].defining = True

            return value
    




        # Pop a block off of the stack, ending it.
        # Harder than you thought, though! 
        if (keyword == "end"):
            if (klen > 1):
                self.error("The 'end' keyword takes no arguments (it is by itself).")

            if (isinstance(self.stack[0], SlowClass)):
                self.stack[0].defining = False

            if (len(self.stack.stack) > 1):
                self.stack.pop()

            return self.null()
            


        # Operators - PEMDAS is the bane of my existence.

        # Greater than
        if (">" in line):
            # primitive; for debug
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split(">")]]

            return SlowEntity(SlowTypes.Bool, left.value > right.value)

        if (">" in line):
            # primitive; for debug
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split(">=")]]

            return SlowEntity(SlowTypes.Bool, left.value >= right.value)

        # Less than
        if ("<" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("<")]]
            return SlowEntity(SlowTypes.Bool, left.value < right.value)

        if ("<=" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("<=")]]
            return SlowEntity(SlowTypes.Bool, left.value <= right.value)


        # Equal operator
        if ("==" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("==")]]
            return SlowEntity(SlowTypes.Bool, left == right)

        # Equal operator
        if ("!=" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("!=")]]
            return SlowEntity(SlowTypes.Bool, left != right)
        
        # Object is the same
        if ("===" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("===")]]
            return SlowEntity(SlowTypes.Bool, left.value is right.value)

        if ("!==" in line):
            left, right = [self.interpret_line(x) for x in [x.strip() for x in line.split("!==")]]
            return SlowEntity(SlowTypes.Bool, left.value is not right.value)

        # Increment
        if ("++" in keyword): 
            pre = self.interpret_line(keyword.split("++")[0])
            pre.value += 1
            return SlowEntity(SlowTypes.Number, pre.value)


        # Decrement
        if ("--" in keyword): 
            pre = self.interpret_line(keyword.split("--")[0])
            pre.value -= 1
            return SlowEntity(SlowTypes.Number, pre.value)

        self.error(f"'{keyword}' is not defined or is not a valid keyword within the Slow Programming Language.")
