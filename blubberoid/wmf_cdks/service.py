import attr
import copy
from typing import List, Optional

from constructs import Construct
from wmf_cdks.imports import k8s
from wmf_cdks import helpers


@attr.s
class K8sPort:
    port = attr.ib()  # type: int
    target_port = attr.ib()  # type: int
    node_port = attr.ib()  # type: int

    def definition(self, labels: helpers.Labels) -> k8s.ServicePort:
        if self.target_port is not None:
            tp = k8s.IntOrString.from_number(self.target_port)
        else:
            tp = None
        return k8s.ServicePort(
            name=labels.name,
            port=self.port,
            target_port=tp,
            node_port=self.node_port,
            protocol="TCP",
        )


class BaseService(Construct):
    """
    Defines a kubernetes service with all the labels and selectors.
    
    This class should mainly be called from the WMFApp construct, and not be instantiated by itself.
    """

    suffix = ""

    def __init__(
        self, scope: Construct, ns: str, labels: helpers.Labels, ports: List[K8sPort]
    ):
        super().__init__(scope, ns)
        self.labels = copy.deepcopy(labels)
        self.ports = ports
        # Add suffix as appropriate
        self.labels.suffix += self.suffix

        k8s.Service(
            self,
            labels.name,
            metadata=self._meta(),
            spec=k8s.ServiceSpec(
                type="NodePort", selector={"release": labels.name}, ports=self._ports(),
            ),
        )

    def _meta(self) -> k8s.ObjectMeta:
        return k8s.ObjectMeta(labels=self.labels.labels, name=self.labels.name)

    def _ports(self) -> List[k8s.ServicePort]:
        return [port.definition(self.labels) for port in self.ports]


class DebugService(BaseService):
    suffix = "-debug"

    def _ports(self) -> List[k8s.ServicePort]:
        ports = []
        # Ensure we don't define node ports for debug functions
        for port in self.ports:
            port.node_port = None
            ports.append(port.definition(self.labels))
        return ports


class TLSService(BaseService):
    suffix = "-tls-service"


@attr.s(auto_attribs=True)
class Service:
    scope: Construct
    ns: str
    labels: helpers.Labels
    app_port: int = 0
    tls_port: int = 0
    app_public_port: Optional[int] = None
    debug_ports: Optional[List[int]] = None

    def synth(self):
        if self.tls_port != 0:
            tls = K8sPort(self.tls_port, None, self.tls_port)
            TLSService(self.scope, self.ns + "-tls", labels=self.labels, ports=[tls])
        if self.app_port != 0:
            app = K8sPort(self.app_port, self.app_port, self.app_public_port,)
            BaseService(self.scope, self.ns, labels=self.labels, ports=[app])
        if self.debug_ports is not None:
            debug = [K8sPort(port, port, None) for port in self.debug_ports]
            DebugService(
                self.scope, self.ns + "-debug", labels=self.labels, ports=debug
            )
