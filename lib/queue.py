import boto3
import json

def to_msg_attributes(data):
    # Options are String, Number, String.Array
    # https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html#SNSMessageAttributes.DataTypes
    # @todo improve
    return {key: {'StringValue': str(event[key]), 'DataType': 'string'} for key in data}

class Queue(object):
    pass

class EmitterViaSns(object):
    def __init__(self, sns):
        self.sns = sns
        self.queue_url = None
        

    def emit(self, name, data={}, delay=0, body=''):
        pass
        """
        # @todo
        self.sns.send_message(
            QueueUrl=self.queue_url,
            MessageBody=body,
            DelaySeconds=delay,
            MessageAttributes=to_msg_attributes(data),
            MessageDeduplicationId='string',
            MessageGroupId='string'
        )
        """

# Use dynanomdb to store job state (queued, started, complete)
# which trigger sns to sqs
# Before queuing job, ensure it doesn't already exist
class Job(object):

    def start(self):
        pass

    def finish(self):
        pass

    def progress(self):
        pass

    def state(self):
        pass

    def retry(self):
        pass
        # Put back on queue

class UniqueJob(Job):

    def job_id(self):
        pass
    
    def is_already_working(self):
        pass
    