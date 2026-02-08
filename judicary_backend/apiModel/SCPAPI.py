from pymongo import MongoClient
import json
# Search Keyword
def SearchKeyWord(Main_Search,CheckBox,dllm):
    '''
    Main_Search -> String
    CheckBox-> List of Strings
    dllm -> DLLM object

    returns
    [{
                'filename': ...,
                'content': ...,
                'id':  ...,
                'summary' : ... '
                'ie':  ... 

            }...] , totalnumber

    '''
    
    indexes  = json.loads(dllm.find_matching_files_in_mongodb( Main_Search, CheckBox))
    ids = [entry['id'] for entry in indexes]
    data = json.loads(dllm.find_files_by_indexes(ids))
    for entry in data:
        entry['ie'] = dllm.convert_to_json(entry['ie'])
    return [data ,  len(data)]

def OnDetail(id,dllm):

    '''
    id -> String/ID # dummy for now
    dllm -> DLLM object

    returns
    [{
                'filename': ...,
                'content': ...,
                'id':  ...,
                'summary' : ... '
                'ie':  ... 

            }...] , totalnumber

    '''
    ids = json.loads(dllm.SimilarCaseRetrieval(id))['indexes']
    data = json.loads(dllm.find_files_by_indexes(ids))
    #print(data)
    for entry in data:
        entry['ie'] = dllm.convert_to_json(entry['ie'])
    #print(data)
    #data = [entry for entry in data]
    return [data, len(data)]


def GenerateSumIE(doc,dllm,Sum='both'):
    '''
    doc -> string # dummy for now
    dllm -> DLLM object

    returns sum,ie
    # Sample Summary output {"device": "cuda", "predicted": [{"output": "Summary"}]}
    # Sample IE Output     {"device": "cuda", "predicted": [{"output": Json format}]}

    '''

    if Sum == 'sum'  or Sum == 'Sum':
        data = dllm.generate_abstracts( doc ,"Sum")
        return data
    elif Sum == 'ie'  or Sum == 'IE':
        data = dllm.generate_abstracts( doc ,"IE")
        return data
    elif Sum == "Both" or Sum == "both":
        print('Generating summary')
        sum = dllm.generate_abstracts( doc ,"Sum")
        print('Generating Information')
        ie = dllm.generate_abstracts( doc ,"IE")

        ie = json.loads(ie)
        ie['predicted'][0]['output'] = dllm.convert_to_json(ie['predicted'][0]['output'] )
        return json.loads(sum),ie


def insert_file_to_database(filename, content, summary, information,dllm):
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')  # Change the connection string as per your MongoDB setup
    db = client['JudiciaryCases']  # Use a valid database name without spaces
    collection = db['files']  # Choose a collection name, e.g., 'files'
    
    # Get the count of existing documents in the collection
    start_id = collection.count_documents({}) + 1
    
    # Prepare the data to be inserted
    data = {
        'filename': filename,
        'content': content,
        'summary': summary,
        'information': information,  # Convert information to JSON string
        'id': start_id
    }
    
    # Insert the data into the database
    collection.insert_one(data)
    
    # Close the database connection
    client.close()




