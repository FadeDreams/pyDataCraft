## Installation

1. Clone this repository:

   ```bash
   git clone git@github.com:FadeDreams/task1.git
   cd task1
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. edit .env file and make sure elasticsearch and mongodb are running:

```
MONGODB_URI=mongodb://localhost:27017/
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
MONGODB_NAME=dbt1
MONGODB_COLLECTION=colt1
```

3. head to: http://localhost:8000/fileuploader/
