from .utils import ElasticsearchUploader

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse

from elasticsearch import Elasticsearch
from .form import FileUploadForm
from .models import UploadedFile

import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
from pymongo import MongoClient

# client = MongoClient('mongodb://localhost:27017/')
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongodb_uri)

def test_mongodb(request):
    # Connect to MongoDB
    db = client['dbt1']
    collection = db['colt1']

    # Retrieve data from the collection
    data = collection.find()

    # Convert the data to a list for printing
    data_list = list(data)

    # Print the data to the console
    for item in data_list:
        print(item)

    # Return a simple response
    return HttpResponse("MongoDB data printed to console.")

def test_elastic(request):
    try:
        # Connect to Elasticsearch cluster
        es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

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


def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            database_choice = form.cleaned_data['database']

            instance = UploadedFile(file=uploaded_file)
            instance.save()

            saved_instance_pk = instance.pk
            current_file = get_object_or_404(UploadedFile, pk=saved_instance_pk)

            db = client['dbt1']
            collection = db['colt1']

            print(database_choice)
            if database_choice == 'mongodb':
                print('Data inserted into MongoDB')
                if current_file.file.name.endswith('.csv'):
                # Read CSV file
                    with current_file.file.open() as f:
                        data = pd.read_csv(f)
                        data_dict = data.to_dict(orient='records')

                        # Insert each row as a document
                        for doc in data_dict:
                            collection.insert_one(doc)

                elif current_file.file.name.endswith('.json'):
                    # Read JSON file
                    with current_file.file.open() as f:
                        json_data = json.load(f)

                        # Insert the JSON data directly
                        collection.insert_one(json_data)

            if database_choice == 'elasticsearch':
                es_uploader = ElasticsearchUploader(hosts=[{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
                return es_uploader.upload_data(request, current_file)


            return redirect('upload_success')
    else:
        form = FileUploadForm()
    return render(request, 'fileuploader/upload.html', {'form': form})


def upload_success(request):
    return render(request, 'fileuploader/upload_success.html')

# def file_list(request):
    # files = UploadedFile.objects.all()
    # return render(request, 'fileuploader/file_list.html', {'files': files})

def generate_word_cloud_from_data(data, file):
    # Combine all textual columns to create content for the word cloud
    content = ""
    for column_name in data.columns:
        if data[column_name].dtype == 'object':  # Check if the column contains text data
            content += ' '.join(data[column_name].dropna()) + ' '

    # Check if the 'content' variable is not empty before creating the word cloud
    if content.strip():
        # Create and save the word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(content)
        image_path = f'media/wordcloud_{file.pk}.png'
        wordcloud.to_file(image_path)
        return image_path
    else:
        return None


def file_list(request):
    files = UploadedFile.objects.all()
    word_clouds = []

    for file in files:
        data = None
        if file.file.name.endswith('.json'):
            ...
            # Read JSON file
            # with file.file.open() as f:
                # data = json.load(f)
                # data = pd.DataFrame(data)  # Convert JSON to DataFrame
        elif file.file.name.endswith('.csv'):
            # Read CSV file
            with file.file.open() as f:
                data = pd.read_csv(f)

        if data is not None:
            image_path = generate_word_cloud_from_data(data, file)  # Pass 'file' object as an argument
            if image_path:
                word_clouds.append((file, image_path))

    return render(request, 'fileuploader/file_list.html', {'files': files, 'word_clouds': word_clouds})




# def file_detail(request, pk):
    # file = get_object_or_404(UploadedFile, pk=pk)
    # return render(request, 'fileuploader/file_detail.html', {'file': file})
# fileuploader/views.py

def file_detail(request, pk):
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

    return render(request, 'fileuploader/file_detail.html', {
        'file': file,
        'data': data,
        'columns': columns,
        'rows': rows,
        'json_data': json_data,
        'json_formatted': json_formatted,
    })


def file_update(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file.file = form.cleaned_data['file']
            file.database = form.cleaned_data['database']
            file.save()
            return redirect('file_list')
    else:
        form = FileUploadForm(initial={'file': file.file, 'database': file.database})
    return render(request, 'fileuploader/file_update.html', {'form': form, 'file': file})

def file_delete(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    if request.method == 'POST':
        file.delete()
        return redirect('file_list')
    return render(request, 'fileuploader/file_delete.html', {'file': file})

