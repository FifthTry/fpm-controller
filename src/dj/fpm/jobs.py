import boto3
from django.conf import settings
from textwrap import dedent
import subprocess

import os
from django.template import Template, Context
from huey import SqliteHuey


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


class NginxConfigGenerator:
    template_dir = os.path.join(settings.BASE_DIR, "nginx_templates")

    def __init__(self, package, server_instance):
        self.package = package
        self.server_instance = server_instance

    def generate(self):
        self._generate_for_subdomain()
        for domain_instance in self.package.domains.all():
            if domain_instance.state != "SUCCESS":
                self._generate_for_custom_domain_without_ssl(domain_instance)
                self.reload_nginx()
                domain_instance.state = "WAITING"
                domain_instance.save()
                is_success = self._generate_ssl_certificate(domain_instance)
                if is_success:
                    self._generate_for_custom_domain_with_ssl(domain_instance)
                    domain_instance.state = "SUCCESS"
                else:
                    domain_instance.state = "FAILED"
                domain_instance.save()
        self.reload_nginx()

    def _generate_for_subdomain(self):
        context = Context(
            {
                "full_subdomain": f"{self.package.slug}.5thtry.com",
                "client_ip": self.server_instance.ip,
            }
        )
        template_name = "subdomain.txt"
        with open(
            os.path.join(
                settings.NGINX_CONFIG_DIR, f"{self.package.slug}_subdomain.conf"
            ),
            "w+",
        ) as f:
            f.write(dedent(self._render(template_name, context)))

    def _generate_for_custom_domain_without_ssl(self, domain_instance):
        context = Context(
            {
                "full_domain": domain_instance.custom_domain,
                "client_ip": self.server_instance.ip,
            }
        )
        template_name = "custom_domain_pre_ssl.txt"
        with open(
            os.path.join(
                settings.NGINX_CONFIG_DIR,
                f"{self.package.slug}_{domain_instance.id}.conf",
            ),
            "w+",
        ) as f:
            f.write(dedent(self._render(template_name, context)))

    def _generate_ssl_certificate(self, domain_instance):
        domain_name = domain_instance.custom_domain
        os.makedirs(
            f"/var/www/html/certs/{domain_name}/.well-known/acme-challenge/",
            exist_ok=True,
        )
        """
            certbot certonly: Run certbot to just generate the certificate
            -d {domain_name}: For the domain name
            --webroot: Use webroot method to generate config
            -w <dir>: Directory to keep the challenge
            -n: Non interactive. In case of reuse, this fails silently

            For the scenario, where the certificate is not up for renewal, it still exits with 0
        """
        # Run the command and expect 0 code. If not, return false
        #

        # return subprocess.Popen(
        #     [
        #         f"sudo certbot certonly -d {domain_name} --webroot -w /var/www/html/certs/{domain_name} -n"
        #     ],
        #     shell=True,
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # ).wait() == 0
        #
        first_cert = (
            subprocess.Popen(
                [
                    f"/home/ec2-user/bin/acme.sh --issue --webroot /var/www/html/certs/{domain_name} -d {domain_name}"
                ],
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).wait()
            == 0
        )
        return (
            subprocess.Popen(
                [
                    f"/home/ec2-user/bin/acme.sh --install-cert -d {domain_name} --key-file /home/ec2-user/tls/{domain_name}.key --fullchain-file /home/ec2-user/tls/{domain_name}.pem"
                ],
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).wait()
            == 0
        )

    def _generate_for_custom_domain_with_ssl(self, domain_instance):
        context = Context(
            {
                "full_domain": domain_instance.custom_domain,
                "client_ip": self.server_instance.ip,
            }
        )
        template_name = "custom_domain_post_ssl.txt"
        with open(
            os.path.join(
                settings.NGINX_CONFIG_DIR,
                f"{self.package.slug}_{domain_instance.id}.conf",
            ),
            "w+",
        ) as f:
            f.write(dedent(self._render(template_name, context)))
        # domain_instance.state = "domain_instance.state = "WAITING""

    def reload_nginx(self):
        subprocess.Popen(
            ["sudo /bin/systemctl restart nginx"],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).wait()

    def _render(self, template_name, context):
        with open(os.path.join(self.template_dir, template_name), "r") as f:
            src = Template(f.read())
            result = src.render(context)
        return result
