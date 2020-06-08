#!/usr/bin/env python
from constructs import Construct
from cdk8s import App, Chart

from wmf_cdks.service import Service
from wmf_cdks import helpers, deployment

from wmf_cdks.imports import k8s


class BlubberoidChart(Chart):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        main_app_port = 9090
        # Define services for debugging, tls and plain connection
        labels = helpers.Labels(chart="blubberoid", version="0.1")
        # Deployment data: declare the config volume and the container
        config = deployment.Volume(name="config", data={"policy.yaml": '"foo": "bar"'})
        webapp = deployment.WebAppContainer(
            name=labels.name,
            image="docker-registry.wikimedia.org/blubberoid:1.0",
            cli_args=["--policy", "/etc/blubberoid/policy.yaml"],
            port=main_app_port,
            mounts={"/etc/blubberoid": config},
            check_path="/?spec",
        )

        deployment.BaseDeployment(
            self,
            "blubberoid",
            labels=labels,
            num_replicas=2,
            volumes=[config],
            containers=[webapp],
        )
        Service(
            self, "blubberoid-service", labels=labels, app_port=main_app_port,
        ).synth()
        # TODO: add TLS termination, networkpolicies, etc.


app = App()
BlubberoidChart(app, "blubber")

app.synth()
