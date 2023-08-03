from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from elasticsearch import Elasticsearch
import pandas as pd
import json
import os
from pymongo import MongoClient
from .form import FileUploadForm
from .models import UploadedFile
from .utils import ElasticsearchUploader, generate_word_cloud_from_data

es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
es_port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
es_scheme = os.getenv('ELASTICSEARCH_SCHEME', 'http')

mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
mongodb_name = os.getenv('MONGODB_NAME', 'dbt1')
mongodb_collection = os.getenv('MONGODB_COLLECTION', 'colt1')


class TestMongoDBView(View):
    def get(self, request):
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)

        db = client[mongodb_name]
        collection = db[mongodb_collection]

        # Retrieve data from the collection
        data = collection.find()

        # Convert the data to a list for printing
        data_list = list(data)

        # Print the data to the console
        for item in data_list:
            print(item)

        # Return a simple response
        return HttpResponse("MongoDB data printed to console.")

class TestElasticView(View):
    def get(self, request):
        try:
            es = Elasticsearch(hosts=[{'host': es_host, 'port': es_port, 'scheme': es_scheme}])

            # Check if the Elasticsearch cluster is up and running
            if es.ping():
                index_name = 'colt1'

                # Create an index if it doesn't exist
                if not es.indices.exists(index=index_name):
                    es.indices.create(index=index_name)

                # Perform a basic search operation
                search_results = es.search(index=index_name, body={
                    "query": {
                        "match_all": {}
                    }
                })

                total_hits = search_results['hits']['total']['value']

                response_data = {
                    "message": "Elasticsearch connection test successful",
                    "total_hits": total_hits
                }

                return JsonResponse(response_data)

            else:
                return JsonResponse({"message": "Elasticsearch cluster is not reachable"})

        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"})

