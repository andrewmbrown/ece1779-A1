import boto3 
from boto3.dynamodb.conditions import Key
from app.models import User 

from access import access_keys

class AwsSession:

    def __init__(self):

        self.AWS_ACC_KEY = access_keys['AWS_ACC_KEY']
        self.AWS_SEC_KEY = access_keys['AWS_SECRET_KEY']

        self.user_table_name = 'user-test'
        self.image_table_name = 'image-location-test'

        session = boto3.Session(
                aws_access_key_id=self.AWS_ACC_KEY,
                aws_secret_access_key=self.AWS_SEC_KEY,
                region_name='us-east-1')
        self.s3 = boto3.client('s3', 
            aws_access_key_id=self.AWS_ACC_KEY, 
            aws_secret_access_key=self.AWS_SEC_KEY, 
            region_name="us-east-1")
        self.ddb = session.resource('dynamodb')
        
        self.user_table = self.ddb.Table(self.user_table_name)
        # self.image_location_table = self.ddb.Table(self.image_table_name)

        self.bucket = 'ece1779a3g81'
        self.bucket_url_base = 'https://ece1779a3g81.s3.amazonaws.com/'

    def DDB_get_user(self, username):

        response = self.user_table.query(
            KeyConditionExpression=Key('username').eq(username)
        )
        if len(response) < 1:
            # no users found with that username
            return -1
        raw_user = response["Items"][0]
        user = User(
                username=raw_user["username"],
                email=raw_user["email"],
                password_hash=raw_user["password_hash"]
            )
        return user

    def DDB_add_user(self, username, email, password):
        return
