from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
import boto3
from botocore.exceptions import ClientError
ec2 = boto3.client('ec2')

def index(request, action):
    instance_ids = request.GET.get('instance_ids', '')
    if instance_ids is None:
        my_err = {
            "error": "instance id is empty"
        }
        jsonRes = JsonResponse(my_err, content_type = "application/json", safe=False)
        jsonRes['Access-Control-Allow-Origin'] = '*'
        return jsonRes
    instance_id_list = instance_ids.split(',')
    for instance_id in instance_id_list:
        if action == 'ON':
        # Do a dryrun first to verify permissions
            try:
                ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            # Dry run succeeded, run start_instances without dryrun
            try:
                response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
                print(response)
            except ClientError as e:
                print(e)
        else:
            # Do a dryrun first to verify permissions
            try:
                ec2.stop_instances(InstanceIds=[instance_id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            # Dry run succeeded, call stop_instances without dryrun
            try:
                response = ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
                print(response)
            except ClientError as e:
                print(e)
    my_res = {
        "acknowledge": True
    }
    jsonRes = JsonResponse(my_res, content_type = "application/json", safe=False)
    jsonRes['Access-Control-Allow-Origin'] = '*'
    return jsonRes