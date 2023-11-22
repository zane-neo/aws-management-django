from django.shortcuts import render
import json
from django.http import JsonResponse
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

ml_commons_base_path = "/Users/zaniu/Documents/code/ml-commons/plugin/build/distributions"
neural_search_base_path = "/Users/zaniu/Documents/code/neural-search/build/distributions"

@csrf_exempt
def index(request, plugin_type):
    request_body = json.loads(request.body.decode('utf-8'))
    public_ips = request_body['publicIps']
    file_path = request_body['filePath']
    print("file path is: {}".format(file_path))
    if file_path is None or public_ips is None or plugin_type is None:
        return failure_response("file path is empty or public ips empty or plugin type is empty")
    else:
        failures = []
        thread_pool = create_thread_pool_executor(len(public_ips))
        futures_maps = []
        for public_ip in public_ips:
            if plugin_type == 'ml':
                _file_path = ml_commons_base_path + "/" + file_path
            elif plugin_type == 'neuralsearch':
                _file_path = neural_search_base_path + "/" + file_path
            future = thread_pool.submit(send_install_restart, public_ip, _file_path, plugin_type)
            futures_maps.append({"public_ip": public_ip, "future": future})
        for item in futures_maps:
            i_public_ip = item['public_ip']
            i_future = item['future']
            success = i_future.result()
            if not success:
                failures.append(i_public_ip)
        thread_pool.shutdown()
        return success_response(failures)

@csrf_exempt
def fetch_selectible_files(request, plugin_name):
    # request_body = json.loads(request.body.decode('utf-8'))
    # plugin_name = request_body['pluginName']
    
    files = None
    if (plugin_name == 'ml' and os.path.exists(ml_commons_base_path)):
        files = os.listdir(ml_commons_base_path)
    elif (plugin_name == 'neuralsearch' and os.path.exists(neural_search_base_path)):
        files = os.listdir(neural_search_base_path)
    else:
        return failure_response("file path parameter is not correct or base path not exist")
    
    res = list(filter(lambda x: 'zip' in x, files))
    return success_response({"files": res})

def send_install_restart(public_ip, file_path, plugin_type):
    print("entered send install and restart method, public ip is: {}, file path is:{}".format(public_ip, file_path))
    script_names = {
        "ml": "install_ml_plugin.sh",
        "neuralsearch": "install_neural_search_plugin.sh"
    }
    script_name = script_names.get(plugin_type, "")
    
    scp_command = """
        scp -i ~/zaniu-ec2-nopass.pem {} ec2-user@{}:~/
        ssh -i ~/zaniu-ec2-nopass.pem ec2-user@{} << EOF
            sh ~/kill_opensearch.sh
            ./{}
            nohup sh ~/kill_and_restart.sh > nohup.log 2&>1 &
    """.format(file_path, public_ip, public_ip, script_name)
    res = subprocess.run(scp_command, shell=True)
    if res.returncode != 0:
        return False
    else:
        return True


def failure_response(error_msg):
    response = JsonResponse({"error": error_msg}, content_type = 'application/json', safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response

def success_response(res):
    response = JsonResponse(res, content_type = 'application/json', safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    return response

def create_thread_pool_executor(size: 1):
    return ThreadPoolExecutor(size)
