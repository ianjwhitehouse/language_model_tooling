# Imports
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

from base_classes import Model, UserInput, main_loop
from file_manager import FileManagerTool
from python_runner import PythonTool
from internet_tools import WikipediaTool, GoogleTool


class Llama_Model(Model):
    def __init__(self,):
        model_id = "meta-llama/Meta-Llama-3-8B-Instruct" # casperhansen/llama-3-70b-instruct-awq" # meta-llama/Meta-Llama-3-8B-Instruct" # ""
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.LLM = LLM(model=model_id) #, tensor_parallel_size=2, max_model_len=3124, gpu_memory_utilization=0.9, swap_space=80) #, max_num_seqs=1)
        
        self.terminators = [
            self.tokenizer.eos_token_id,
            # tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        self.sampling_params = SamplingParams(n=1, max_tokens=8192, stop_token_ids=self.terminators, temperature=0.6, top_p=0.9)

    def prompt(self, messages):
        if type(messages[0]) == dict:
            prompt = [self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
            ).replace("<|eot_id|>", "")]
           
            output = self.LLM.generate(prompt, self.sampling_params)[0].outputs[0]
            return output.text.strip()
            
        else:
            prompt = [self.tokenizer.apply_chat_template(
                    message, 
                    tokenize=False, 
                    add_generation_prompt=True
            ).replace("<|eot_id|>", "") for message in messages]

            print(prompt)
            
            outputs = self.LLM.generate(prompt, self.sampling_params)
            return [out.outputs[0].text.strip() for out in outputs]


if __name__ == "__main__":
    llama_model = Llama_Model()
    main_loop(UserInput(), llama_model, [FileManagerTool(), PythonTool(), WikipediaTool(summary_model=llama_model), GoogleTool()])
