# Imports
from enum import Enum
from typing import Callable, List


class Model:
    def __init__(self,):
        raise NotImplementedError

    def prompt(self, messages: str | List[str]) -> str:
        raise NotImplemetedError


class UserInput(Model):
    def __init__(self,):
        print("Accepting user input")

    def prompt(self, messages):
        for message in messages:
            if message["role"] == "assistant":
                print(" > %s" % message["content"])
            elif message["role"] == "user":
                print("Assistant: %s" % message["content"])
            else:
                print("System: %s" % message["content"])

        # print(messages)
        return input("> ")


ToolUseStatus = Enum("ToolUseStatus", ["FINISHED", "PROMPTING", "FAILED_REPROMPT", "SUCCEEDED"])


class Tool:
    def __init__(self,):
        raise NotImplementedError

    def get_name(self,) -> str:
        raise NotImplementedError

    def get_commands(self,) -> List[tuple[str, str, Callable, tuple[str]]]:
        return [("HELP", "Get help using the %s tool" % self.get_name(), lambda x: x, ())]

    def get_short_description(self,) -> str:
        raise NotImplementedError

    def get_two_examples(self,) -> str:
        raise NotImplemetedError
    
    def get_starter_prompt(self,) -> str:
        raise NotImplemetedError

    def __call__(self, args: List[str]) -> (ToolUseStatus, str):
        cmd = args[0]
        cmds = {c[0]: c[2] for c in self.get_commands()}

        if cmd == "HELP":
            status = ToolUseStatus.SUCCEEDED
            s = "Information on using the %s tool:\n\nAvailable commands:\n%s\n\nExamples using the %s tool %s\n\n%s" % (
                self.get_name(),
                "\n".join(["%s: %s" % (c[0], c[1]) for c in self.get_commands()]),
                self.get_name(),
                self.get_two_examples()[0],
                self.get_two_examples()[1]
            )
            return status, s
        
        elif cmd in cmds:
            try:
                return cmds[cmd](args[1:])
            except IndexError:
                cmds = {c[0]: c[3] for c in self.get_commands()}
                args = cmds[cmd]
                return ToolUseStatus.FAILED_REPROMPT, "Not enough arguments were included to run %%%%s %s.  The %s command requires %s as arguments, separated by spaces" % (
                    self.get_name(), cmd, ", ".join(args)
                )

        else:
            return ToolUseStatus.FAILED_REPROMPT, "%%%s %s is not a valid %s command.  To view all of the commands, run %%%s HELP" % (
                self.get_name(), cmd, self.get_name(), self.get_name()
            )


def main_loop(model1: Model, model2: Model, tools: List[Tool]):
    model1_messages = []
    model2_messages = []

    initial_prompt = r"You are a machine learning agent (refered to as the assistant) in a conversation with 2 other agents - the user, who asks you questions, and the system, which can help you respond and instructs you on your responses.  You can interact with the system using a set of tools.  To use a tool, put % before the name of the tool (i.e. %FILE_MANAGER), followed by the command you want the tool to run.  For example, to list the contents of the current directory, you can run the LIST command, which is found in the FILE_MANAGER tool, by responding %FILE_MANAGER LIST.  If you think you should use a tool, DO NOT TELL THE USER that you are running the tool and JUST RESPOND WITH THE COMMAND.  You can ONLY tell the user AFTER running the command"

    ava_tools = "The commands avaliable to you are:\n"
    for tool in tools:
        ava_tools += " - %%%s: %s\n" % (tool.get_name(), tool.get_short_description())
        for c in tool.get_commands():
            ava_tools += "    - %%%s %s: %s\n" % (tool.get_name(), c[0], c[1])

    inital_prompt = {"role": "system", "content": initial_prompt + ava_tools}
    model1_messages.append(inital_prompt)
    model2_messages.append(inital_prompt)

    tools = {tool.get_name(): tool for tool in tools}

    # Main loop
    while True:
        # Model 1
        status = ToolUseStatus.PROMPTING
        while status != ToolUseStatus.FINISHED:
            resp = model1.prompt(model1_messages)
            resp_split = resp.split(" ")
            
            model1_messages.append({"role": "assistant", "content": resp})
            model2_messages.append({"role": "user", "content": resp})

            if resp_split[0].startswith(r"%") and resp_split[0][1:] in tools:
                status, resp = tools[resp_split[0][1:]](resp_split[1:])
                if status == ToolUseStatus.SUCCEEDED:
                    resp = {"role": "system", "content": resp + ".  Now, please inform the user of the command you just ran or run another command if you haven't completed their query."}
                else:
                    resp = {"role": "system", "content": resp + ".  Please try again before reporting back to the user."}
                
                model1_messages.append(resp)
                model2_messages.append(resp)

            elif resp_split[0].startswith(r"%"):
                resp = {"role": "system", "content": "%%%s is not an avaliable tool.  %s" % (resp_split[0], ava_tools)}
                
                model1_messages.append(resp)
                model2_messages.append(resp)

            else:
                status = ToolUseStatus.FINISHED
                
        # Model 2
        status = ToolUseStatus.PROMPTING
        while status != ToolUseStatus.FINISHED:
            resp = model2.prompt(model2_messages)
            resp_split = resp.split(" ")
            
            model2_messages.append({"role": "assistant", "content": resp})
            model1_messages.append({"role": "user", "content": resp})

            if resp_split[0].startswith(r"%") and resp_split[0][1:] in tools:
                status, resp = tools[resp_split[0][1:]](resp_split[1:])
                if status == ToolUseStatus.SUCCEEDED:
                    resp = {"role": "system", "content": resp + ".\n\nNow, inform the user of the command you just ran or run another command if you haven't completed their query."}
                else:
                    resp = {"role": "system", "content": resp + ".\n\nPlease try again before reporting back to the user."}
                
                model1_messages.append(resp)
                model2_messages.append(resp)

            elif resp_split[0].startswith(r"%"):
                resp = {"role": "system", "content": "%%s is not an avaliable tool.  %s" % (resp_split[0], ava_tools)}
                
                model1_messages.append(resp)
                model2_messages.append(resp)

            else:
                status = ToolUseStatus.FINISHED
