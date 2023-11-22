from django.shortcuts import render

# Create your views here.
# Create cluster entrace.
from django.http import JsonResponse
import requests
import os
import boto3
import json
import time
from django.views.decorators.csrf import csrf_exempt
import subprocess

instance_base_specification = {
    "t2.micro": 1,
    "t2.small": 2,
    "m5.large": 8,
    "m5.xlarge": 16,
    "m5.2xlarge": 32,
    "m5.4xlarge": 64,
    "c6g.large": 4,
    "c6g.12xlarge": 96,
    "c5.12xlarge": 96,
    "r6g.large": 16,
    "r5.12xlarge": 384,
    "r6g.4xlarge": 128,
    "c6.12xlarge": 96,
    "r5.8xlarge": 256,
    "r5.16xlarge": 512,
    "c4.2xlarge": 15,
    "c5.2xlarge": 16
}
m5_series = [1, 2, 4, 8, 12, 16, 24]
c6g_series = [1, 2, 4, 6, 12, 16]
r6g_series = [1, 2, 4, 6, 12, 16]

header = {
    "Authorization": "Basic YWRtaW46YWRtaW4="
}

# manager check controller.
def index(request):
    url = request.build_absolute_uri()
    built_url = url.replace('8000', '9200')
    f_url = built_url.replace('cluster_node_status/', '')
    print("built final url is: {}".format(f_url))
    try:
        res = requests.get(f_url, headers=header)
        res_list = res.json()
        result = []
        for i in res_list: 
            result.append(i)
        ret = {
            "result": result
        }
    except Exception as e:
        ret = {
            "error": "fetch failed"
        }

    return success_response(ret)

