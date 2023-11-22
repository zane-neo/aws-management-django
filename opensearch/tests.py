from django.test import TestCase
import re
import os
import subprocess

# Create your tests here.


def replace_with_a_new_file():
    with open('~/Documents/code/shells/opensearch.yml', 'r') as file:
        cluster_ips = "ip-172-31-37-163.ap-northeast-1.compute.internal,ip-172-31-43-28.ap-northeast-1.compute.internal,ip-172-31-35-31.ap-northeast-1.compute.internal,ip-172-31-47-50.ap-northeast-1.compute.internal,ip-172-31-32-210.ap-northeast-1.compute.internal,ip-172-31-34-115.ap-northeast-1.compute.internal,ip-172-31-40-6.ap-northeast-1.compute.internal,ip-172-31-40-120.ap-northeast-1.compute.internal,ip-172-31-41-121.ap-northeast-1.compute.internal,ip-172-31-36-169.ap-northeast-1.compute.internal,ip-172-31-46-234.ap-northeast-1.compute.internal"
        ips_str = ''
        for ip in cluster_ips.split(','):
            ips_str += '"' + ip + '",'
        ips_str = '[' + ips_str.removesuffix(',') + ']'
        with open('~/Documents/code/shells/opensearch.yml.temp', 'a') as temp:
            for line in file:
                if 'discovery.seed_hosts' in line:
                    print(ips_str)
                    temp.write("discovery.seed_hosts: " + ips_str + "\n")
                else:
                    temp.write(line)

def replace_inplace():
    with open('~/Documents/code/shells/opensearch.yml', 'r') as file:
        content = file.read()

    cluster_ips = "ip-172-31-37-163.ap-northeast-1.compute.internal,ip-172-31-43-28.ap-northeast-1.compute.internal,ip-172-31-35-31.ap-northeast-1.compute.internal,ip-172-31-47-50.ap-northeast-1.compute.internal,ip-172-31-32-210.ap-northeast-1.compute.internal,ip-172-31-34-115.ap-northeast-1.compute.internal,ip-172-31-40-6.ap-northeast-1.compute.internal,ip-172-31-40-120.ap-northeast-1.compute.internal,ip-172-31-41-121.ap-northeast-1.compute.internal,ip-172-31-36-169.ap-northeast-1.compute.internal,ip-172-31-46-234.ap-northeast-1.compute.internal"
    ips_str = ''
    for ip in cluster_ips.split(','):
        ips_str += '"' + ip + '",'
    ips_str = '[' + ips_str.removesuffix(',') + ']'
    # content.replace('/discovery.seed_hosts:.*/g', "discovery.seed_hosts:" + ips_str)
    content = re.sub(r"^discovery.seed_hosts:\s.*$", ips_str, content)
    with open('~/Documents/code/shells/opensearch.yml', 'w') as temp:
       temp.write(content)

    print(content)

def check_file():
    res = os.path.exists("~/Documents/code/ml-commons/plugin/build/distributions/opensearch-ml-2.4.1.0-SNAPSHOT.zip")
    print(res)

def check_shell_result():
    res = subprocess.run("ls -a", shell=True)
    print(res.returncode)

check_shell_result()