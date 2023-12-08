from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
import subprocess
import boto3

ec2 = boto3.client('ec2')


def simple_describe():
    cluster = []
    instance_descriptions = ec2.describe_instances()['Reservations']
    for instance_description in instance_descriptions:
        for instance in instance_description['Instances']:
            # print("current instance information is:{}".format(instance))
            instance_id = instance['InstanceId']
            instance_state = instance['State']['Name']
            if instance_state == 'terminated' or instance_state == 'shutting-down':
                continue
            private_ip_address = instance['PrivateIpAddress']
            public_dns_name = instance['PublicDnsName']
            private_dns_name = instance['PrivateDnsName']
            instance_type = instance['InstanceType']
            launch_time = instance['LaunchTime']
            # print(launch_time)
            tags = instance['Tags']
            for tag in tags:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                elif tag['Key'] == 'Group':
                    group_name = tag['Value']
            if instance_state == 'running':
                command = """
                    ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                        ps -ef | grep opensearch | grep -v grep
                """.format(public_dns_name)
                res = subprocess.run(command, shell=True)
                print("res value is:{}".format(res.returncode))
                if res.returncode == 0:
                    os_running = "true"
                else: 
                    os_running = "false"
            else:
                os_running = "false"
            single_instance = {
                'instance_id': instance_id,
                'node_purpose': instance_name,
                'private_ip_address': private_ip_address,
                'public_dns_name': public_dns_name,
                'private_dns_name': private_dns_name,
                'instance_type': instance_type,
                'instance_state': instance_state,
                'group_name': group_name,
                'opensearch_running': os_running,
                'launch_time': launch_time
            }
            print('current instance id is: {}, os running status is: {}'.format(instance_id, os_running))
            cluster.append(single_instance)
    return cluster


def index(request):
    cluster = simple_describe()
    result = {
        "result": cluster
    }
    response = JsonResponse(result, content_type ="application/json", safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response