def success_response(ret):
    response = JsonResponse(ret, safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response

# This method is used to create a opensearch cluster.
## The annotation is to avoid csrf validation, the solution is from stackoverflow: https://stackoverflow.com/a/38663331.
@csrf_exempt
def index1(request, creation_type): 
    print("received request is: {}".format(request.body))
    request_body = json.loads(request.body.decode("utf-8"))
    if creation_type is None:
        response = JsonResponse({"acknowledge": False}, safe=False)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    # There's two cases we need to support, creating one or multiple cluster manager nodes, creating one or more data nodes.
    # In the add nodes method, we need to support two cases as well, adding one or more data nodes, adding one or more ml nodes.
    cluster_ips = request_body['clusterIps']
    print('cluster_ips are: {}'.format(cluster_ips))
    if creation_type == 'postprocessing':
        if cluster_ips is None or cluster_ips == '':
            raise Exception("cluster ips are null")
        else:
            public_ips = request_body['publicIps'].split(',')
            print("received public ip is : {}".format(public_ips))
            for public_ip in public_ips:
                if public_ip is None:
                    continue
                else:
                    post_opensearch_yml_file_processing(cluster_ips, public_ip)
    elif creation_type == 'checkClusterConfig':
        public_ips = request_body['publicIps'].split(',')
        for public_ip in public_ips:
            fetch_remote_cluster_config = """
                scp -i ~/zaniu-ec2-nopass.pem ec2-user@{}:~/config.properties .
            """.format(public_ip)
        subprocess.run(fetch_remote_cluster_config, shell=True)
        if not os.path.exists('./config.properties'):
            raise Exception("config file fetch failed")
        else:
            res = {}
            with open('./config.properties', 'r') as configs:
                for line in configs:
                    line = line.replace('\n', '')
                    if "=" in line:
                        key, value = line.split("=")
                        res[key] =value
                        print("current key is: {}, current value is: {}".format(key, value))
            subprocess.run("rm -f ./config.properties", shell=True)
            response = JsonResponse(res, safe=False)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    else: # create new group or new nodes
        group_name = request_body['groupName']
        if group_name is None:
            response = JsonResponse({"acknowledge": False, "errMsg": "group name is null, please check your input!"}, safe=False)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        create_count = request_body['instanceCount']
        node_type = request_body['nodeType']
        ebs_size = request_body['ebsSize']
        node_purpose = request_body['nodePurpose']
        
        opensearch_version = request_body['opensearchVersion'] if 'opensearchVersion' in request_body else ''
        opensearch_platform = request_body['opensearchPlatform'] if 'opensearchPlatform' in request_body else ''
        opensearch_source = request_body['opensearchSource'] if 'opensearchSource' in request_body else ''
        build_no = request_body['buildNo'] if 'buildNo' in request_body else ''
        data_node_public_ip = request_body['dataNodePublicIp'] if 'dataNodePublicIp' in request_body else ''
        create_instance(int(create_count), node_type, int(ebs_size), node_purpose, group_name, cluster_ips, opensearch_version,
                    opensearch_source, opensearch_platform, build_no, data_node_public_ip, creation_type=creation_type)
        
    response = JsonResponse({"acknowledge": True}, safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response

def write_config_file_to_data_node(opensearch_version, opensearch_platform, build_no, opensearch_source, public_dns_name):
    with open('./config.properties', 'a') as config_file:
        config_file.write("opensearch_version=" + opensearch_version + "\n")
        config_file.write("platform=" + opensearch_platform + "\n")
        if build_no is not None and build_no != '':
            config_file.write("ci_build_no=" + build_no + "\n")
        config_file.write("opensearch_source=" + opensearch_source + "\n")
        config_file.write("plugin_version=" + opensearch_version + ".0\n")
        config_file.write("\n")
    scp_config_command = """
        scp -i ~/zaniu-ec2-nopass.pem ./config.properties ec2-user@{}:~/
        rm -rf ./config.properties
    """.format(public_dns_name)
    subprocess.run(scp_config_command, shell=True)

def fetch_config_from_data_node_and_upload_to_other_node(data_node_public_ip, public_dns_name):
    fetch_command = """
        rm -rf ./config.properties
        scp -i ~/zaniu-ec2-nopass.pem ec2-user@{}:~/config.properties .
        scp -i ~/zaniu-ec2-nopass.pem ./config.properties ec2-user@{}:~/
        rm -rf ./config.properties
    """.format(data_node_public_ip, public_dns_name)
    print("fetch data node config and upload to other node command is: {}".format(fetch_command))
    subprocess.run(fetch_command, shell=True)

# create a new EC2 instance
def create_instance(create_count, instance_type, ebs_size, node_purpose, group_name, cluster_ips, opensearch_version,
                        opensearch_source, opensearch_platform, build_no, data_node_public_ip, creation_type):
    print("create_instance parameters: create_count={}, node_type={}, ebs_size={}, node_purpose={}, group_name={}, cluster_ips={}, opensearch_version={}, opensearch_source={}, opensearch_platform={}, build_no={}, data_node_public_ip={}, creation_type={}".format(create_count, instance_type, ebs_size, node_purpose, group_name, cluster_ips, opensearch_version, opensearch_source, opensearch_platform, build_no, data_node_public_ip, creation_type))
    ec2_res = boto3.resource('ec2')
    instances = ec2_res.create_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': ebs_size,
                },
            },
        ],
        ImageId='ami-072bfb8ae2c884cc4' if opensearch_platform == 'x64' else 'ami-0e6a6d31c24757ae2', 
        # ImageId='ami-0e6a6d31c24757ae2', # arm
        MinCount=1,
        MaxCount=create_count,
        InstanceType=instance_type,
        KeyName='zaniu-ec2-nopass',
        SecurityGroupIds=['sg-00c771f61ffe68528'],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': node_purpose
                    },
                    {
                        'Key': 'Group',
                        'Value': group_name
                    }
                ]
            },
        ]
    )
    for instance in instances:
        memory = instance_memory_lookup(instance_type)
        create_jvm_file(memory)
        create_opensearch_yml_file(instance, node_purpose, cluster_ips)
        time.sleep(3)
        public_dns_name = get_public_ip_address_by_instance_id(instance.instance_id)
        if not (public_dns_name == '' or public_dns_name is None):
            execute_shell_scripts(public_dns_name)
            if creation_type == 'group':
                write_config_file_to_data_node(opensearch_version, opensearch_platform, build_no, opensearch_source, public_dns_name)
            else:
                fetch_config_from_data_node_and_upload_to_other_node(data_node_public_ip, public_dns_name)
            # start install opensearch and start opensearch!
            start_command = """
                ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                    sh ~/kill_opensearch.sh
                    sh ~/install_opensearch.sh
                    nohup sh ~/kill_and_restart.sh > /dev/null 2>&1 &
            """.format(public_dns_name)
            res = subprocess.run(start_command, shell=True)
            print(res)
            print("Done!!")


def get_public_ip_address_by_instance_id(instance_id):
    client = boto3.client('ec2')
    instance_desc = client.describe_instances(InstanceIds=[instance_id])
    public_dns_name = instance_desc['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicDnsName']
    print("created node public dns name is: {}".format(public_dns_name))
    return public_dns_name


def instance_memory_lookup(instance_type):
    memory = instance_base_specification[instance_type]
    print('memory is: {}'.format(memory))
    return memory
        


def execute_shell_scripts(public_ip_address):
    test_command = "scp -i ~/zaniu-ec2-nopass.pem ~/ec2_connect_test.txt ec2-user@{}:~/".format(public_ip_address)
    print('executing the test connect: {}'.format(test_command))
    res = os.system(test_command)
    while res != 0:
        res = os.system(test_command)
    command = "/Users/zaniu/Documents/opensearch-configs/shells/transfer_install_scripts.sh {}".format(public_ip_address)
    print('executing the transfer command: {}'.format(command))
    os.system(command)


