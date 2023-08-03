from elasticsearch import Elasticsearch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
import json
import os
from wordcloud import WordCloud
import pandas as pd

class ElasticsearchUploader:
    def __init__(self, hosts):
        self.es = Elasticsearch(hosts=hosts)

    def upload_data(self, request, current_file, index_name):
        try:
            if self.es.ping():
                # index_name = f'colt1_{identifier}'  # Use the identifier in the index name

                if not self.es.indices.exists(index=index_name):
                    self.es.indices.create(index=index_name)

                if current_file.file.name.endswith('.csv'):
                    with current_file.file.open() as f:
                        data = pd.read_csv(f)
                        data_dict = data.to_dict(orient='records')

                        for doc in data_dict:
                            self.es.index(index=index_name, body=doc)

                elif current_file.file.name.endswith('.json'):
                    with current_file.file.open() as f:
                        json_data = json.load(f)
                        self.es.index(index=index_name, body=json_data)

                response_data = {
                    "message": f"Data indexed into Elasticsearch index '{index_name}' successfully"
                }

                return render(request, 'fileuploader/elastic_upload_success.html', {'response_data': response_data})

            else:
                return JsonResponse({"message": "Elasticsearch cluster is not reachable"})

        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"})

    def update_data(self, request, current_file, index_name):
            try:
                if self.es.ping():
                    # index_name = f'colt1_{identifier}'  # Use the identifier in the index name

                    if self.es.indices.exists(index=index_name):
                        # Delete the existing index
                        self.es.indices.delete(index=index_name)

                    # Create a new index
                    self.es.indices.create(index=index_name)

                    if current_file.file.name.endswith('.csv'):
                        with current_file.file.open() as f:
                            data = pd.read_csv(f)
                            data_dict = data.to_dict(orient='records')

                            for doc in data_dict:
                                # Assuming 'id' is the unique identifier in your document
                                self.es.index(index=index_name, body=doc, id=doc['id'])

                    elif current_file.file.name.endswith('.json'):
                        with current_file.file.open() as f:
                            json_data = json.load(f)
                            # Assuming 'id' is the unique identifier in your document
                            self.es.index(index=index_name, body=json_data, id=json_data['id'])

                    response_data = {
                        "message": f"Data updated in Elasticsearch index '{index_name}' successfully"
                    }

                    return render(request, 'fileuploader/elastic_upload_success.html', {'response_data': response_data})

                else:
                    return JsonResponse({"message": "Elasticsearch cluster is not reachable"})

            except Exception as e:
                return JsonResponse({"message": f"Error: {str(e)}"})


    def delete_data(self, request, index_name):
        try:
            if self.es.ping():
                if self.es.indices.exists(index=index_name):
                    # Delete the index
                    self.es.indices.delete(index=index_name)
                    response_message = f"Elasticsearch index '{index_name}' deleted successfully"
                    response_data = {"deleted": True, "message": response_message}
                else:
                    response_message = f"Elasticsearch index '{index_name}' does not exist"
                    response_data = {"deleted": False, "message": response_message}

                return response_data

            else:
                return {"deleted": False, "message": "Elasticsearch cluster is not reachable"}

        except Exception as e:
            return {"deleted": False, "message": f"Error: {str(e)}"}


def generate_word_cloud_from_data(data, file):
    content = ""
    for column_name in data.columns:
        if data[column_name].dtype == 'object':
            column_values = data[column_name].dropna()
            if all(isinstance(value, str) for value in column_values):
                content += ' '.join(column_values) + ' '
            elif all(isinstance(value, list) for value in column_values):
                content += ' '.join([item for sublist in column_values for item in sublist]) + ' '

    if content.strip():
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(content)
        image_path = f'media/wordcloud_{file.pk}.png'
        wordcloud.to_file(image_path)
        return image_path
    else:
        return None

