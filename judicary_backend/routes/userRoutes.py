from flask import request, jsonify
from apiModel.DLLM import DLLM
from apiModel.SCPAPI import GenerateSumIE
import pickle
from models.users import User
from apiModel.AIJudge import AIJudge
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from models.case import Case
from models.filters import Filters
from  datetime import datetime
from bson.objectid import ObjectId
from mongoengine.queryset.visitor import Q
import json
from docx import Document
import os
import torch
import numpy as np
import os
import json
from tqdm import tqdm
import io
from bucket.google_bucket import upload_to_gcs
from werkzeug.utils import secure_filename
import bson
# from celery import Celery
from bson import json_util
from math import ceil

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# celery_app = Celery('tasks', broker='pyamqp://guest@localhost//')


def get_specific_filters(filter_field, filters_list = None):

    if (filters_list == (None)):
        try:
            page = int(request.args.get('page', 1))  # Default to first page
            page_size = int(request.args.get('page_size', 8))  # Default to 10 items per page

            filters_doc = Filters.objects.first()
            if filters_doc:
                filters_list = getattr(filters_doc, filter_field, [])
                total_items = len(filters_list)
                total_pages = ceil(total_items / page_size)
                # Pagination
                start_index = (page - 1) * page_size
                end_index = start_index + page_size
                paginated_filters = filters_list[start_index:end_index]
                

                return jsonify({
                    'filters': paginated_filters,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_items': total_items,
                        'total_pages': total_pages 
                    }
                }), 200
            else:
                return jsonify({"message": "No filters found"}), 404
        except Exception as e:
            return jsonify({'error': str(e), "status_code": 500}), 500
    else:
        try:
            page = 1  # Default to first page
            page_size = 8  # Default to 8 items per page

            # print("xyz2" , filters_list)
            total_items = len(filters_list)
            # print("pop" ,len(filters_list)  , page_size)
            if (total_items > page_size):
                total_pages = ceil(total_items / page_size)
                # Pagination
                start_index = (page - 1) * page_size
                end_index = start_index + page_size
                paginated_filters = filters_list[start_index:end_index]
                # print("qwerty" , paginated_filters)
                return {
              
                    'filters': paginated_filters,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_items': total_items,
                        'total_pages': total_pages
                    }
                
            }
            else:
                total_pages = ceil(total_items / page_size)
                # print("xyz" , filters_list)
                return {
                    'filters': filters_list,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_items': total_items,
                        'total_pages': total_pages
                    }
                   }
                
            
        except Exception as e:
            return jsonify({'error': str(e), "status_code": 500}), 500


