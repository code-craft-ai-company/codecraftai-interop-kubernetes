"""
    .. module:: kubeconfigloader
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`KubeConfigLoader`, the helper that resolves a
        kubeconfig from a path, an in-memory dict, or an in-cluster
        service-account context into a :class:`KubernetesRestClient`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Dict, List, Optional

from ccai.errors.exceptions import SemanticError

from ccai.restclient.kubernetes.kubeconfigresolver import (
    KubeConfigResolver
)
from ccai.restclient.kubernetes.kubernetesrestclient import (
    KubernetesRestClient
)


class KubeConfigLoader:
    """
        Resolves a kubeconfig source into a
        :class:`ccai.restclient.kubernetes.kubernetesrestclient.KubernetesRestClient`.

        Exactly one of ``kubeconfig_path``, ``kubeconfig_dict`` or
        ``in_cluster`` must be supplied. The loader keeps the resolved
        in-memory dict (when one was supplied) so callers may later switch
        contexts without re-reading the source.

        :ivar kubeconfig_path: The path the kubeconfig was loaded from, or
            ``None``.
        :ivar kubeconfig_dict: The in-memory kubeconfig dict, or ``None``.
        :ivar in_cluster: ``True`` when the in-cluster context is in use.
        :ivar context: The active context name, or ``None`` for in-cluster.
    """

    def __init__(
        self,
        *,
        kubeconfig_path: Optional[str] = None,
        kubeconfig_dict: Optional[Dict[str, object]] = None,
        in_cluster: bool = False,
        context: Optional[str] = None,
    ) -> None:
        """
            Initialise a :class:`KubeConfigLoader`.

            :param kubeconfig_path: Filesystem path of a kubeconfig file.
            :param kubeconfig_dict: An in-memory kubeconfig dict.
            :param in_cluster: When ``True`` use the in-cluster
                service-account context.
            :param context: The named context to activate. Ignored when
                ``in_cluster`` is ``True``.

            :returns: ``None``
            :raises: SemanticError
        """
        sources_supplied = []

        if kubeconfig_path is not None:
            sources_supplied.append("kubeconfig_path")

        if kubeconfig_dict is not None:
            sources_supplied.append("kubeconfig_dict")

        if in_cluster is True:
            sources_supplied.append("in_cluster")

        if len(sources_supplied) == 0:
            err_msg_lines = [
                "A kubeconfig source must be supplied.",
                "Provide exactly one of 'kubeconfig_path', "
                "'kubeconfig_dict' or 'in_cluster=True'.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg) from None

        if len(sources_supplied) > 1:
            err_msg_lines = [
                "Only one kubeconfig source may be supplied.",
                "SUPPLIED: ({})".format(len(sources_supplied)),
            ]
            for source_name in sources_supplied:
                err_msg_lines.append("    {}".format(source_name))

            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg) from None

        self.kubeconfig_path = kubeconfig_path
        self.kubeconfig_dict = kubeconfig_dict
        self.in_cluster = in_cluster
        self.context = context
        return

    def available_contexts(self) -> List[str]:
        """
            Enumerate the context names available in the resolved kubeconfig.

            :returns: The list of context names. An in-cluster loader yields
                an empty list because in-cluster operation has no contexts.
        """
        context_names: List[str] = []

        if self.in_cluster is True:
            return context_names

        config_dict = self.kubeconfig_dict

        if config_dict is None and self.kubeconfig_path is not None:
            import yaml

            with open(self.kubeconfig_path, "r") as config_handle:
                config_dict = yaml.safe_load(config_handle)

        if config_dict is None:
            return context_names

        contexts = config_dict.get("contexts", None)

        if contexts is None:
            return context_names

        for context_entry in contexts:
            entry_name = context_entry.get("name", None)
            if entry_name is not None:
                context_names.append(entry_name)

        return context_names

    def build_api_client(self) -> object:
        """
            Resolve the kubeconfig source and build a configured
            :class:`KubernetesRestClient`.

            The name is retained from when this returned an SDK
            ``ApiClient``; the returned object now carries the api groups
            directly (``core_v1``, ``apps_v1``, ``batch_v1``,
            ``networking_v1``, ``version``).

            :returns: A configured :class:`KubernetesRestClient`.
        """
        resolver = KubeConfigResolver(
            kubeconfig_path=self.kubeconfig_path,
            kubeconfig_dict=self.kubeconfig_dict,
            in_cluster=self.in_cluster,
            context=self.context,
        )
        resolution = resolver.resolve()
        api_client = KubernetesRestClient(resolution=resolution)
        return api_client


__all__ = ["KubeConfigLoader"]
