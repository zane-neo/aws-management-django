from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
import os
import subprocess

def index(request, operation):
    command = ""
    public_dns_name = request.GET.get('public_dns_name', '')
    print("passed into public_dns_name value is: {}".format(public_dns_name))
    if operation == 'stop':
        command = """
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./kill_opensearch.sh
        """.format(public_dns_name)
    elif operation == 'installml':
        plugin_version = parse_plugin_version(public_dns_name)
        print("parsed plugin version is: {}".format(plugin_version))
        if not os.path.exists("/Users/zaniu/Documents/code/ml-commons/plugin/build/distributions/opensearch-ml-{}-SNAPSHOT.zip".format(plugin_version)):
            response = JsonResponse({"error": "plugin version is empty!"}, content_type="application/json", safe=False)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            command = """
                sh /Users/zaniu/Documents/code/shells/scp_to_remote.sh /Users/zaniu/Documents/code/ml-commons/plugin/build/distributions/opensearch-ml-{}-SNAPSHOT.zip {}
                ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                    sh ~/kill_opensearch.sh
                    ./install_ml_plugin.sh
                    sh ~/kill_and_restart.sh > /dev/null 2>&1 &
            """.format(plugin_version, public_dns_name, public_dns_name)
    elif operation == 'installneural':
        plugin_version = parse_plugin_version(public_dns_name)
        if not os.path.exists("/Users/zaniu/Documents/code/neural-search/build/distributions/opensearch-neural-search-{}-SNAPSHOT.zip".format(plugin_version)):
            response = JsonResponse({"error": "plugin version is empty!"}, content_type="application/json", safe=False)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            command = """
            sh /Users/zaniu/Documents/code/shells/scp_to_remote.sh /Users/zaniu/Documents/code/neural-search/build/distributions/opensearch-neural-search-{}-SNAPSHOT.zip {}
                ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                    ./install_neural_search_plugin.sh
                    sh kill_and_restart.sh > /dev/null 2>&1 &
            """.format(plugin_version, public_dns_name, public_dns_name)
    elif operation == 'installOSDashboard':
        command = """
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                ./install_opensearch_dashboard.sh
                sh start_opensearch_dashboard.sh > /dev/null 2>&1 &
        """.format(public_dns_name)
    elif operation == 'reinstallos':
        command = """
        sh /Users/zaniu/Documents/code/shells/scp_to_remote.sh /Users/zaniu/Documents/code/shells/config.properties {}
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
            sh /Users/zaniu/Documents/code/shells/scp_to_remote.sh /Users/zaniu/Documents/code/shells/config.properties {}
        """.format(public_dns_name)
    # To run ssh port forwarding in background: https://unix.stackexchange.com/a/685276
    elif operation == 'createSSHTunnel':
        command = """
            pwd
            sh ./restart/stop_9200.sh > /dev/null 2>&1 &
            ssh -i ~/zaniu-ec2-nopass.pem -fN -L 9200:127.0.0.1:9200 ec2-user@{}
        """.format(public_dns_name)
    elif operation == 'startDashboard':
        command = """
            ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
                sh start_opensearch_dashboard.sh
        """.format(public_dns_name)

    print("current command is: {}".format(command) )
    res = subprocess.run(command, shell=True)
    print("res value is:{}".format(res))
    ack = {
        "acknowledge": True
    }
    response = JsonResponse(ack, content_type="application/json", safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response
    
def parse_plugin_version(public_dns_name):
    fetch_config = """
            rm -rf ./config.properties
            scp -i ~/zaniu-ec2-nopass.pem ec2-user@{}:~/config.properties .
    """.format(public_dns_name)
    subprocess.run(fetch_config, shell=True)
    plugin_version = None
    with open('./config.properties', 'r') as config:
        for line in config:
            if "plugin_version" in line:
                k, v = line.replace('\n', '').split("=")
                plugin_version = v
    return plugin_version