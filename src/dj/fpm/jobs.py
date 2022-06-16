import boto3


class ClientManager(object):
    def __init__(self):
        self.ec2 = boto3.client("ec2")

    def create_instance(self):
        """
        Input:
            - Notihing
        Output:
            - Reservation ID
        """
        AMI_ID = "ami-0cff7528ff583bf9a"
        self.ec2.create_instances(
            MaxCount=1, MinCount=1, ImageId=AMI_ID, InstanceType="t2.micro"
        )
