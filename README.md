# Plate Number Recognition with Amazon Rekognition
## Read license plate number from existing video in S3

1. Create an empty S3 bucket in same region of your Amazon Rekognition service, please note down your bucket name.
2. Create the Amazon SQS queue.
3. Create the Amazon SNS topic.
4. Give Amazon Rekognition Video permission to publish the completion status of a video analysis operation to the Amazon SNS topic.
5. Subscribe the Amazon SQS queue to the Amazon SNS topic.

add this policy in SQS

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