def userRoutes(app):
    @app.route('/users', methods=['GET'])
    @jwt_required()  # Protect the route with JWT authentication
    def query_records():
        try:
            # Get the identity of the current user from the JWT token
            current_user_email = get_jwt_identity()
            users = User.objects()

            # Construct list of user data including email and profile information
            user_list = []
            for user in users:
                user_data = {
                    'email': user.auth_id.email,  # Retrieve email from associated Auth document
                    'user_profile': {
                        'auth_id': str(user.auth_id.id),  # Convert ObjectId to string
                        'profile_id': str(user.id),  # Convert ObjectId to string
                        'firstName': user.firstName,
                        'lastName': user.lastName,
                        'gender': user.gender,
                        'phone_number': user.phone_number,
                        'cnic_number': user.cnic_number,
                        'organization': user.organization,
                        'ntn_number': user.ntn_number,
                        'country': user.country,
                        'province': user.province,
                        'city': user.city,
                        'address': user.address,
                        'subscription': user.subscription,
                        'created_at': user.created_at.isoformat(),
                        'updated_at': user.updated_at.isoformat()
                        # Add more fields as needed
                    }
                }
                user_list.append(user_data)

            return jsonify(user_list), 200

        except Exception as e:
            return jsonify({'error': str(e), "status_code": 500}), 500

    @app.route('/createCase', methods=['POST'])
    @jwt_required()
    def create_case():
        try:
            # print("POST request received for creating a new case with data:", request.json)
            data = request.json

            similar_cases = SimilarCasesRetrieval(data.get('FileName'))
            print("check123---->  ", similar_cases)
            # temp = User.objects.get(id=data.get('user_id')),


            case_approval = data.get('CaseApproval', [])

            # Check if the case_approval is a string. If so, make it a list.
            if isinstance(case_approval, str):
                case_approval = [case_approval]

            # Now ensure it's a list with valid entries or default to a list with 'Not specified'
            case_approval = [item.strip().rstrip('.') for item in case_approval if item.strip()]

            # If the list is empty or values are invalid, default to ['Not specified']
            case_approval = case_approval if case_approval else ['Not specified']


            new_case = Case(
                user_id=User.objects.get(id=data.get('user_id')),  # Assuming user_id is provided in the request
                JudgeNames=data.get('JudgeNames', []),
                People=data.get('People', []),
                Organizations=data.get('Organizations', []),
                Locations=data.get('Locations', []),
                # Dates={
                #     'DateOfHearing': data.get('Dates', {}).get('DateOfHearing', ''),
                #     'JudgmentDate': data.get('Dates', {}).get('JudgmentDate', ''),
                #     'NotificationDate': data.get('Dates', {}).get('NotificationDate', ''),
                # },
                CaseNumbers=data.get('CaseNumbers', []),
                Appellants=data.get('Appellants', []),
                Respondents=data.get('Respondents', []),
                Money=data.get('Money', []),
                FIRNumbers=data.get('FIRNumbers', []),
                ReferenceArticles=data.get('ReferenceArticles', []),
                ReferredCases=data.get('ReferredCases', []),
                ReferredCourts=data.get('ReferredCourts', []),
                AppealCaseNumbers=data.get('AppealCaseNumbers', []),
                AppealCourtNames=data.get('AppealCourtNames', []),
                CaseApproval=case_approval,
                ExtractiveSummary=data.get('ExtractiveSummary', ''),
                FileURL=data.get('FileURL',''),
                FileName=data.get('FileName' ,''),
                SimilarCases= (similar_cases),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            new_case.save()  # Save the new case to the database
            created_case_id = str(new_case.id) 
            
            new_judge_names = data.get('JudgeNames', [])
            new_locations = data.get('Locations', [])
            new_case_types = [data.get('CaseType')] if 'CaseType' in data else []  # Adjust based on actual data structure

            # Check if a Filters document already exists
            filters_doc = Filters.objects.first()
            if not filters_doc:
                # If not, create a new Filters document and save it
                Filters(
                    JudgeFilters=new_judge_names, 
                    CaseTypeFilters=new_case_types, 
                    LocationFilters=new_locations,
                    created_at=datetime.utcnow(),  # Set created_at to now
                    updated_at=datetime.utcnow()  # Set updated_at to now
                ).save()
            else:
                # Update the existing Filters document with new values and update updated_at field
                update_operations = {'updated_at': datetime.utcnow()}  # Prepare to update updated_at
                
                for judge_name in new_judge_names:
                    Filters.objects().update_one(add_to_set__JudgeFilters=judge_name, **update_operations)
                for location in new_locations:
                    Filters.objects().update_one(add_to_set__LocationFilters=location, **update_operations)
                for case_type in new_case_types:
                    Filters.objects().update_one(add_to_set__CaseTypeFilters=case_type, **update_operations)

            
            return jsonify(message="Case verified & added successfully", case_id=created_case_id), 200  # Return the JSON representation of the new case with status code 201 (Created)
        except Exception as e:
            print("Error occurred:", str(e))
            return jsonify({'error': str(e), "status_code": 500}), 500  # Return error response with status code 500 if an error occurs


    @app.route('/getCaseFromId/<string:case_id>', methods=['GET'])
    # @jwt_required()
    def get_case_from_id(case_id):
        try:
            # Validate the ObjectId
            if not bson.ObjectId.is_valid(case_id):
                return jsonify({'error': 'Invalid ID format'}), 400

            # Attempt to find the case by its ID
            case = Case.objects(id=case_id).first()
            if case:
                return jsonify(case.to_json()), 200
            else:
                return jsonify({'error': 'Case not found'}), 404
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return jsonify({'error': str(e), 'status_code': 500}), 500


    # @app.route('/getFilters', methods=['GET'])
    # # @jwt_required()
    # def get_filters():
    #     try:
    #         # Attempt to retrieve the single Filters document
    #         filters_doc = Filters.objects.first()
            
    #         # If the document exists, return its JSON representation
    #         if filters_doc:
    #         # Convert the document to a dictionary
    #             data = filters_doc.to_mongo().to_dict()
    #             # Remove unwanted fields
    #             data.pop('created_at', None)
    #             data.pop('updated_at', None)
    #             data.pop("_id",None)
    #             # # Convert ObjectId to string
    #             # data['_id'] = str(data['_id'])

    #             # # Fix for any other ObjectId fields
    #             # for key, value in data.items():
    #             #     if isinstance(value, ObjectId):
    #             #         data[key] = str(value)

    #             return jsonify(data), 200
    #         else:
    #             # If no document is found, return a message
    #             return jsonify({"message": "No filters found"}), 404
            
    #     except Exception as e:
    #         print("Error occurred:", str(e))
    #         return jsonify({'error': str(e), "status_code": 500}), 500

   

    @app.route('/getJudgeFilters', methods=['GET'])
    # @jwt_required()
    def get_judge_filters():
        return get_specific_filters('JudgeFilters')

    @app.route('/getLocationFilters', methods=['GET'])
    # @jwt_required()
    def get_location_filters():
        return get_specific_filters('LocationFilters')

    @app.route('/getCaseTypeFilters', methods=['GET'])
    # @jwt_required()
    def get_case_type_filters():
        return get_specific_filters('CaseTypeFilters')

    @app.route('/getCases', methods=['GET'])
    def get_cases():
        try:
            # Basic pagination setup
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))

            # Initialize an empty query
            query = Q()

            # Retrieve filters and search string from request
            filters = request.args.get('filters')
            search_string = request.args.get('search', '')

            # Apply filters if they are provided
            if filters:
                filters_dict = json.loads(filters)
                for key, value in filters_dict.items():
                    # Add filter conditions for each key in the filters
                    query &= Q(**{f'{key}__in': value})

            # Apply search to the ExtractiveSummary if it is provided and length is >= 3
            if search_string and len(search_string) >= 3:
                search_query = Q(ExtractiveSummary__icontains=search_string)
                query &= search_query

            # Execute the query with pagination
            cases_query = Case.objects(query).paginate(page=page, per_page=page_size)

            cases_list = []
            for case in cases_query.items:
                case_data = {
                    "_id": str(case.id),
                    "user": str(case.user_id.id) if case.user_id else '',
                    "JudgeNames": case.JudgeNames or [],
                    "People": case.People or [],
                    "Organizations": case.Organizations or [],
                    "Locations": case.Locations or [],
                    "CaseNumbers": case.CaseNumbers or [],
                    "Appellants": case.Appellants or [],
                    "Respondents": case.Respondents or [],
                    "Money": case.Money or [],
                    "FIRNumbers": case.FIRNumbers or [],
                    "ReferenceArticles": case.ReferenceArticles or [],
                    "ReferredCases": case.ReferredCases or [],
                    "ReferredCourts": case.ReferredCourts or [],
                    "AppealCaseNumbers": case.AppealCaseNumbers or [],
                    "AppealCourtNames": case.AppealCourtNames or [],
                    "CaseApproval": case.CaseApproval if case.CaseApproval else '',
                    "FileName": case.FileName if case.FileName else '',
                    "SimilarCases": case.SimilarCases or [],
                    "ExtractiveSummary": case.ExtractiveSummary if case.ExtractiveSummary else '',
                    "FileURL": case.FileURL if case.FileURL else '',
                    "created_at": case.created_at.isoformat() if case.created_at else '',
                    "updated_at": case.updated_at.isoformat() if case.updated_at else '',
                }
                cases_list.append(case_data)

            judge_list = []
            locations_list = []
            if search_string and len(search_string) >= 3:
                cases_query_2 = Case.objects(query)
                for case in cases_query_2:
                    judge_list.extend(case.JudgeNames or [])
                    locations_list.extend(case.Locations or [])

            judges_filter_result = get_specific_filters("JudgeFilters", judge_list)
            if "error" in judges_filter_result:
                return {"error": judges_filter_result["error"], "status_code": 500}

            location_filter_result = get_specific_filters("LocationFilters", locations_list)
            if "error" in location_filter_result:
                return {"error": location_filter_result["error"], "status_code": 500}

            response = {
                'cases': cases_list,
                "judge_list": judges_filter_result or [],
                "locations_list": location_filter_result or [],
                'total': cases_query.total,
                'pages': cases_query.pages,
                'page': page,
                'page_size': page_size,
            }

            return jsonify(response), 200
        except Exception as e:
            print("Error occurred:", str(e))
            return jsonify({'error': str(e), "status_code": 500})

    @app.route('/uploadFile', methods=['POST'])
    @jwt_required()
    def fileUpload():
        dllm = DLLM()
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        
        file = request.files['file']
        file.filename = secure_filename(file.filename)
        _, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower()

        if file_extension not in ['.pdf', '.docx', '.txt']:
            return jsonify({'error': 'File format not supported'}), 400
        
        # Define the local save path
        # local_save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # file.save(local_save_path)

        if file_extension == '.txt':
            # Convert .txt content to .docx
            doc = Document()
            txt_content = file.read().decode('utf-8')
            print("Hello")
            summary, ie = GenerateSumIE(txt_content, dllm)
            print("we are good")
            doc.add_paragraph(txt_content)

            # Prepare the byte stream to write the .docx content
            docx_buffer = io.BytesIO()
            doc.save(docx_buffer)
            docx_buffer.seek(0)  # Reset the buffer cursor to the start

            # Create a .docx filename
            docx_filename = os.path.splitext(file.filename)[0] + '.docx'
            # Set the file_stream to the docx_buffer for uploading
            file_stream = docx_buffer
            if summary and ie:
                embedding_file = SaveNewEmbedding(file)
        else:
            # Handle other file extensions (.pdf, .docx) without conversion
            # Set the file_stream to the uploaded file's stream
            file_stream = file.stream
            docx_filename = file.filename
            summary, ie = GenerateSumIE(file_stream, dllm)
            if summary and ie:
                embedding_file = SaveNewEmbedding(file)

        # parsed_ie = json.loads(ie['predicted'])
    
    
        # ie = {
        #     "device": "cuda",
        #     "predicted": [
        #         {
        #             "output": "{\"JudgeNames\": [\"MUHAMMAD-YAQUB-ALI\"], \"People\": [\"Harnam-Singh\", \"Leave-refused.\"], \"Organizations\": [\"Custodian-of-Evacuee-Property\"], \"Locations\": [\"Pakistan\"], \"CaseNumbers\": [\"Writ-Petition-in-the-High-Court\"], \"Appellants\": [\"Leave-refused.\"], \"Respondents\": [\"Bagat-Sohr\"], \"Money\": [\"Rs.-35,255\"], \"Case Approval\": [\"Leave-refused.\"]}"
        #         }
        #     ]
        # },
        # summary = {   
        #     "device": "cuda",
        #     "predicted": [
        #         {
        #             "output": "Summary : MUHAMMAD YAQUB ALI, J.The petitioner claimed that Harnam Singh and others evacuee owners had entered into an agreement for sale of the land in dispute in favour of her husband Baga Singh who embraced Islam after Partition and died in Pakistan. Out of the sale price fixed at Rs. 35,255, baga Singh had allegedly paid to the vendors on the 6th January 1947, a sum of Rs. 16,000. Long after the prescribed period of limitation for filing a suit for specific performance had expired, the petitioner applied to the Deputy Rehabilitation Commissioner under section 16 of the Pakistan (Administration of Evacued Property) Act XII of 1957, for permission to file a suo motu jurisdiction under section 12 of the Land Settlement Act. It was contended that the Chief Settlement Commissioner could not intervene as no order was passed by any Settlement authority and in any case nine months having expired when the decree was executed the order passed by the Revenue authorities sanctioning the mutation of land in her favour could not be revised under S. 19 (i) of the Law Settlement Act No Court, tribunal or authority could pass any judgment, decree or order in respect of it. An exception was made in case of persons who had before the bar was imposed on alienation of evacee properties entered into valid agreements for their purchase and had passed whole or part of the consideration. The holder of such an agreement could file suit with the prior permission of the Custodian of escuee property If the suit was decreed it was necessary to again obtain confirma tion of the decree by the Custidian of Escuevaee Property other wise it could no be executed."
        #         }
        #     ]
        # }

        # Call the function to upload the file stream to GCS
        URL = upload_to_gcs(os.getenv('BUCKET_NAME', 'judiciary_bucket'), file_stream, docx_filename, os.path.join(app.root_path, 'google_bucket_credentials.json'))
        if "Error" not in embedding_file:
            return jsonify({"summary": summary , "ie": ie, 'message': 'File Uploaded successfully to GCS', 'URL': URL , 'filename' : embedding_file}), 200
        else:
            return jsonify({"summary": summary , "ie": ie, 'message': 'File Uploaded successfully to GCS', 'URL': URL , 'filename' : "Error_File"}), 200

    @app.route('/FindCasesByFilenames', methods=['POST'])
    def find_cases_by_filenames():
        try:
            # Get array of filenames from request
            request_data = request.json
            filenames = request_data.get('filenames', [])
            self_id = request_data.get('self_id')
                
            # Query cases based on filenames
            cases = []
            for filename in filenames:
                # Find cases with matching filename
                cursor = Case.objects(FileName=filename)

                # Append unique cases to the list
                for case in cursor:
                    if case not in cases:
                        cases.append(case)

            # Remove duplicates based on content
            unique_cases = remove_duplicates(cases)

            # Convert ObjectId to string, remove unnecessary fields, and jsonify the response
            unique_cases_json = []
            for case in unique_cases:
                case_dict = case.to_mongo().to_dict()
                case_dict['_id'] = str(case_dict['_id'])
                case_dict['user_id'] = str(case_dict['user_id'])
                case_dict.pop('created_at', None)
                case_dict.pop('updated_at', None)
                unique_cases_json.append(case_dict)

            filtered_cases = [case for case in unique_cases_json if case['_id'] != self_id]

            return jsonify(filtered_cases)

        except Exception as e:
            return jsonify({'error': str(e), "status_code": 500}), 500

    def remove_duplicates(cases):
        unique_cases = []
        unique_filenames = set()

        for case in cases:
            filename = case['FileName']
            if filename not in unique_filenames:
                unique_cases.append(case)
                unique_filenames.add(filename)

        return unique_cases
   
    @app.route('/FindSimilarCases', methods=['POST'])
    def SimilarCasesRetrieval(search_string, embedding_directory='Embeddings (complete  case)'):
        input_embedding = None
        file_scores = []
        print("i am here")
        # Load embeddings and find the input embedding
        for filename in os.listdir(embedding_directory):
            with open(os.path.join(embedding_directory, filename), 'r') as file:
                data = json.load(file)
                if search_string in filename and 'embedding' in data:
                    input_embedding = np.array(data['embedding'])
                    break  # Found the input embedding, no need to continue

        if input_embedding is None:
            return {"error": "Input embedding not found"}

        # Calculate similarities with other files
        for filename in os.listdir(embedding_directory):
            with open(os.path.join(embedding_directory, filename), 'r') as file:
                data = json.load(file)
                if 'embedding' in data:
                    file_embedding = np.array(data['embedding'])
                    score = np.dot(input_embedding, file_embedding) / (np.linalg.norm(input_embedding) * np.linalg.norm(file_embedding))
                    file_scores.append((filename, score))

        # Sort and extract similar case filenames
        file_scores.sort(key=lambda x: x[1], reverse=True)
        similar_cases = [filename.split('_embedding.json')[0] for filename, _ in file_scores[:10]]  # Adjust the number as needed

        return similar_cases


    # This function takes prompt as an arguement and returns the generated output
    @app.route('/chatbot_query', methods=['POST'])
    def PromptFunction():
            if torch.cuda.is_available():
                device = torch.device("cuda")
                print("Using GPU:", torch.cuda.get_device_name(0))
            else:
                device = torch.device("cpu")
        
            # Get the data from the text box
            #input_text = request.form.get('input_text')
            input_text = request.json
            
            judge = AIJudge()
             
            print(input_text)
            print(type(input_text))
            #input_text str(input_text)
            list_of_filenames,output_text = judge.ProcessPrompt(input_text)
            print(output_text)
            # Process the input text (you can add your processing logic here)
            
            #list_of_filenames = judge.compare_embeddings_with_files(input_text)
            
            cases = [] 
            for filename in list_of_filenames:
                # Find cases with matching filename
                cursor = Case.objects(FileName=filename)

                # Append unique cases to the list
                for case in cursor:
                    if case not in cases:
                        cases.append(case)

            # Create a JSON response with the output
            response_data = {
                'chatbot_response': output_text ,
                'list_of_cases' : cases,
            }
            del judge
            return jsonify(response_data)
    


