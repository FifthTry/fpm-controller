import boto3
from django.conf import settings

class ClientManager(object):
    def __init__(self):
        self.boto3 = boto3.Session()
        self.ec2 = self.boto3.resource("ec2")
        self.ec2_client = self.boto3.client("ec2")

    def create_instance(self):
        """
        Input:
            - Notihing
        Output:
            - Reservation ID
        """
        response = self.ec2_client.run_instances(
            MaxCount=1,
            MinCount=1,
            # ImageId=settings.BASE_FPM_CLIENT_AMI_ID,
            InstanceType="t2.micro",
            LaunchTemplate={
                "LaunchTemplateId": "lt-07067c8b5ac945df2",
            },
        )
        return (response["Instances"][0]["InstanceId"], response["Instances"][0]["PrivateIpAddress"])

    def stop_instance(self, instance_id):
        self.ec2_client.stop_instances(InstanceIds=[instance_id])
        return True

# def test():
    