# Plate Number Recognition with Amazon Rekognition
## Read license plate number from existing video in S3

1. Create an empty S3 bucket in same region of your Amazon Rekognition service, please note down your bucket name.
2. Create the Amazon SNS topic, prepend the topic name with "AmazonRekognition" and note down your SNS ARN.
3. Create the Amazon SQS queue, note down your SQS ARN.
4. Allow SNS to send message to SQS, modify your SQS access policy:

```
{
  "Statement": [{
    "Effect":"Allow",
    "Principal": {
      "Service": "sns.amazonaws.com"
    },
    "Action":"sqs:SendMessage",
    "Resource":"<YOUR-SQS-ARN>",
    "Condition":{
      "ArnEquals":{
        "aws:SourceArn":"<YOUR-SNS-ARN>"
      }
    }
  }]
}
```

4. Give Amazon Rekognition Video permission to publish the completion status of a video analysis operation to the Amazon SNS topic.
- In IAM, create new policy:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "<YOUR-TOPIC-ARN>"
        }
    ]
}

```
- Create new Service Role, Choose Rekognition as AWS Service. Please note service role ARN.


5. Subscribe the Amazon SQS queue to the Amazon SNS topic.
6. Create Cloud9 Environment with default configuration and install boto3
```
sudo pip install boto3
```
7. Clone demo repository: 

```
git clone https://github.com/divaga/plate-number-rekognition.git
```

8. Go to plate-number-rekognition folder and copy sample video to your S3 bucket

```
aws s3 cp traffic.mp4 s3://<YOUR-S3-BUCKET-NAME>/traffic.mp4
```
9. Open detect-text.py and change value for roleArn (from step no.4), bucket name (from step no.1) and video file name (from step no.8)
10. execute detect-text.py
```
python detext-text.py 
```

