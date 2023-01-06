from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
import os
import subprocess

def index(request, operation):
    with open('/Users/zaniu/Documents/opensearch-configs/shells/config.properties', 'r') as config:
        for line in config:
            if 'plugin_version' in line:
                plugin_version = line.split('=')[1].replace('\n', '')
    command = ""
    public_dns_name = request.GET.get('public_dns_name', '')
    print("passed into public_dns_name value is: {}".format(public_dns_name))
    if operation == 'stop':
        command = """
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./kill_opensearch.sh
        """.format(public_dns_name)
    elif operation == 'installml':
        command = """
        sh /Users/zaniu/Documents/opensearch-configs/shells/scp_to_remote.sh /Users/zaniu/Documents/opensearch-configs/shells/config.properties {}
            sh ~/Documents/opensearch-configs/shells/scp_to_remote.sh ~/Documents/code/ml-commons/plugin/build/distributions/opensearch-ml-{}-SNAPSHOT.zip {}
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./install_ml_plugin.sh
                sh kill_and_restart.sh > /dev/null 2>&1 &
        """.format(public_dns_name, plugin_version, public_dns_name, public_dns_name)
    elif operation == 'installneural':
        command = """
        sh /Users/zaniu/Documents/opensearch-configs/shells/scp_to_remote.sh /Users/zaniu/Documents/opensearch-configs/shells/config.properties {}
        sh /Users/zaniu/Documents/opensearch-configs/shells/scp_to_remote.sh /Users/zaniu/Documents/code/neural-search/build/distributions/opensearch-neural-search-{}-SNAPSHOT.zip {}
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./install_neural_search_plugin.sh
                sh kill_and_restart.sh > /dev/null 2>&1 &
        """.format(public_dns_name, plugin_version, public_dns_name, public_dns_name)
    elif operation == 'reinstallos':
        command = """
        sh /Users/zaniu/Documents/opensearch-configs/shells/scp_to_remote.sh /Users/zaniu/Documents/opensearch-configs/shells/config.properties {}
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./install_opensearch.sh
                sh kill_and_restart.sh > /dev/null 2>&1 &
        """.format(public_dns_name, public_dns_name)
    elif operation == 'restart' or operation == 'start':
        command = """
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                sh kill_and_restart.sh > /dev/null 2>&1 &
        """.format(public_dns_name)
    elif operation == 'updateConfig':
        command = """
            sh /Users/zaniu/Documents/opensearch-configs/shells/scp_to_remote.sh /Users/zaniu/Documents/opensearch-configs/shells/config.properties {}
        """.format(public_dns_name)
    # To run ssh port forwarding in background: https://unix.stackexchange.com/a/685276
    elif operation == 'createSSHTunnel':
        command = """
            pwd
            sh ./restart/stop_9200.sh > /dev/null 2>&1 &
            ssh -i /Users/zaniu/zaniu-ec2-nopass.pem -fN -L 9200:127.0.0.1:9200 ec2-user@{}
        """.format(public_dns_name)

    print("current restart command is: {}".format(command) )
    subprocess.run(command, shell=True)
    # print("res value is:{}".format(res))
    ack = {
        "acknowledge": True
    }
    response = JsonResponse(ack, content_type="application/json", safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response
    
