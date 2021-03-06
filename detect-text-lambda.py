import json
import urllib.parse
import boto3
import sys
import time
import re



class VideoDetect:
    jobId = ''
    rek = boto3.client('rekognition')
    sqs = boto3.client('sqs')
    sns = boto3.client('sns')
    
    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):    
        self.roleArn = role
        self.bucket = bucket
        self.video = video
    
    def StartTextDetection(self):
        response=self.rek.start_text_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)
        

    def GetTextDetectionResults(self):
        maxResults = 1000
        paginationToken = ''
        finished = False
        
        dynamodb = None
        

        while finished == False:
            response = self.rek.get_text_detection(JobId=self.startJobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken)

            print('Codec: ' + response['VideoMetadata']['Codec'])
            
            print('Duration: ' + str(response['VideoMetadata']['DurationMillis']))
            print('Format: ' + response['VideoMetadata']['Format'])
            print('Frame rate: ' + str(response['VideoMetadata']['FrameRate']))
            print()
            
            # REGEX for Indonesia's Car Plate Number
            plate_pattern = '^[A-Z]{1,2} [0-9]{1,4} [A-Z]{1,3}$'

            for textDetection in response['TextDetections']:
                text=textDetection['TextDetection']
                reg_result = re.match(plate_pattern, text['DetectedText'])
                if str(text['Type']) == 'LINE' and reg_result:

                    print("Timestamp: " + str(textDetection['Timestamp']))
                    print("   Text Detected: " + text['DetectedText'])
                    print("   Confidence: " +  str(text['Confidence']))
                    print ("      Bounding box")
                    print ("        Top: " + str(text['Geometry']['BoundingBox']['Top']))
                    print ("        Left: " + str(text['Geometry']['BoundingBox']['Left']))
                    print ("        Width: " +  str(text['Geometry']['BoundingBox']['Width']))
                    print ("        Height: " +  str(text['Geometry']['BoundingBox']['Height']))
                    print ("   Type: " + str(text['Type']) )
                    print()
                    
                    # write to dynamodb
                    
                    if not dynamodb:
                        dynamodb = boto3.resource('dynamodb')
                    table = dynamodb.Table('PlatNomorRekognition')
                    response = table.put_item(
                           Item={
                                'plat_nomor': text['DetectedText'],
                                'time_stamp': str(textDetection['Timestamp']),
                                'video_file': self.video,
                                'confidence': str(text['Confidence'])
                            }
                        )

                if 'NextToken' in response:
                    paginationToken = response['NextToken']
                else:
                    finished = True

    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False
    
        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)

            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine = dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                   ReceiptHandle=message['ReceiptHandle'])


        return succeeded
    
    def CreateTopicandQueue(self):
      
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        
        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']
 
        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)
 
        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

    

def lambda_handler(event, context):
    # Get the object from the event and show its content type
    s3 = boto3.client('s3')
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        roleArn = 'ROLE'   
        video = key

        analyzer=VideoDetect(roleArn, bucket,video)
        analyzer.CreateTopicandQueue()
    
        analyzer.StartTextDetection()
        if analyzer.GetSQSMessageSuccess()==True:
            analyzer.GetTextDetectionResults()
        
        analyzer.DeleteTopicandQueue()

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
