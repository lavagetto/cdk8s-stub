import attr
from typing import Dict


@attr.s
class Labels:
    # The name of the application. E.g. "eventgate"
    chart = attr.ib()  # type: str
    # The version of the application, e.g. 1.2.0
    version = attr.ib()  # type: str
    # The deployment name. E.g. "main"
    deployment = attr.ib(default="local")  # type: str
    maxlen = attr.ib(default=64)  # type: int
    suffix = attr.ib(default="")  # type: str

    @property
    def name(self) -> str:
        """The name of the resource"""
        return self._out("{chart}-{deployment}{suffix}")

    @property
    def release(self) -> str:
        """The name of the release"""
        return self._out("{chart}-{deployment}")

    @property
    def app_id(self) -> str:
        """The application id"""
        return self._out("{chart}-{version}")

    @property
    def labels(self) -> Dict[str, str]:
        """Standard WMF app labels."""
        return {
            "app": self._out("{chart}"),
            "release": self.name,
            "heritage": "cdk8s",
            "suffix": self.suffix,
        }

    def _out(self, fmt: str) -> str:
        safe_version = self.version.replace("+", "_")
        output = fmt.format(
            chart=self.chart,
            version=safe_version,
            deployment=self.deployment,
            suffix=self.suffix,
        )
        cut = self.maxlen - 1
        return output[0:cut]

    @property
    def labels(self) -> Dict[str, str]:
        """Standard WMF app labels."""
        return {
            "app": self._out("{chart}"),
            "release": self.release,
            "heritage": "cdk8s",
        }
