
from g1_v import generate_response
import json
from tqdm import tqdm
def main():   
#/Users/mohorbanerjee/Desktop/workspace/Llama-3.1-8B-Instruct_sample=199_dp=5.json
    with open('/home/users/ntu/mohor001/g1vllm/Llama-3.1-8B-Instruct_sample=199_dp=5.json','r') as file:
        dataneo=file.read()
    dataneo=json.loads(dataneo)

    for idx,ij in enumerate(tqdm(dataneo)):
        
        if(idx==30):
            break
        
        temp=[]
        
        for query in ij["problem_statements"]:
            
            user_query = query
            
            if True:   
                # Generate and display the response
                for steps, total_thinking_time in generate_response(user_query):
                        for i, (title, content, thinking_time) in enumerate(steps):
                            # Ensure content is a string
                            if not isinstance(content, str):
                                content = json.dumps(content)
                            if title.startswith("Final Answer"):
                                temp.append(content)
        ij["outputs"]=temp    
    with open("o1like.json", "w") as dola_file:
        json.dump(dataneo, dola_file, indent=4)
if __name__ == "__main__":
    main()