def create_jvm_file(memory):
    with open('/Users/zaniu/Documents/opensearch-configs/shells/jvm.options.bak', 'r') as jvm_file:
        jvm_options = jvm_file.read()
        allocate_memory = memory / 2
        if allocate_memory < 1:
            allocate_memory_str = str(int(allocate_memory * 1000)) + 'm'
        else:
            allocate_memory_str = str(int(allocate_memory)) + 'g'
        jvm_options = jvm_options.replace('-Xms1g', '-Xms' + allocate_memory_str)
        jvm_options = jvm_options.replace('-Xmx1g', '-Xmx' + allocate_memory_str)
        with open('/Users/zaniu/Documents/opensearch-configs/shells/jvm.options', 'w') as tmp_jvm:
            tmp_jvm.write(jvm_options)


def create_opensearch_yml_file(instance, node_purpose, cluster_ips):
    ips_str = ''
    if cluster_ips is None or cluster_ips == '': 
        ips_str = '"'+ instance.private_dns_name + '"'
    else:
        cluster_ips_array = cluster_ips.split(',')
        for ip in cluster_ips_array:
            ips_str += '"' + ip + '",'
        ips_str += '"'+ instance.private_dns_name + '"'
    with open('/Users/zaniu/Documents/opensearch-configs/shells/opensearch.yml.bak', 'r') as opensearch_yml:
        opensearch_yml_content = opensearch_yml.read()
        opensearch_yml_content = opensearch_yml_content.replace('# cluster.name: mycluster', 'cluster.name: mycluster')
        opensearch_yml_content = opensearch_yml_content.replace('discovery.seed_hosts: []',
                                                                    'discovery.seed_hosts: [' + ips_str + ']')
        if node_purpose == 'data_node':  # current is data node.
            node_roles = "data, ingest, cluster_manager"
            opensearch_yml_content = opensearch_yml_content.replace('cluster.initial_cluster_manager_nodes: []',
                                                                    'cluster.initial_cluster_manager_nodes: [' +
                                                                    ips_str + ']')
        elif node_purpose == 'ml_node':
            node_roles = "ml, cluster_manager"
           
        else:  # debug purpose
            node_roles = "data, ingest, ml, cluster_manager"

        opensearch_yml_content = opensearch_yml_content.replace('node.roles: []', 'node.roles: [ ' + node_roles + ' ]')

        with open('/Users/zaniu/Documents/opensearch-configs/shells/opensearch.yml', 'w') as tmp_opensearch_yml:
            tmp_opensearch_yml.write(opensearch_yml_content)


def post_opensearch_yml_file_processing(cluster_ips, public_ip):
    ips_str = ''
    if cluster_ips is None or cluster_ips == '': 
        raise Exception("cluster ip should not be null")
    else: 
        for ip in cluster_ips.split(','):
            ips_str += '"' + ip + '",'
    ips_str = ips_str.removesuffix(',')
    
    fetch_remote_opensearch_config = """
        scp -i ~/zaniu-ec2-nopass.pem ec2-user@{}:~/opensearch/config/opensearch.yml .
    """.format(public_ip)

    print("fetch remote config command: {}".format(fetch_remote_opensearch_config))
    res = subprocess.run(fetch_remote_opensearch_config, shell=True)
    print("fetch command result is:{}".format(res))
    print("cluster ips are: {}".format(cluster_ips))

    remove_temp = 'ls ./opensearch.yml'
    res = subprocess.run(remove_temp, shell=True)
    print("check if file exist: {}".format(res))

    if os.path.exists('./opensearch.yml.tmp'): 
        os.remove('./opensearch.yml.tmp')
    with open('./opensearch.yml', 'r') as opensearch_yml:
        for line in opensearch_yml:
            with open('./opensearch.yml.tmp', 'a') as tmp_opensearch_yml:
                if "discovery.seed_hosts" in line:
                    tmp_opensearch_yml.write("discovery.seed_hosts: [" + ips_str + "]\n")
                else:
                    tmp_opensearch_yml.write(line)
    
    command = """
        scp -i ~/zaniu-ec2-nopass.pem ./opensearch.yml.tmp ec2-user@{}:~/
        ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
            mv ~/opensearch.yml.tmp ~/opensearch.yml
            cp ~/opensearch.yml ~/opensearch/config/
    """.format(public_ip, public_ip)
    print(command)
    res = subprocess.run(command, shell=True)
    res = subprocess.run("rm -rf ./opensearch.yml.tmp", shell=True)
    print(res)