import boto3
from django.conf import settings


class ClientManager(object):
    def __init__(self):
        self.boto3 = boto3.Session()
        self.ec2 = self.boto3.resource("ec2")
        self.ec2_client = self.boto3.client("ec2")

    def create_instance(self, name: str = None):
        """
        Input:
            - name: String
        Output:
            - Reservation ID
        """
        response = self.ec2_client.run_instances(
            MaxCount=1,
            MinCount=1,
            InstanceType="t2.micro",
            LaunchTemplate={
                "LaunchTemplateId": "lt-07067c8b5ac945df2",
            },
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": f"{name}(client instance)"},
                    ],
                },
            ],
        )
        return (
            response["Instances"][0]["InstanceId"],
            response["Instances"][0]["PrivateIpAddress"],
        )

    def stop_instance(self, instance_id):
        self.ec2_client.stop_instances(InstanceIds=[instance_id])
        return True


from django.conf import settings
import os
from django.template import Template, Context

class NginxConfigGenerator:
    template_dir = os.path.join(settings.BASE_DIR, "nginx_templates")
    
    def generate_config_for_package(self, package):
        pass

    def _generate_for_subdomain(self):
        pass

    def _generate_for_custom_domain_without_ssl(self):
        pass

    def _generate_for_custom_domain_with_ssl(self):
        pass

    def _render(self, template_name, context):
        with open(os.path.join(self.template_dir, template_name), 'r') as f:
            src = Template(f.read())
            # context = Context({"full_subdomain": subdomain, "client_ip": client_ip})
            result = src.render(context)
            print(result)
        return result