#----------We dont this function as a route , look at the end of the file for the functions defination ---------------------#
    #This function returns names of files without extension e.g ['2021S24','2019L5045']
    # @app.route('/', methods=['GET'])
    # def PromptSimilarCases():
    #     if request.method == 'GET':
    #         # Get the data from the text box
    #         input_text = request.form.get('input_text')
    #         # judge = AIJudge()
    #         # output_text = judge.compare_embeddings_with_files(input_text)

            

    #         # Create a JSON response with the output
    #         response_data = {
    #             'output': output_text 
    #         }
    #         return jsonify(response_data)
        

    # This Function needs to be called after File has been Uploaded . so it can generated the facts from file in background , make sure to pass the actual file into this function
    # @app.route('/SaveNewEmbedding', methods=['POST'])
    # def SaveNewEmbedding():
         
    #     if 'file' not in request.files:
    #         return jsonify({"error": "No file part"})

    #     file = request.files['file']
    #     if file.filename == '':
    #         return jsonify({"error": "No selected file"})
    #     if file:
    #         input_text = file.read().decode("utf-8")
    #         output_dir = 'modelsLocation/TempEmbeddings'
    #         dllm = DLLM()
    #         print(file.filename)
            
    #         # It appears you want to save the embeddings here.
    #         # process_files_in_directory should be adjusted to save the embeddings
    #         # and return the filename if successful
    #         try:
    #             dllm.process_files_in_directory(input_text, file.filename, output_dir)
    #             return file.filename.split('.')[0]  # Return just the base filename without extension
    #         except Exception as e:
    #             return "Error: " + str(e)  # Return the error message

    #     else:
    #         return "Error: No file provided"  # Return an error message if no file was provided
    # @app.route('/SaveNewEmbedding', methods=['POST'])
def SaveNewEmbedding(file):
    print("Running embedding")
    if file:
        try:
            input_text = file.read().decode("utf-8")
            output_dir = 'Embeddings (complete  case)'
            dllm = DLLM()
            print(file.filename)
            dllm.process_files_in_directory(input_text, file.filename, output_dir)
            return file.filename.split('.')[0]
        except Exception as e:
            print(f"Error in process_files_in_directory: {e}")
            return "Error: " + str(e)
    else:
        return jsonify({"error": "Error processing file"})

def PromptSimilarCases():
    # if request.method == 'GET':
    # Get the data from the text box
    # input_text = request.form.get('input_text')
    # judge = AIJudge()
    # output_text = judge.compare_embeddings_with_files(input_text)

    
    #---Temporary Data ( FileNames )
    temp_array = ['1971S974', '1971S977' , '1971S979' , '1971S979' , '1971S993' , '1972L101', '1972L23' , '1972L37','1972L47' , '1972L48' , '1972L50']


    #Don't return a json response but an array of strings
    # response_data = {
    #     'output': output_text 
    # }
    # return jsonify(response_data)

    return temp_array