def test_del(request):
    es_uploader = ElasticsearchUploader(hosts=[{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
    # index_name = 'colt1'
    index_name = mongodb_collection + '_' + str(92)
    print(index_name)
    es_uploader.delete_data(request, index_name)

    print(f"{result['deleted']} documents deleted from Elasticsearch, {72}")
    return HttpResponse("del")


class UploadFileView(View):
    template_name = 'fileuploader/upload.html'
    
    def get(self, request) -> HttpResponse:
        form = FileUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request) -> HttpResponse:
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            database_choice = form.cleaned_data['database']

            instance = UploadedFile(file=uploaded_file, database=database_choice)
            instance.save()

            saved_instance_pk = instance.pk
            current_file = get_object_or_404(UploadedFile, pk=saved_instance_pk)

            client = MongoClient(mongodb_uri)
            db = client[mongodb_name]
            collection = db[mongodb_collection]

            identifier = current_file.pk 

            print(database_choice)
            if database_choice == 'mongodb':
                print('Data inserted into MongoDB')
                if current_file.file.name.endswith('.csv'):
                    # Read CSV file
                    with current_file.file.open() as f:
                        data = pd.read_csv(f)
                        data_dict = data.to_dict(orient='records')

                        # Insert each row as a document with the identifier (pk)
                        for doc in data_dict:
                            doc['identifier'] = identifier
                            collection.insert_one(doc)

                elif current_file.file.name.endswith('.json'):
                    # Read JSON file
                    with current_file.file.open() as f:
                        json_data = json.load(f)
                        # Insert the JSON data directly with the identifier (pk)
                        json_data['identifier'] = identifier
                        collection.insert_one(json_data)

            if database_choice == 'elasticsearch':
                es_uploader = ElasticsearchUploader(hosts=[{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
                # index_name = f'colt1_{identifier}'  # Use the identifier in the index name
                index_name = mongodb_collection + '_' + str(identifier)
                es_uploader.upload_data(request, current_file, index_name)  # Update Elasticsearch data


            return redirect('upload_success')

class UploadSuccessView(View):
    template_name = 'fileuploader/upload_success.html'

    def get(self, request) -> HttpResponse:
        return render(request, self.template_name)

class FileListView(View):
    template_name = 'fileuploader/file_list.html'

    def get(self, request) -> HttpResponse:
        files = UploadedFile.objects.all()
        word_clouds = []
        word_clouds_json = []

        for file in files:
            data = None
            data2 = None
            if file.file.name.endswith('.json'):
                # ...
                # Read JSON file
                with file.file.open() as f:
                    json_data = json.load(f)
                    data2 = pd.json_normalize(json_data)
                    print(data2)
            elif file.file.name.endswith('.csv'):
                # Read CSV file
                with file.file.open() as f:
                    data = pd.read_csv(f)

            if data is not None:
                image_path = generate_word_cloud_from_data(data, file)  # Pass 'file' object as an argument
                if image_path:
                    word_clouds.append((file, image_path))

            if data2 is not None:
                image_path = generate_word_cloud_from_data(data2, file)  # Pass 'file' object as an argument
                if image_path:
                    word_clouds_json.append((file, image_path))

        return render(request, self.template_name, {'files': files, 'word_clouds': word_clouds, 'word_clouds_json': word_clouds_json})

class FileDetailView(View):
    template_name = 'fileuploader/file_detail.html'

    def get(self, request, pk) -> HttpResponse:
        file = get_object_or_404(UploadedFile, pk=pk)

        if file.file.name.endswith('.csv'):
            # Read CSV file
            with file.file.open() as f:
                data = pd.read_csv(f)
                columns = data.columns
                rows = data.values.tolist()

            # Prepare JSON variables as None when the file is a CSV
            json_data = None
            json_formatted = None

        elif file.file.name.endswith('.json'):
            # Read JSON file
            with file.file.open() as f:
                json_data = json.load(f)
                # Convert JSON data to a formatted string for display
                json_formatted = json.dumps(json_data, indent=2)

            # Prepare CSV variables as None when the file is a JSON
            data = None
            columns = None
            rows = None

        else:
            # If the file has neither .csv nor .json extension, set all variables as None
            data = None
            columns = None
            rows = None
            json_data = None
            json_formatted = None

        return render(request, self.template_name, {
            'file': file,
            'data': data,
            'columns': columns,
            'rows': rows,
            'json_data': json_data,
            'json_formatted': json_formatted,
        })

class FileUpdateView(View):
    template_name = 'fileuploader/file_update.html'

    def get(self, request, pk) -> HttpResponse:
        file = get_object_or_404(UploadedFile, pk=pk)
        form = FileUploadForm(initial={'file': file.file, 'database': file.database})
        return render(request, self.template_name, {'form': form, 'file': file})

    def post(self, request, pk) -> HttpResponse:
        file = get_object_or_404(UploadedFile, pk=pk)
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file.file = form.cleaned_data['file']
            file.database = form.cleaned_data['database']
            file.save()

            identifier = int(pk)
            # Update MongoDB or Elasticsearch based on the selected database
            if file.database == 'mongodb':
                client = MongoClient(mongodb_uri)
                db = client[mongodb_name]
                collection = db[mongodb_collection]
                
                # Delete documents with matching identifier
                result = collection.delete_many({'identifier': identifier})
                print(f"{result.deleted_count} documents deleted from MongoDB, {identifier}")

                if file.file.name.endswith('.csv'):
                    # Read CSV file
                    with file.file.open() as f:
                        data = pd.read_csv(f)
                        data_dict = data.to_dict(orient='records')

                        # Insert each row as a document with the identifier (pk)
                        for doc in data_dict:
                            doc['identifier'] = identifier
                            collection.insert_one(doc)
                            # print("inserted ", doc)

                elif file.file.name.endswith('.json'):
                    # Read JSON file
                    with file.file.open() as f:
                        json_data = json.load(f)

                        # Insert the JSON data directly with the identifier (pk)
                        json_data['identifier'] = identifier
                        collection.insert_one(json_data)
                        # print("inserted ", json_data)

            elif file.database == 'elasticsearch':
                es_uploader = ElasticsearchUploader(hosts=[{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
                index_name = mongodb_collection + '_' + str(identifier)
                es_uploader.update_data(request, file, index_name)  # Update Elasticsearch data
                # You might want to handle errors and return appropriate responses here

            return redirect('file_list')
        
        # Return an HttpResponse in case the form is not valid
        return HttpResponse("Form is not valid. Please check your input.")

class FileDeleteView(View):
    template_name = 'fileuploader/file_delete.html'

    def get(self, request, pk) -> HttpResponse:
        file = get_object_or_404(UploadedFile, pk=pk)
        return render(request, self.template_name, {'file': file})

    def post(self, request, pk) -> HttpResponse:
        file = get_object_or_404(UploadedFile, pk=pk)
        
        # Get the database choice for the uploaded file
        database_choice = file.database
        
        identifier = file.pk
        if database_choice == 'mongodb':
            # Connect to MongoDB and delete data from the collection
            client = MongoClient(mongodb_uri)
            db = client[mongodb_name]
            collection = db[mongodb_collection]
            
            result = collection.delete_many({'identifier': identifier})
            print(f"{result.deleted_count} documents deleted from Elasticsearch, {identifier}")
        
        elif database_choice == 'elasticsearch':
            es_uploader = ElasticsearchUploader(hosts=[{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
            index_name = mongodb_collection + '_' + str(identifier)
            result = es_uploader.delete_data(request, index_name)  
            
            print(f"{result['deleted']} documents deleted from Elasticsearch, {file.pk}")
        
        # Delete the file record
        file.delete()
        
        return redirect('file_list')

