import yaml
from kubernetes import client, config

# Load Kubernetes configuration from default location
config.load_kube_config()

# Create ConfigMap for Logstash configuration
logstash_config = {
    'logstash.conf': '''
    input {
        container {
            id => "k8-logs"
            type => "json"
            tags => ["app"]
        }
    }
    filter {
        # Add custom filters here as needed
    }
    output {
        elasticsearch {
            hosts => "http://elasticsearch:9200"
            index => "app-logs-%{+YYYY.MM.dd}"
        }
    }
    '''
}

configmap = client.V1ConfigMap(
    metadata=client.V1ObjectMeta(
        name='logstash-config',
        labels={'app': 'elk'}
    ),
    data=logstash_config
)

core_v1_api = client.CoreV1Api()
core_v1_api.create_namespaced_config_map(namespace='default', body=configmap)

# Create Logstash deployment
logstash_deployment = {
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': 'logstash',
        'labels': {'app': 'elk'}
    },
    'spec': {
        'replicas': 1,
        'selector': {
            'matchLabels': {'app': 'elk', 'tier': 'logstash'}
        },
        'template': {
            'metadata': {
                'labels': {'app': 'elk', 'tier': 'logstash'}
            },
            'spec': {
                'containers': [{
                    'name': 'logstash',
                    'image': 'docker.elastic.co/logstash/logstash:7.12.1',
                    'env': [
                        {'name': 'XPACK_MONITORING_ENABLED', 'value': 'false'}
                    ],
                    'volumeMounts': [{
                        'name': 'config-volume',
                        'mountPath': '/usr/share/logstash/config',
                        'readOnly': True
                    }]
                }],
                'volumes': [{
                    'name': 'config-volume',
                    'configMap': {'name': 'logstash-config'}
                }]
            }
        }
    }
}

apps_v1_api = client.AppsV1Api()
apps_v1_api.create_namespaced_deployment(namespace='default', body=logstash_deployment)

# Create Elasticsearch service
elasticsearch_service = {
    'apiVersion': 'v1',
    'kind': 'Service',
    'metadata': {
        'name': 'elasticsearch',
        'labels': {'app': 'elk'}
    },
    'spec': {
        'ports': [{
            'name': 'http',
            'port': 9200,
            'targetPort': 9200
        }],
        'selector': {'app': 'elasticsearch'}
    }
}

core_v1_api.create_namespaced_service(namespace='default', body=elasticsearch_service)

# Create Elasticsearch deployment
elasticsearch_deployment = {
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': 'elasticsearch',
        'labels': {'app': 'elk'}
    },
    'spec': {
        'replicas': 1,
        'selector': {
            'matchLabels': {'app': 'elk', 'tier': 'elasticsearch'}
        },
        'template': {
            'metadata': {
                'labels': {'app': 'elk', 'tier': 'el
