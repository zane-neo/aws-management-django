"""aws_management_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from my_app import views as my_app_view
from restart import views as restart_view
from instance_manager import views as instance_manager_view
from opensearch import views as opensearch_view
from install_plugins import views as install_plugins_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', my_app_view.index, name="homepage"),
    path('application/<str:operation>', restart_view.index, name= "application"),
    path('instance/<str:action>', instance_manager_view.index, name="instance_manager"),
    path('cluster_node_status/_cat/nodes', opensearch_view.index, name='opensearch_cluster_nodes_status'),
    path('node_creation/<str:creation_type>', opensearch_view.index1, name='node_creation'),
    path('install_plugin/<str:plugin_type>', install_plugins_view.index, name='install_plugin_index'),
    path('install_plugin_file_list/<str:plugin_name>', install_plugins_view.fetch_selectible_files, name='install_plugin_fetch_files')
]
