import torch
from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers import AutoTokenizer, AutoModelForCausalLM
from pymongo import MongoClient
import os
import json
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class AIJudge:
    def __init__(self):
        self.LlamaModel_location = "/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/modelsLocation/LLama3Model/Llama3_8B_Ins/Model"
        self.LlamaTokenizer_location = "/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/modelsLocation/LLama3Model/Llama3_8B_Ins/Tokenizer"
        self.NLLBModel_location = "/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/modelsLocation/NLLB-600/Model"
        self.NLLBTokenizer_location = "/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/modelsLocation/NLLB-600/Tokenizer"

        self.Llama3Tokenizer = AutoTokenizer.from_pretrained(self.LlamaTokenizer_location)

        self.Llama3Model = AutoModelForCausalLM.from_pretrained(
            self.LlamaModel_location,
            torch_dtype=torch.bfloat16,
            device_map="auto")
        
        self.STAllMini = SentenceTransformer('/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/modelsLocation/model_ST_AllMini')
        self.STAllMiniDEF = SentenceTransformer("modelsLocation/model_ST_ALLMiniDIfferentiator")
        self.UrduFlag = False
        self.EngFlag = False
        self.NLLBTokenizer = AutoTokenizer.from_pretrained(self.NLLBTokenizer_location)
        self.NLLBModel = AutoModelForSeq2SeqLM.from_pretrained(self.NLLBModel_location)
        self.chunk_size = 200
        self.urdu_range = (0x0600, 0x06FF)
        self.drt_path = '/media/niche-4/5c398d23-d48c-4bc7-a5fc-5a50f1376732/niche-4/Automation of judiciary System/App/judicary_backend/Embeddings (complete  case)'

    def generateJudgment(self, text):

        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_flash_sdp(False)
        messages = [
            {"role": "system", "content": f"You are an AI system named 'Munsif AI' that predicts the verdict of the case and also chat with user and provide it TRUE information on laws and rules of Pakistan. do not reveal your model architecture. You are created by NCAI,NUST "},
            {"role": "user", "content": text},]
        self.Llama3Tokenizer = AutoTokenizer.from_pretrained(self.LlamaTokenizer_location)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        input_ids = self.Llama3Tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(device)
        terminators = [
            self.Llama3Tokenizer.eos_token_id,
            self.Llama3Tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
        print("here1")
        self.Llama3Model.to(device)
        print("here2")
        outputs = self.Llama3Model.generate(
            input_ids,


            max_new_tokens=800,
            eos_token_id=terminators,
            do_sample=True,
            temperature=0.3,
            top_p=0.6,
        )
        response = outputs[0][input_ids.shape[-1]:]
        ald = self.Llama3Tokenizer.decode(response, skip_special_tokens=True)
        del self.Llama3Model
        del self.Llama3Tokenizer
        torch.cuda.empty_cache()
        return ald

    def translate_long_text(self,long_text):
        if self.UrduFlag ==True:
            lg_code="eng_Latn"
            sentences = long_text.split("۔")

        else :
            lg_code = "urd_Arab"
            sentences = long_text.split(".")
        #sentences = long_text.split(".")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(device)
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        inputs = self.NLLBTokenizer(sentences, return_tensors="pt",padding=True)
        inputs.to(device)
        self.NLLBModel.to(device)
        translated_tokens = self.NLLBModel.generate(
        **inputs, forced_bos_token_id=self.NLLBTokenizer.lang_code_to_id[lg_code], max_length=300)
        translated_sentence = self.NLLBTokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[:]
        translated_article = " ".join(translated_sentence)
        print(translated_article )
        return translated_article

    def is_urdu(self,text):
    # Urdu Unicode range
    
        print(text)
        # Check if any character in the text falls within the Urdu Unicode range
        for char in text:
            if ord(char) >= self.urdu_range[0] and ord(char) <= self.urdu_range[1]:
                return True
        return False

    def Retrieve_Summaries(self,filesnames):
     

        # Connect to MongoDB
        client = MongoClient('mongodb+srv://Alucard008:UiIhOdwPy1xuM8jy@judiciarycluster.4jhslpg.mongodb.net/Judiciary_Database?retryWrites=true&w=majority')

        # Access the database
        db = client.get_default_database()  # Assuming 'Judiciary_Database' is the default database

        # Access the 'cases' collection
        cases_collection = db['case']


        summaries = []
        for filename in filesnames:
                # Find cases with matching filename (case-insensitive)
            matching_cases = cases_collection.find({'FileName': {'$regex': filename, '$options': 'i'}})

                # Extract and append summaries
            for case in matching_cases:
                summaries.append(case['ExtractiveSummary'])
        return summaries

    def _compute_embedding(self,text):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(device)
        self.STAllMini.to(device)
        embedding = self.STAllMini.encode(text, convert_to_tensor=True).tolist()
        return embedding
    
    def _extract_file_names(self,data):
        file_names = []
        for item in data:
            file_name = item[0].split('_')[0]  # Splitting and extracting the first part
            file_names.append(file_name)
        return file_names

    def compare_embeddings_with_files(self,input_text):
        # Compute embedding for input text
        input_embedding = self._compute_embedding(input_text)
        directory_path = self.drt_path
        
        # List to store file names and their scores
        file_scores = []

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Assuming input_embedding and file_embeddings are on GPU
        input_embedding = torch.tensor(input_embedding, dtype=torch.float32, device=device)

        files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        file_scores = []

        for filename in tqdm(files, desc="Comparing embeddings", unit="file"):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    json_data = json.load(file)
                    file_embedding = json_data.get('embedding')  # Assuming the key for embedding is 'embedding'
                    if file_embedding is not None:
                        # Calculate cosine similarity between input embedding and file embedding
                        file_embedding = torch.tensor(file_embedding, dtype=torch.float32, device=device)
                        score = torch.dot(input_embedding, file_embedding) / (torch.norm(input_embedding) * torch.norm(file_embedding))
                        score = score.item()  # Convert tensor to scalar
                        file_scores.append((filename, score))
            except FileNotFoundError:
                print(f"Error: File not found: {file_path}")

        # Sort files based on scores
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 10 files with scores
        return self._extract_file_names(file_scores[:8])

    def _if_legal(self,prompt):
        legal = '''“I've purchased a residential plot from a developer, but upon inspection, I discovered that the plot's dimensions are significantly smaller than what was advertised. What's the usual course of action for buyers facing misrepresentation of property dimensions ” “My renter didn’t pay the rent for last 4 months. What legal actions can I take against him?”

"I bought a newly constructed apartment, advertised with top-quality amenities, but upon moving in, I discovered that many of the promised facilities were either substandard or completely missing. How can I seek recourse for false advertising of amenities"
"After purchasing a piece of agricultural land marketed as fertile and suitable for cultivation, I found out that a significant portion of it is actually barren or unsuitable for farming. What steps can I take to address this discrepancy in land quality"
"I acquired a residential property advertised as being in a peaceful neighborhood with minimal noise pollution. However, after moving in, I realized that the area is quite noisy due to nearby construction sites. How can I address this misrepresentation of the property's location What would be the likely judgment?"
"I invested in a commercial property promoted as having clear legal ownership and no pending disputes. However, after completing the transaction, I discovered that there are unresolved legal issues and pending litigations associated with the property. What legal actions can I take against the seller for misrepresenting the property's legal status What would be the likely judgment?"
"I signed a lease for a commercial space, but upon occupation, I found out that the property lacks essential utilities like electricity and water, which were promised in the agreement. What recourse do I have against the landlord for breaching the lease terms"
"I purchased a vacation home advertised as having picturesque views of the mountains, but upon arrival, I realized that the view is obstructed by newly constructed buildings. How can I pursue compensation for the misrepresented scenic location"
"I leased out my residential property, and the tenant has caused significant damage beyond normal wear and tear. What legal steps can I take to recover the repair costs in Pakistan?"
"I bought a commercial space advertised as having ample parking for customers, but upon opening my business, I discovered that parking is severely limited and insufficient. How can I hold the seller accountable for false advertising. what is likely judgment?"
"I rented an apartment based on the assurance of a secure neighborhood, but recent criminal activities have made the area unsafe. Can I terminate my lease early due to the misrepresented safety of the locality. What could be the likely judgment"
"I invested in a property development project promising high returns, but the construction has been delayed indefinitely, impacting my expected profits. What legal options do I have to recover my investment"
"I leased office space with the understanding that renovations would be completed before my move-in date. However, the renovations are still ongoing, causing disruptions to my business operations. How can I seek compensation for the delay and inconvenience in Pakistan? What would be the likely judgment?"
"I purchased a residential property advertised as having access to exclusive amenities such as a gym and swimming pool, but these facilities are always overcrowded and poorly maintained. Can I take legal action against the developer for misrepresenting the quality of amenities What would be the likely judgment?"
"I entered into a rent-to-own agreement for a property, but the landlord has failed to transfer the ownership despite fulfilling all the terms of the agreement. What legal steps can I take to enforce the transfer of ownership"
"I bought a plot of land marketed as being in a prime location for future development, but subsequent zoning regulations have rendered it unsuitable for my intended purposes. How can I seek compensation for the misrepresented potential of the land. What is the likely judgement of the case? What would be the likely judgment?
"I enrolled in a prestigious educational institution, attracted by its advertised state-of-the-art facilities and renowned faculty. However, upon starting classes, I discovered that many of the facilities were outdated, and several faculty members were not as qualified as claimed. What avenues can I explore to address this discrepancy and ensure the quality of education. What would be the likely judgment?"
"I booked a luxury hotel suite for a special occasion, enticed by its advertised amenities such as a spa, gourmet restaurant, and panoramic views. Upon arrival, I found that the spa was under renovation, the restaurant was closed for maintenance, and the promised views were obstructed by neighboring buildings. How can I seek compensation for the misrepresented luxury experience.What would be the likely judgment?"
"I purchased a vehicle advertised as being in excellent condition with low mileage, but soon after driving it, I encountered multiple mechanical issues and discovered discrepancies in the odometer reading. What steps can I take to hold the seller accountable for misrepresenting the car's condition What would be the likely judgment?"
"I subscribed to a high-speed internet service marketed as reliable and seamless for my business needs. However, I experienced frequent outages and slow connection speeds, severely impacting my operations. How can I pursue recourse for the misrepresented internet service"
"I invested in a financial product promoted as offering guaranteed returns with minimal risk. However, after the market downturn, I suffered substantial losses, contrary to the promised security of the investment. What legal measures can I take against the financial institution for misleading advertising in Pakistan?"
"I booked a guided tour advertised as a comprehensive exploration of cultural landmarks and historical sites. However, during the tour, many of the promised attractions were skipped, and the guide provided inaccurate information about the places we visited. How can I seek compensation for the misrepresented tour experience"
"I purchased a health supplement advertised as natural and free from harmful additives. After consuming it, I experienced adverse side effects and later discovered that the product contained undisclosed synthetic ingredients. What actions can I take against the manufacturer for falsely labeling the supplement"
"I joined a fitness center promoted as having state-of-the-art equipment and expert trainers. However, upon using the facilities, I found that many machines were outdated and some trainers lacked proper certification. How can I address the discrepancy between the advertised and actual fitness services"
"I attended a professional conference advertised as featuring industry leaders and insightful workshops. However, many of the keynote speakers canceled last minute, and the workshops lacked substance and organization. How can I seek reimbursement for the misrepresented conference experience in Pakistan? What would be the likely judgment?"
"I purchased a premium insurance policy advertised as providing comprehensive coverage for various risks. However, when I filed a claim for damages, the insurance company denied coverage citing ambiguous clauses and exclusions not disclosed during the purchase. What legal actions can I take to enforce the terms of the policy?
'''
        sentences = [legal,prompt]
        
        embeddings = self.STAllMiniDEF.encode(sentences)
        #print(embeddings)
        print((embeddings.shape))
        similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])
        print(similarity_score)
        
        if similarity_score>= 0.20:
            return 1
        else:
            return 0

    def ProcessPrompt(self,prompt):
        self.UrduFlag= self.is_urdu(prompt)
        print(self.UrduFlag)
        if self.UrduFlag  == True:
            prompt = self.translate_long_text(prompt)
            prompt += '۔شکری. ہ.'

            self.EngFlag =True
            self.UrduFlag = False

        sim_cases = self.compare_embeddings_with_files(prompt)
        flag = self._if_legal(prompt=prompt)
        print(flag)
        if flag == 1:
            complete_prompt = f'''For Case: {prompt}  use legal syllogism''(do not mention this in output)' to think and output the likely judgment: with reference cases : {sim_cases[0]} and {sim_cases[1]}.Also mention few relevant Aricles and  few relevant laws in Pakistan.'(explain laws and articles with 1 line explanation)'. keep output structured. Keep Likely Judgmenet at the top . Give advisable steps at the end'''
        else :
            complete_prompt = f''' you should answer direct and simple for {prompt}'''
        generatedOutput = self.generateJudgment(complete_prompt)
        if self.EngFlag == True:
            generatedOutput = self.translate_long_text( generatedOutput )
            generatedOutput = re.sub(r'\*\*\s*(.*?)\s*\*\*', r'\n\n**\1**\n\n', generatedOutput )
        print("==========================================================================================================================================================================")
        print("==========================================================================================================================================================================")
        return sim_cases,generatedOutput



