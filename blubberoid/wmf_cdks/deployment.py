# A typical deployment will include various sidecars and configmaps.
# Here we define a base deployment construct which includes:
# - TLS termination sidecar (optional)
# - Main pod
# - Monitoring sidecar
# As for service, the main class is not a construct per se, but rather a composition of such things.
import attr
from typing import Dict, List, Optional

from constructs import Construct

from wmf_cdks import helpers
from wmf_cdks.imports import k8s


@attr.s(auto_attribs=True)
class Volume:
    """Abstraction to define a volume

    We only support configmap volumes for now.
    You will need to refer to the volume by name in the container
    configuration
    """

    name: str
    data: Dict[str, str]

    @property
    def config_map_name(self) -> str:
        return "{}-config".format(self.name)

    @property
    def pod_volume(self) -> k8s.Volume:
        return k8s.Volume(
            name=self.name,
            config_map=k8s.ConfigMapVolumeSource(name=self.config_map_name),
        )

    def synth(self, scope: Construct) -> k8s.ConfigMap:
        """generate the config map"""
        return k8s.ConfigMap(scope, name=self.config_map_name, data=self.data)


class VolumeFromFile(Volume):
    def __init__(self, name: str, source: str, target: str):
        data = {target: self._read(source)}
        super().__init__(name, data)

    def synth(self, scope: Construct) -> k8s.ConfigMap:
        return k8s.ConfigMap(scope, name=self.config_map_name, binary_data=data)


class BaseDeployment(Construct):
    def __init__(
        self,
        scope: Construct,
        ns: str,
        containers: List[k8s.Container],
        labels: helpers.Labels,
        num_replicas: int,
        volumes: Optional[List[Volume]] = None,
    ):
        super().__init__(scope, ns)
        self.scope = scope
        self.labels = labels
        self.volumes = volumes
        self.containers = containers
        k8s.Deployment(
            self.scope,
            "deployment",
            metadata=self._meta(),
            spec=k8s.DeploymentSpec(
                replicas=num_replicas,
                selector=self._selector(),
                template=k8s.PodTemplateSpec(
                    metadata=k8s.ObjectMeta(
                        labels=self.labels.labels, annotations=self._annotations()
                    ),
                    spec=self._spec(),
                ),
            ),
        )

    def _meta(self) -> k8s.ObjectMeta:
        """Basic metadata for the object"""
        return k8s.ObjectMeta(name=self.labels.name, labels=self.labels.labels)

    def _selector(self) -> k8s.LabelSelector:
        return k8s.LabelSelector(match_labels=self.labels.labels)

    def _annotations(self) -> Optional[Dict]:
        """Annotations support needs to be added by subclasses."""
        return

    def _affinity(self) -> Optional[k8s.Affinity]:
        """Affinity should be added by the subclasses."""
        return

    def _volumes(self) -> Optional[List[k8s.Volume]]:
        """This should mostly demand work to the volume abstraction."""
        if self.volumes is not None:
            return [v.synth(self) for v in self.volumes]
        return

    def _spec(self) -> k8s.PodSpec:
        """Builds the full pod spec."""
        return k8s.PodSpec(
            containers=self.containers,
            volumes=self._volumes(),
            affinity=self._affinity(),
        )


def WebAppContainer(
    *,
    name: str,
    image: str,
    port: int,
    cli_args: Optional[List[str]] = None,
    mounts=Optional[Dict[str, Volume]],
    check_path: str
):
    my_probes = probes(port, check_path)
    volumemounts = [
        k8s.VolumeMount(mount_path=path, name=v.name) for path, v in mounts.items()
    ]
    return k8s.Container(
        name=name,
        args=cli_args,
        image_pull_policy="IfNotPresent",
        image=image,
        liveness_probe=my_probes["liveness"],
        readiness_probe=my_probes["readiness"],
        ports=[k8s.ContainerPort(container_port=port)],
        volume_mounts=volumemounts,
    )


def probes(port: int, url: str) -> Dict[str, k8s.Probe]:
    """Get a simple definition of a liveness and readiness probe for an HTTP service on a port"""
    return {
        "liveness": k8s.Probe(
            tcp_socket=k8s.TcpSocketAction(port=k8s.IntOrString.from_number(port))
        ),
        "readiness": k8s.Probe(
            http_get=k8s.HttpGetAction(
                port=k8s.IntOrString.from_number(port), path=url
            ),
        ),
    }
