from typing import List
import os

from base_classes import Tool, ToolUseStatus


class FileManagerTool(Tool):
    def __init__(self, path="."):
        self.path = path

    def get_name(self,):
        return "FILE_MANAGER"

    def get_short_description(self,):
        return "The file manager tool can move between directories and view/open files in them"

    def get_commands(self,):
        return [
            ("LS", "List the current directory's contents", self.list, ()),
            ("PWD", "Print the current directory's path", self.pwd, ()),
            ("CD", "Change directory", self.cd, ("Relative path to new directory",)),
            ("WRITE", "Write a file", self.write, ("File name", "file contents")),
            ("READ", "Read a file", self.read, ("File name",)),
        ] + super().get_commands()

    def list(self, args: List[str]):
        return ToolUseStatus.SUCCEEDED, "These files are in the current directory: '%s'" % ", ".join(os.listdir(self.path))
    
    def pwd(self, args: List[str]):
        return ToolUseStatus.SUCCEEDED, "The current directory is %s" % os.path.realpath(self.path)

    def cd(self, args: List[str]):
        new_path = os.path.realpath(os.path.join(self.path, args[0]))
        if os.path.exists(new_path):
            self.path = new_path
            return ToolUseStatus.SUCCEEDED, "Changed the current directory to %s" % os.path.realpath(self.path)
        else:
            return ToolUseStatus.FAILED_REPROMPT, "%s is not a valid path, please try again with a different path"

    def write(self, args: List[str]):
        try:
            with open(args[0], "w+") as f:
                f.write(" ".join(args[1:]))
            return ToolUseStatus.SUCCEEDED, "Successfully wrote to %s" % args[0]
        except IOError as e:
            return ToolUseStatus.FAILED_REPROMPT, "File opening failed because of %s" % e

    def read(self, args: List[str]):
        try:
            with open(args[0], "r") as f:
                s = f.read()
            return ToolUseStatus.SUCCEEDED, "The file %s's contents are: '%s'" % (args[0], s)
        except IOError as e:
            return ToolUseStatus.FAILED_REPROMPT, "File opening failed because of %s" % e
    
    def get_two_examples(self,):
        ex1 = "user: What files are on my desktop\nassistant: %FILE_MANAGER CD ~/Desktop\nsystem: Changed the current directory to ~/Desktop\nassistant: %FILE_MANAGER LS\nsystem: These files are in the current directory: 'dogs.txt, example.png'\nassistant: The files dogs.txt and example.png are on your desktop\nuser: What is in dogs.txt\nassistant: %FILE_MANAGER READ dogs.txt\nsystem: The file dogs.txt's contents are: 'golden retriever, german shepherd, french bulldog'\nassistant: The dogs.txt file includes the names of three dog breeds"

        ex2 = "user: Can you make a list of where I want to go on vacation?\nassistant: Sure, which destinations did you have in mind?\nuser: I want to go Mexico between Janurary 1st and 4, Germany between March 7th and 12th, and Italy between March 12th and 21st.  Can you save that information with my documents\nassistant: %FILE_MANAGER CD ~/Documents\nsystem: Changed the current directory to ~/Documents\nassistant: %FILEMANAGER WRITE vacations.txt Mexico: 1/1-1/4\nGermany: 3/7-3/12\nItaly: 3/12-3/21\nsystem: Successfully wrote to vacations.txt\nassistant: I noted those destinations in your documents folder"

        return ex1, ex2


