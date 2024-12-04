import boto3
import json
import requests
from threading import Thread

class HttpRequestThread(Thread):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
        self.http_status_code = None
        self.body = None

    def run(self) -> None:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"}
            req  = requests.get(self.url, headers = headers, timeout = 2.001)
            req.raise_for_status()
            self.http_status_code = req.status_code
            self.body = req.text
        except requests.HTTPError as e:
            self.http_status_code = req.status_code
        except requests.Timeout as e:
            self.http_status_code = 102

class FetchThread(Thread):
    def __init__(self, data: dict, table: boto3.resource('dynamodb').Table) -> None:
        super().__init__()
        self.id = data['id']
        self.table = table
        self.data = data

    def __iter__(self):
        # Return an iterator over the desired attributes
        return iter({"id":self.id, "data":self.data}.items())

    def __getitem__(self, key):
        # Allow subscript access to attributes
        attributes = {"id":self.id, "data":self.data}
        if key in attributes:
            return attributes[key]
        raise KeyError(f"'{key}' not found in HttpRequestThread")

    def updateDB(self):
        validDate = self.data.get('validDate')
        self.data.pop('id', None)
        data = {
            "data": self.data,
            "validDate": validDate
        }
        update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in data)
        expression_attribute_names = {f"#{k}": k for k in data}
        expression_attribute_values = {f":{k}": v for k, v in data.items()}
        self.table.update_item(
            Key = {'jobID': self.id},
            UpdateExpression = update_expression,
            ExpressionAttributeNames = expression_attribute_names,
            ExpressionAttributeValues = expression_attribute_values
        )

    def getDB(self):
        found =  self.table.get_item(Key = {'jobID': self.id})
        found = found.get('Item')
        if found:
            found = found.get('data')
        self.data = found or self.data

    def merge(self,data):
        if self.data == None:
            self.data = {}
        self.data = self.data | data
    
    def fetchData(self):
        url = f'https://applicants.bairesdev.com/api/JobPosting?JobPostingId={self.id}'
        jp = HttpRequestThread(url)
        jp.start()

        url = f'https://applicants.bairesdev.com/api/Job?JobOfferId={self.id}'
        jo = HttpRequestThread(url)
        jo.start()

        jp.join()
        jo.join()

        job = {}
        if jp.body and json.loads(jp.body):
            body = json.loads(jp.body)
            #job['title'] = body.get('title') # already have this on xml
            #job['shortDesc'] = body.get('description') # already have this on xml
            job['postDate'] = body.get('datePosted')
            job['validDate'] = body.get('validThrough')
            req = body.get('applicantLocationRequirements')
            if req:
                job['requirements'] = { req['@type']: req['name'].split(',')}
            job['hiring'] = body.get('hiringOrganization')
            job['location'] = body.get('jobLocationType')
            job['employmentType'] = body.get('employmentType')

        if jo.body and json.loads(jo.body):
            body = json.loads(jo.body)
            if body and body.get('jobResults') and body.get('jobResults')[0]:
                body = body.get('jobResults')[0]
                #job['title'] = body.get('title') # already have this on xml
                job['description'] = body.get('description')
                #job['technology'] = body.get('technology') # already have this on xml


        self.merge({k: v for k, v in job.items() if v is not None})


    def run(self) -> None:
        self.getDB()
        if self.data == None or not self.data.get('description'):
            self.fetchData()
            self.updateDB()

