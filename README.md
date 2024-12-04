# BairesDevRSS
Just an exercise to fetch site data using threads and saving it on DB

---
# Pre-requisites
* A free aws account
* Thats all :D

---
# Configurations
<a name="how-to-create-lambda-layers"></a>
## How to create lambda Layers
1. Open aws cloudshell [page](https://console.aws.amazon.com/cloudshell) (make sure that you are at the same region of the lambda funcion)
2. Install desired python version (I am using 3.11 for this one)
```
sudo yum install python3.11
```
3. Install desired package
```
python3.11 -m pip install requests -t python/lib/python3.11/site-packages
```
<a name="unable-to-import-module"></a>
>[!NOTE]
> Some packages does not work when installed using this way, throwing `[ERROR] Runtime.ImportModuleError: Unable to import module` during execution. Just install it forcing the expected parameters for the lambda machine
>```
>pip install --platform manylinux2014_x86_64 --target=python --implementation cp --python-version 3.11 --only-binary=:all: --upgrade lxml
>```

4. Zip it
```
zip -r requests_layer.zip python
```
5. Publish layer
```
aws lambda publish-layer-version --layer-name requests --zip-file fileb://requests_layer.zip --compatible-runtimes python3.11
```

---

---
<a name="create-dynamo-table"></a>
## Create new DynamoDB table.
1. Access DynamoDB [page](https://console.aws.amazon.com/dynamodbv2)
2. Click on "Create table" button
3. Input table name. (We are using `BairesDevJobs` for this exercise)
4. Input partition key, aka primary key. (We are using `jobID` for this exercise)
5. Click on "Create table" button

---
<a name="create-lambda-function"></a>
## Create new lambda funcion.
1. Access AWS Lambda [page](https://console.aws.amazon.com/lambda)
2. Click on "Create function" button
3. Make sure to select a python version that is available at cloudshell too. (3.11 for this exercise)
4. Make sure to enable function URL, in additional settings section.
  - Select auth type = NONE. Just dont share this url and you will be safe.

<a name="add-layer-to-lambda-function"></a>
## Add layer to the lambda funciton
1. In the last section of your lambda function code tab.
2. Click on "Add a ayer"
3. Select custom layer
4. Choose the desired layer.
5. Repeat it untill all required layers was added. (we need requests and lxml layers for this exercises)
> [!IMPORTANT]
> if a layer is not showing, review the [How to create lambda Layers](#how-to-create-lambda-layers) section

<a name="grant-dynamo-permission-to-lambda-function"></a>
## Grant default read/write DynamoDB permission to the lambda function
1. Open configuration tab on lambda function page.
2. Select Permissions sub tab.
3. Click on IAM role link (It is just bellow role name)
4. Click on add a permission and select a policy that have getItem and UpdateItem for dynamoDB.
   - If you have any policy with it, just create a new one. [How to create a permission policy](#how-to-create-a-permission-policy) section.
5. Click on "Add permissions" button.


---
<a name="how-to-create-a-permission-policy"></a>
## How to create a permission policy
1. Access IAM policies [page](https://console.aws.amazon.com/iam/home#/policies)
2. Click on "Create Policy" button.
3. Select the allowed actions or configure the json directly.
   - For this example I used this old json, but not all actions are required.
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": [
				"dynamodb:BatchGetItem",
				"dynamodb:BatchWriteItem",
				"dynamodb:PutItem",
				"dynamodb:DeleteItem",
				"dynamodb:GetItem",
				"dynamodb:Scan",
				"dynamodb:Query",
				"dynamodb:UpdateItem"
			],
			"Resource": "*"
		}
	]
}
```
4. Click on "Next" button
5. Input the policy name
6. Click on "Create policy" button

---
<a name="instalation"></a>
# Instalation?
1. Just copy `extractor.py`, `FetchThread.py` and `lambda_function.py` files to lambda function.

## Run
1. Open function url using your prefered browser and/or RSS reader. (You can find it at the right side of your Lambda function diagram)
2. To filter a job just pass the search in url path.
   - Example: `https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.lambda-url.eu-central-1.on.aws/qa` will list only QA jobs.
> [!TIP]
> You can enable debug by passing it as query string parameter
> Example: `https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.lambda-url.eu-central-1.on.aws/qa?debug`
