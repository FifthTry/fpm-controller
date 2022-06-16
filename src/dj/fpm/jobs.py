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
        AMI_ID = "ami-0d58faa21cb14df81"
        instances = self.ec2.create_instances(
            MaxCount=1, MinCount=1, ImageId=AMI_ID, InstanceType="t2.micro"
        )
        # Returns a list of all the instances created(in this case, only one)
        instance = instances[0]
        return instance.id
