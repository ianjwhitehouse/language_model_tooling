from typing import List

from base_classes import Tool, ToolUseStatus


class PythonTool(Tool):
    def __init__(self):
        pass

    def get_name(self,):
        return "PYTHON"

    def get_short_description(self,):
        return "The Python interpreter can run single line Python programs and includes support for variables"

    def get_commands(self,):
        return [
            ("RUN", "Run a single line python script", self.run, ("Python script",)),
        ] + super().get_commands()

    def run(self, args: List[str]):
        try:
            s = " ".join(args).strip().replace("print", "")
            return ToolUseStatus.SUCCEEDED, "The results of the line of Python is '%s'" % (eval(s))
        except Exception as e:
            return ToolUseStatus.FAILED_REPROMPT, "The line of Python did not run because of %s" % e
    
    def get_two_examples(self,):
        ex1 = "user: What is the sum of the first 10 numbers?\nassistant: %PYTHON RUN sum([i + 1 for i in range(10)])\nsystem: The results of the line of Python is '55'\nnassistant: The sum of the first 10 numbers is 55\n"

        ex2 = "user: Can you make a function that asks the user for a number and multiplies it by 12\nassistant: Sure, a function to do that could be 'lambda : 12 * int(input())'\nuser: Please run that function\nassistant: %PYTHON RUN lambda : 12 * int(input())\nsystem: The results of the line of Python is '60'\nassistant: The product of the number you entered and 12 is 60."

        return ex1, ex2