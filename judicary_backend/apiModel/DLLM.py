from pymongo import MongoClient
from tqdm import tqdm
import re
import torch
import time
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from datasets import Dataset
import json
import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

class DLLM:
    def __init__(self):
        self.key_mapping = {
            "JudgeNames": "jdg-",
            "People": "pp-",
            "Organizations": "org-",
            "Locations": "loc-",
            "CaseNumbers": "cn-",
            "Appellants": "app-",
            "Respondents": "res-",
            "Money": "mon-",
            "FIRNumbers": "fr-",
            "ReferenceArticles": "ra-",
            "ReferredCases": "rca-",
            "ReferredCourts": "rco-",
            "AppealCaseNumbers": "acn-",
            "AppealCourtNames": "apcn-",
            "Case Approval": "capp-"
        }
        #self.client = MongoClient('mongodb://localhost:27017/')

    # This function generates abstracts using a pretrained model based on the specified prefix.
    # It first checks if CUDA is available, then determines the appropriate model based on the prefix.
    # It then adds a prefix text to each article in the input array.
    # After preprocessing the articles, it loads the tokenizer for the selected model.
    # It defines a function to generate answers using the tokenizer and a dummy batch for demonstration purposes.
    # This function maps the generated abstracts to the input articles.
    # Finally, it converts the output summaries to JSON format along with information about the device used.
    # Note: The model loading part is commented out and a dummy response is returned for illustration purposes.

    

    def generate_abstracts(self, article_array, prefix):
        # Check if CUDA is available to select the appropriate device
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        print(device)

        # Determine the prefix text and model based on the specified prefix
        if prefix == "Sum":
            prefix_text = "Summary : "
            model_name = "modelsLocation/Summarization"
        elif prefix == "IE":
            prefix_text = "Extract Crucial Information : "
            model_name = "modelsLocation/Information"  # Assuming model 2 is T5-base
        else:
            raise ValueError("Invalid prefix. Choose 'Sum' for summarization or 'IE' for extraction.")
        
        # Add prefix_text to each article in article_array
        article_array = [prefix_text +  article_array]
        
        my_dict = {'article': article_array}
        test_dataset = Dataset.from_dict(my_dict)
        #model_directory = 'something'
        print("Loading Model")
        start_time = time.time()
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
        # Load the tokenizer for the selected model
        end_time = time.time()
        processing_time = end_time - start_time
        print("Loading Model Processing time:", processing_time, "seconds")
        print("Loading Tokenizer")
        tokenizer = AutoTokenizer.from_pretrained('google/long-t5-tglobal-base')

        # Define a function to generate answers using the tokenizer
        def generate_answer(batch):
            inputs_dict = tokenizer(batch["article"], padding="max_length", max_length=8192, return_tensors="pt", truncation=True)
            input_ids = inputs_dict.input_ids.to(device)
            attention_mask = inputs_dict.attention_mask.to(device)

            with torch.no_grad():
               predicted_summary_ids = model.generate(input_ids, attention_mask=attention_mask)

            # Generate a dummy abstract for illustration (Replace with actual model generation)
            batch["predicted_abstract"] = tokenizer.decode(predicted_summary_ids[0], skip_special_tokens=True)
            return batch
        print("Generating")
        start_time = time.time()
        # Apply the function to generate abstracts for the test dataset
        test_dataset = test_dataset.map(generate_answer)
        end_time = time.time()
        processing_time = end_time - start_time
        print("Generating Output Processing time:", processing_time, "seconds")


        

        # Convert the output summaries to JSON format
        output_summaries = [{"output": summary} for summary in test_dataset["predicted_abstract"]]
        del model
        return json.dumps({"device": device, "predicted": output_summaries})
        
    



    def SimilarCaseRetrieval(self, text):
        # Sample dictionary mapping file names to their content
        # Extract indexes from the function's return value
        indexes = [45, 55, 65]  # Example indexes of similar cases found
        
        # Combine found_files and indexes
        result = {"indexes": indexes}  # Combining indexes into a dictionary
        
        # Convert result to JSON format
        return json.dumps(result)  # Returning the result as a JSON string

    def find_files_by_indexes(self, indexes):
        """
        Fetches files from MongoDB based on the given indexes.

        Args:
            indexes (list): List of indexes to search for in the database.

        Returns:
            list: List of dictionaries containing file information.
                Each dictionary contains keys: 'content', 'summary', 'filename', 'ie', 'id'.
        """
        try:
           # client = MongoClient('mongodb://localhost:27017/')  # Connect to MongoDB
            db = self.client['JudiciaryCases']  # Replace 'your_database_name' with your database name
            collection = db['files']  # Choose a collection name, e.g., 'files'
            print("connected to DB")
        except Exception as e:
            print("Error connecting to the database:", e)
            return []

        files = []
        documents = collection.find({'id': {'$in': indexes}})

        for document in documents:
            try:
                if document:
                    content = document['content']
                    summary = document['summary']
                    filename = document['filename']
                    ie = document['information']
                    id = document['id']  # You need to implement Information Extraction logic
                    files.append({
                        'content': content,
                        'summary': summary,
                        'filename': filename,
                        'ie': ie,
                        'id': id
                    })
            except Exception as e:
                print(f"Error retrieving document for index {document}: {e}")
        return  json.dumps(files, indent=4)
        #return files

    def find_matching_files_in_mongodb(self, search_string, optional_strings=None):
        """
        Search for matching files in MongoDB based on the search string and optional strings.

        Args:
            search_string (str): The main search string.
            optional_strings (list[str], optional): List of optional strings to search for in addition to the main string.

        Returns:
            list[dict]: List of dictionaries containing matching files, each dictionary containing 'id' and 'filename'.
        """
        # Remove leading/trailing whitespaces from the search string
        search_string = search_string.strip()

        # Remove leading/trailing whitespaces from optional strings if provided
        if optional_strings:
            optional_strings = [opt_string.strip() for opt_string in optional_strings]
        else:
            optional_strings = []  # Handle case where optional_strings is None

        # Connect to MongoDB
        #client = MongoClient('mongodb://localhost:27017/')
        db = self.client['JudiciaryCases']  # Replace 'your_database_name' with your database name
        collection = db['files']  # Choose a collection name, e.g., 'files'

        matching_files = []

        # Retrieve all documents from the collection
        cursor = collection.find()
        for index, document in enumerate(tqdm(cursor, desc="Searching files in MongoDB")):
            content = document['content']
            filename = document['filename']
            index = document['id']

            # Check if all optional strings are present in the content
            if optional_strings and not all(re.search(opt_string, content, re.IGNORECASE) for opt_string in optional_strings):
                continue  # Skip this file if any optional string is not found

            # Check if the search string is present in the content
            if re.search(search_string, content, re.IGNORECASE):
                matching_files.append({
                    'id': index,
                    'filename': filename
                })
 
        return json.dumps(matching_files)

    # Method to extract key-value pairs from a given text using a predefined mapping.
    # It searches for each key's corresponding prefix in the text using regular expressions,
    # and extracts the value associated with it. Returns a dictionary of extracted pairs.
    def _extract_key_value(self, text):
        pairs = {}
        text_parts = text.split(' @ ')
        for part in text_parts:
            for key, prefix in self.key_mapping.items():
                if part.startswith(prefix):
                    value = part[len(prefix):].strip()
                    if key == "Case Approval":
                        # Remove "@" symbol if present at the end of the value
                        if value.endswith("@"):
                            value = value[:-1]
                    if key in pairs:
                        # If the key already exists, append the value to the list
                        pairs[key].append(value)
                    else:
                        pairs[key] = [value]
        return pairs

    # Method to convert extracted key-value pairs from text into JSON format.
    # It utilizes _extract_key_value method to obtain the pairs, then converts them into JSON format
    # using the json.dumps() function and returns the JSON output.
    def convert_to_json(self, text):
        extracted_pairs = self._extract_key_value(text)
        json_output = json.dumps(extracted_pairs)
        return json_output


    def _extract_facts_or_analysis(self,text):
        try:
            print(text)
            '''
            data = json.loads(text)
            # Check if the text contains facts
            if 'facts' in data:
                return data['facts']
            # If facts are not available, perform analysis
            elif 'analysis' in data:
                return data['ANALYSIS']
            else:
            '''
            return text  # If neither facts nor analysis are present
        except json.JSONDecodeError:
            return None  # Return None if text is not in valid JSON format

    # Function to process files in a directory
    def process_files_in_directory(self, input_file, filename, output_directory):
        print("Entering process_files_in_directory")
        
        model = SentenceTransformer(r'modelsLocation/model_ST_AllMini')
        print("Model loaded successfully")
        # Extract facts or perform analysis
        processed_text = self._extract_facts_or_analysis(input_file)
        print(f"Processed text: {processed_text[:100]}")  # Print a snippet of the processed text for debugging
        # Check if processed text is not empty
        embedding = model.encode(processed_text, convert_to_tensor=True).tolist()
        print("Embedding generated successfully")
        
        # Determine output filename
        output_filename = filename.split('.')[0] + '_embedding.json'
        output_file = os.path.join(output_directory, output_filename)
        print(f"Output file path: {output_file}")
        
        # Check if the output file already exists
        if not os.path.exists(output_file):
            # Save embeddings and filename in JSON format in the output directory
            with open(output_file, 'w') as json_file:
                json.dump({"filename": filename.split('.')[0]+'.txt', "embedding": embedding}, json_file, indent=4)
            print(f"Embedding for {filename} saved successfully.")
        else:
            print(f"Embedding for {filename} already exists.")
