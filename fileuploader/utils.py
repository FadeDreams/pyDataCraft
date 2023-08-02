from elasticsearch import Elasticsearch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
import json



class ElasticsearchUploader:
    def __init__(self, hosts):
        self.es = Elasticsearch(hosts=hosts)

    def upload_data(self, request, current_file):
        try:
            if self.es.ping():
                index_name = 'colt1'

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


