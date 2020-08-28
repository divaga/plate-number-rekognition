# Plate Number Recognition with Amazon Rekognition
## Read license plate number from existing video in S3

1. Create an empty S3 bucket in same region of your Amazon Rekognition service, please note down your bucket name.
2. Create the Amazon SNS topic, prepend the topic name with "AmazonRekognition"
3. Create the Amazon SQS queue.
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
6. Create Cloud9 Environment
7. Clone demo repository: git clone https://github.com/divaga/plate-number-rekognition.git
8. Copy video to S3 bucket
9. Open detect-text.py and chante roleArn, bucket and video file
10. execute detect-text.py

