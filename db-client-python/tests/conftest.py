"""Shared test fixtures: a real gRPC server on an ephemeral loopback port.

The counterpart of ``client-java``'s ``InProcessServer`` helper, with one difference worth stating:
grpc-python has no in-process transport, so this binds ``127.0.0.1:0`` instead. Still no external
service, no fixed port and nothing to clean up between tests - but it is a real socket, so a test
that hangs blocks on the network rather than deadlocking in-process.

The point is the same either way: tests run against a genuine server and genuine ``grpc.RpcError``s,
so the request the client built and the failure it mapped are observed as the wire carries them
rather than as a mock reports them.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from concurrent import futures
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import grpc
import pytest
from google.protobuf import any_pb2
from google.rpc import code_pb2, error_details_pb2, status_pb2
from grpc_status import rpc_status

from cyrock_db._proto import cyrock_db_cdc_pb2 as cdc_pb2
from cyrock_db._proto import cyrock_db_cdc_pb2_grpc as cdc_grpc
from cyrock_db._proto import cyrock_db_data_pb2 as data_pb2
from cyrock_db._proto import cyrock_db_data_pb2_grpc as data_grpc
from cyrock_db._proto import cyrock_db_graph_pb2 as graph_pb2
from cyrock_db._proto import cyrock_db_graph_pb2_grpc as graph_grpc
from cyrock_db._proto import cyrock_db_nlsearch_pb2 as nlsearch_pb2
from cyrock_db._proto import cyrock_db_nlsearch_pb2_grpc as nlsearch_grpc
from cyrock_db._proto import cyrock_db_platform_pb2 as platform_pb2
from cyrock_db._proto import cyrock_db_platform_pb2_grpc as platform_grpc
from cyrock_db._values_codec import to_struct


@dataclass
class RecordingTokenService(platform_grpc.TokenGrpcServiceServicer):
    """A ``TokenGrpcService`` that records what it was sent and answers however a test asks.

    ``Exchange`` is the subject for transport-level tests because it is the simplest unary call in
    the schema: ``Empty`` in, one message out.
    """

    token:                    str                    = "test-token"
    expires_in:               int                    = 3600
    fail_with:                grpc.StatusCode | None  = None
    fail_detail:              str                     = "the server said no"
    attach_durability_reason: bool                   = False
    # A failure carrying an arbitrary ErrorInfo reason, for the credential-mistake dispatch (issue #464).
    abort_reason:             str | None             = None
    abort_code:               grpc.StatusCode        = grpc.StatusCode.UNAUTHENTICATED
    abort_domain:             str                    = "cyrock.ai"
    requests:                 list[Any]              = field(default_factory=list)
    metadata:                 list[tuple[str, str]]  = field(default_factory=list)

    def Exchange(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        self.metadata.extend(context.invocation_metadata())

        if self.attach_durability_reason:
            packed = any_pb2.Any()
            packed.Pack(error_details_pb2.ErrorInfo(domain="cyrock.ai", reason="DURABILITY_NOT_CONFIRMED"))
            context.abort_with_status(rpc_status.to_status(
                status_pb2.Status(code=code_pb2.ABORTED, message=self.fail_detail, details=[packed])
            ))

        if self.abort_reason is not None:
            packed = any_pb2.Any()
            packed.Pack(error_details_pb2.ErrorInfo(domain=self.abort_domain, reason=self.abort_reason))
            context.abort_with_status(rpc_status.to_status(
                status_pb2.Status(code=self.abort_code.value[0], message=self.fail_detail, details=[packed])
            ))

        if self.fail_with is not None:
            context.abort(self.fail_with, self.fail_detail)

        return platform_pb2.TokenExchangeResponse(token=self.token, expires_in=self.expires_in)


@dataclass
class RecordingCollectionService(platform_grpc.CollectionDefinitionGrpcServiceServicer):
    """A ``CollectionDefinitionGrpcService`` recording its requests and answering from a fixture."""

    collections: list[Any]                = field(default_factory=list)
    requests:    list[Any]                = field(default_factory=list)
    metadata:    list[tuple[str, str]]    = field(default_factory=list)
    fail_with:   grpc.StatusCode | None   = None
    fail_detail: str                      = "the server said no"
    delay_seconds: float                  = 0.0

    def _record(self, request: Any, context: grpc.ServicerContext) -> None:
        self.requests.append(request)
        self.metadata.extend(context.invocation_metadata())
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.fail_with is not None:
            context.abort(self.fail_with, self.fail_detail)

    def Create(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        created = platform_pb2.CollectionDefinitionProto(
            id="generated-id",
            name=request.name,
            vector_fields=request.vector_fields,
            metadata_fields=request.metadata_fields,
        )
        self.collections.append(created)
        return created

    def ListAll(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return platform_pb2.CollectionDefinitionList(collections=self.collections)

    def ListForProject(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return platform_pb2.CollectionDefinitionList(collections=self.collections)

    def Delete(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        for index, existing in enumerate(self.collections):
            if existing.id == request.collection_id:
                return self.collections.pop(index)
        context.abort(grpc.StatusCode.NOT_FOUND, f"Collection not found: {request.collection_id}")

    def Update(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        for existing in self.collections:
            if existing.id == request.id:
                existing.name = request.name
                return existing
        context.abort(grpc.StatusCode.NOT_FOUND, f"Collection not found: {request.id}")


@dataclass
class RecordingDocumentService(data_grpc.DocumentGrpcServiceServicer):
    """A ``DocumentGrpcService`` backed by a dict, faithful enough to test the client against.

    Not a mock: it stores what the client sent and returns it, so a request the client encodes wrongly
    shows up as a wrong value coming back rather than as a passing assertion about a call.
    """

    documents:     dict[int, Any]         = field(default_factory=dict)
    by_key:        dict[str, int]         = field(default_factory=dict)
    requests:      list[Any]              = field(default_factory=list)
    metadata:      list[tuple[str, str]]  = field(default_factory=list)
    fail_with:     grpc.StatusCode | None = None
    fail_detail:   str                    = "the server said no"
    delay_seconds: float                  = 0.0
    next_id:       int                    = 100

    def _record(self, request: Any, context: grpc.ServicerContext) -> None:
        self.requests.append(request)
        self.metadata.extend(context.invocation_metadata())
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.fail_with is not None:
            context.abort(self.fail_with, self.fail_detail)

    def _store(self, request: Any, document_id: int) -> Any:
        stored = data_pb2.DocumentProto(id=document_id, vectors=dict(request.vectors))
        if request.HasField("metadata"):
            stored.metadata.CopyFrom(request.metadata)
        if request.HasField("external_key") and request.external_key:
            stored.external_key = request.external_key
            self.by_key[request.external_key] = document_id
        self.documents[document_id] = stored
        return stored

    def _assign(self, request: Any) -> int:
        # Any negative id means "assign me one"; 0 is a real id. Mirrors the server.
        if request.HasField("id") and request.id >= 0:
            return int(request.id)
        assigned = self.next_id
        self.next_id += 1
        return assigned

    def Upsert(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return data_pb2.UpsertDocumentResponse(id=self._store(request, self._assign(request)).id)

    def UpsertBatch(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return data_pb2.UpsertDocumentsBatchResponse(
            ids=[self._store(each, self._assign(each)).id for each in request.documents]
        )

    def GetById(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        stored = self.documents.get(request.document_id if request.HasField("document_id") else -1)
        if stored is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Document not found: {request.document_id}")
        return stored

    def List(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        ordered = [self.documents[key] for key in sorted(self.documents)]
        limit   = request.limit if request.HasField("limit") else len(ordered)
        return data_pb2.DocumentList(documents=ordered[request.offset : request.offset + limit])

    def Delete(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        stored = self.documents.pop(request.document_id if request.HasField("document_id") else -1, None)
        if stored is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Document not found: {request.document_id}")
        return stored

    # Search returns everything stored, scored by position. Ranking is the server's job and is not
    # what these tests are about; what matters is that the request arrived encoded correctly and the
    # response decodes into Match objects.
    def Search(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return self._matches(request.max_results if request.HasField("max_results") else 10)

    def MultiSearch(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return self._matches(request.max_results if request.HasField("max_results") else 10)

    def HybridSearch(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return self._matches(request.max_results if request.HasField("max_results") else 10)

    def _matches(self, limit: int) -> Any:
        ordered = [self.documents[key] for key in sorted(self.documents)][:max(limit, 0)]
        return data_pb2.SearchDocumentsResponse(
            matches=[
                data_pb2.MatchProto(score=1.0 - (index / 100.0), document=document)
                for index, document in enumerate(ordered)
            ]
        )

    def ExecuteTransaction(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return data_pb2.ExecuteDocumentTransactionResponse(
            results=[
                data_pb2.DocumentOperationResultProto(index=index, generated_id=index + 500)
                for index, _ in enumerate(request.operations)
            ]
        )

    def ExecuteStatement(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return data_pb2.CollectionStatementResponse(
            statement_class="READ_QUERY", statement_type="MATCH", columns=["d"],
            rows=[data_pb2.CollectionQueryRow(values=to_struct({"d": 2}))],
        )

    def UpsertByKey(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        existing = self.by_key.get(request.external_key)
        created  = existing is None
        if existing is None:
            existing = self.next_id
            self.next_id += 1
        keyed = data_pb2.UpsertDocumentRequest(
            collection_id=request.collection_id,
            id=existing,
            vectors=dict(request.vectors),
            external_key=request.external_key,
        )
        if request.HasField("metadata"):
            keyed.metadata.CopyFrom(request.metadata)
        self._store(keyed, existing)
        return data_pb2.UpsertByKeyResponse(id=existing, created=created)

    def GetByKey(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        document_id = self.by_key.get(request.external_key)
        if document_id is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"No document for key: {request.external_key}")
        return self.documents[document_id]

    def RemoveByKey(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        document_id = self.by_key.pop(request.external_key, None)
        if document_id is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"No document for key: {request.external_key}")
        return self.documents.pop(document_id)


@dataclass
class RecordingGraphService(graph_grpc.GraphGrpcServiceServicer):
    """A ``GraphGrpcService`` backed by dicts. Stores what it is sent and hands it back."""

    nodes:         dict[int, Any]         = field(default_factory=dict)
    edges:         dict[int, Any]         = field(default_factory=dict)
    by_key:        dict[str, int]         = field(default_factory=dict)
    requests:      list[Any]              = field(default_factory=list)
    fail_with:     grpc.StatusCode | None = None
    fail_detail:   str                    = "the server said no"
    next_node:     int                    = 1
    detected:      bool                   = False
    summaries:     dict[Any, Any]         = field(default_factory=dict)
    next_edge:     int                    = 1

    def _record(self, request: Any, context: grpc.ServicerContext) -> None:
        self.requests.append(request)
        if self.fail_with is not None:
            context.abort(self.fail_with, self.fail_detail)

    def AddNode(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node_id = self.next_node
        self.next_node += 1
        node = graph_pb2.NodeProto(
            id=node_id, labels=list(request.labels), vectors=dict(request.vectors), created_at=1
        )
        if request.HasField("metadata"):
            node.metadata.CopyFrom(request.metadata)
        self.nodes[node_id] = node
        return graph_pb2.AddNodeResponse(node_id=node_id)

    def AddEdge(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        edge_id = self.next_edge
        self.next_edge += 1
        edge = graph_pb2.EdgeProto(
            id=edge_id, type=request.type, source_id=request.source_id,
            target_id=request.target_id, weight=request.weight, created_at=1,
        )
        if request.HasField("metadata"):
            edge.metadata.CopyFrom(request.metadata)
        self.edges[edge_id] = edge
        return graph_pb2.AddEdgeResponse(edge_id=edge_id)

    def GetNode(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node = self.nodes.get(request.node_id)
        if node is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Node not found: {request.node_id}")
        return graph_pb2.GetNodeResponse(node=node)

    def GetNodeByKey(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node_id = self.by_key.get(request.external_key)
        if node_id is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"No node for key: {request.external_key}")
        return graph_pb2.GetNodeResponse(node=self.nodes[node_id])

    def GetEdge(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        edge = self.edges.get(request.edge_id)
        if edge is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Edge not found: {request.edge_id}")
        return graph_pb2.GetEdgeResponse(edge=edge)

    def RemoveNode(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.nodes.pop(request.node_id, None)
        return graph_pb2.GraphEmpty()

    def RemoveNodeByKey(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node_id = self.by_key.pop(request.external_key, None)
        if node_id is not None:
            self.nodes.pop(node_id, None)
        return graph_pb2.GraphEmpty()

    def RemoveEdge(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.edges.pop(request.edge_id, None)
        return graph_pb2.GraphEmpty()

    def UpdateVector(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node = self.nodes[request.node_id]
        node.vectors[request.field_name].CopyFrom(
            graph_pb2.GraphVectorFieldProto(values=list(request.vector))
        )
        return graph_pb2.GraphEmpty()

    def UpdateWeight(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.edges[request.edge_id].weight = request.weight
        return graph_pb2.GraphEmpty()

    def UpdateNodeMetadata(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.nodes[request.node_id].metadata.CopyFrom(request.metadata)
        return graph_pb2.GraphEmpty()

    def UpdateEdgeMetadata(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.edges[request.edge_id].metadata.CopyFrom(request.metadata)
        return graph_pb2.GraphEmpty()

    def ListNodes(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        ordered = [self.nodes[key] for key in sorted(self.nodes)]
        limit   = request.limit if request.HasField("limit") else len(ordered)
        page    = ordered[request.offset : request.offset + limit]
        return graph_pb2.ListNodesResponse(nodes=[self._project(n, request.include_vectors) for n in page])

    def GetNodes(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        # Duplicates collapse and unknown ids are left out, as the real server does.
        wanted = list(dict.fromkeys(request.node_ids))
        found  = [self.nodes[each] for each in wanted if each in self.nodes]
        return graph_pb2.GetNodesResponse(
            nodes=[self._project(n, request.include_vectors) for n in found]
        )

    def InducedSubgraph(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        wanted = set(request.node_ids)
        nodes  = [self.nodes[each] for each in sorted(wanted & self.nodes.keys())]
        edges  = [
            edge for edge in self.edges.values()
            if edge.source_id in wanted and edge.target_id in wanted
        ]
        return graph_pb2.InducedSubgraphResponse(
            nodes=[self._project(n, request.include_vectors) for n in nodes], edges=edges
        )

    def UpsertNode(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        existing = self.by_key.get(request.external_key) if request.external_key else None
        if request.HasField("node_id"):
            existing = request.node_id
        created = existing is None or existing not in self.nodes
        if existing is None:
            existing = self.next_node
            self.next_node += 1
        node = graph_pb2.NodeProto(
            id=existing, labels=list(request.labels), vectors=dict(request.vectors), created_at=1
        )
        if request.external_key:
            node.external_key = request.external_key
            self.by_key[request.external_key] = existing
        if request.HasField("metadata"):
            node.metadata.CopyFrom(request.metadata)
        self.nodes[existing] = node
        return graph_pb2.UpsertNodeResponse(node_id=existing, created=created)

    # The read paths return everything stored. Ranking, expansion and pathfinding are the server's
    # business; what these fixtures verify is that the request encoded correctly and the response
    # decodes into the right domain type.
    def SearchSimilar(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        ordered = [self.nodes[key] for key in sorted(self.nodes)]
        limit   = request.max_results if request.HasField("max_results") else len(ordered)
        return graph_pb2.SearchSimilarResponse(
            matches=[
                graph_pb2.NodeMatchProto(score=1.0 - index / 100.0, node=node)
                for index, node in enumerate(ordered[: max(limit, 0)])
            ]
        )

    def Neighbors(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.NeighborsResponse(
            nodes=[self._project(n, request.include_vectors) for n in self._all()],
            edges=list(self.edges.values()),
        )

    def Traverse(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.TraverseResponse(nodes=self._all())

    def ContextWindow(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.ContextWindowResponse(nodes=self._all(), edges=list(self.edges.values()))

    def Recall(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.RecallResponse(nodes=self._all(), edges=list(self.edges.values()))

    def ReasoningChain(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.ReasoningChainResponse(nodes=self._all(), edges=list(self.edges.values()))

    def ExecuteTransaction(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.ExecuteTransactionResponse(
            results=[
                graph_pb2.OperationResultProto(index=index, generated_id=index + 1000)
                for index, _ in enumerate(request.operations)
            ]
        )

    def ExecuteStatement(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.StatementResponse(
            statement_class="READ_QUERY", statement_type="MATCH", columns=["n"],
            rows=[graph_pb2.GraphQueryRow(values=to_struct({"n": 1}))],
        )

    # ─── Communities, memory ────────────────────────────────────────────

    def DetectCommunities(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        self.detected = True
        return self._hierarchy(include_members=True)

    def GetCommunities(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return self._hierarchy(include_members=request.include_members)

    def _hierarchy(self, include_members: bool) -> Any:
        members = [1, 2] if include_members else []
        return graph_pb2.DetectCommunitiesResponse(
            communities=[
                graph_pb2.CommunityProto(id=7, level=0, parent_id=0, size=2, member_node_ids=members)
            ],
            levels=1, algorithm="leiden", detected_at=99,
        )

    def PutCommunitySummaries(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        for entry in request.summaries:
            self.summaries[(entry.level, entry.community_id)] = entry
        return graph_pb2.PutCommunitySummariesResponse(
            ids=[200 + index for index, _ in enumerate(request.summaries)]
        )

    def GetCommunitySummaries(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        stored = list(self.summaries.values())
        limit  = request.limit or len(stored)
        return graph_pb2.GetCommunitySummariesResponse(
            summaries=[
                graph_pb2.CommunitySummaryEntryProto(
                    level=e.level, community_id=e.community_id, summary_text=e.summary_text
                )
                for e in stored[:limit]
            ],
            truncated=len(stored) > limit,
        )

    def GetCommunityMembers(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        limit = request.limit or 2
        return graph_pb2.GetCommunityMembersResponse(
            communities=[
                graph_pb2.CommunityMembersProto(
                    level=request.level, community_id=cid,
                    member_node_ids=[1, 2][:limit], truncated=limit < 2,
                )
                for cid in (request.community_ids or [7])
            ]
        )

    def GetCommunityAssignments(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.GetCommunityAssignmentsResponse(
            assignments=[
                graph_pb2.CommunityAssignmentProto(node_id=n, community_id=7) for n in request.node_ids
            ],
            levels=1,
        )

    def GlobalSearch(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.GlobalSearchResponse(
            results=[
                graph_pb2.GlobalSearchResultProto(
                    community_id=7, level=request.level, score=0.9, summary_text="theme",
                    parent_community_id=0,
                    member_node_ids=[1, 2] if request.include_members else [],
                )
            ]
        )

    def RefreshCommunities(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.RefreshCommunitiesResponse(
            hierarchy=self._hierarchy(include_members=False), pruned_summaries=3,
            stale_communities=[graph_pb2.CommunityRefProto(level=0, community_id=9)],
        )

    def CommunityStatus(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.CommunityStatusResponse(
            detected=self.detected, detected_at=99, stale=False, levels=1,
            community_count=1, summary_count=len(self.summaries),
        )

    def Observe(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        node_id = self.next_node
        self.next_node += 1
        self.nodes[node_id] = graph_pb2.NodeProto(
            id=node_id, labels=list(request.labels), vectors=dict(request.vectors), created_at=1
        )
        return graph_pb2.ObserveResponse(node_id=node_id, linked_ids=[501, 502])

    def EntityLink(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.EntityLinkResponse(
            edges=[graph_pb2.EdgeProto(id=9, type="SIMILAR", source_id=request.node_id,
                                       target_id=2, weight=0.95, created_at=1)]
        )

    def Decay(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self._record(request, context)
        return graph_pb2.DecayResponse(pruned_nodes=2, pruned_edges=3)

    def _all(self) -> list[Any]:
        return [self.nodes[key] for key in sorted(self.nodes)]

    @staticmethod
    def _project(node: Any, include_vectors: bool) -> Any:
        """Drops the vectors unless the caller asked for them, as the server does."""
        if include_vectors:
            return node
        stripped = graph_pb2.NodeProto()
        stripped.CopyFrom(node)
        stripped.ClearField("vectors")
        return stripped


@dataclass
class RecordingGraphDefinitionService(platform_grpc.GraphDefinitionGrpcServiceServicer):
    """A ``GraphDefinitionGrpcService`` over a list, enough for definition CRUD."""

    graphs:   list[Any] = field(default_factory=list)
    requests: list[Any] = field(default_factory=list)

    def Create(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        created = platform_pb2.GraphDefinitionProto(
            id=f"graph-{len(self.graphs)}",
            name=request.name,
            node_vector_fields=request.node_vector_fields,
            node_metadata_fields=request.node_metadata_fields,
            edge_metadata_fields=request.edge_metadata_fields,
            enable_temporal_tracking=request.enable_temporal_tracking,
            auto_link_threshold=request.auto_link_threshold,
        )
        self.graphs.append(created)
        return created

    def ListAll(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return platform_pb2.GraphDefinitionList(graphs=self.graphs)

    def ExecuteStatement(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return platform_pb2.ProjectStatementResponse(
            statement_class="PROJECT_SCOPED_DDL", statement_type="SHOW_GRAPHS", columns=["name"]
        )

    def ListForProject(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return platform_pb2.GraphDefinitionList(graphs=self.graphs)

    def Delete(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        for index, existing in enumerate(self.graphs):
            if existing.id == request.graph_id:
                return self.graphs.pop(index)
        context.abort(grpc.StatusCode.NOT_FOUND, f"Graph not found: {request.graph_id}")

    def Fork(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        branch = platform_pb2.GraphDefinitionProto(
            id=f"branch-{len(self.graphs)}", name=request.branch_name,
            parent_graph_id=request.graph_id, branch_name=request.branch_name, forked_at=42,
        )
        self.graphs.append(branch)
        return branch

    def Merge(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return platform_pb2.MergeGraphResponse(
            nodes_added=2, nodes_removed=1, nodes_updated=3,
            edges_added=4, edges_removed=0, edges_updated=1,
        )

    def ListBranches(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return platform_pb2.GraphDefinitionList(
            graphs=[g for g in self.graphs if g.parent_graph_id == request.graph_id]
        )


@dataclass
class RecordingNlSearchService(nlsearch_grpc.NlSearchGrpcServiceServicer):
    """An ``NlSearchGrpcService`` that echoes the query back as a translated one."""

    requests: list[Any] = field(default_factory=list)

    def SearchCollection(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return self._response(request.query)

    def SearchGraph(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        return self._response(request.query)

    @staticmethod
    def _response(query: str) -> Any:
        return nlsearch_pb2.NlSearchResponseProto(
            matches=[nlsearch_pb2.NlSearchMatchProto(id=1, score=0.8, metadata=to_struct({"t": "x"}))],
            translated_query=f"translated:{query}", query_type="SEMANTIC",
        )


@dataclass
class RecordingChangeStreamService(cdc_grpc.ChangeStreamGrpcServiceServicer):
    """A ``ChangeStreamGrpcService`` that plays scripted batches, one per connection.

    ``batches`` is a list of per-connection scripts: the first connection gets ``batches[0]``, a
    reconnect gets ``batches[1]``, and so on; the last is repeated once exhausted. An entry may be a
    list of events to send, or a ``grpc.StatusCode`` to fail with - which is how a reconnect is
    provoked without any timing.
    """

    batches:     list[Any]              = field(default_factory=list)
    requests:    list[Any]              = field(default_factory=list)
    connections: int                    = 0

    def WatchChanges(self, request: Any, context: grpc.ServicerContext) -> Any:  # noqa: N802
        self.requests.append(request)
        index = min(self.connections, len(self.batches) - 1) if self.batches else 0
        self.connections += 1
        script = self.batches[index] if self.batches else []

        if isinstance(script, grpc.StatusCode):
            context.abort(script, "scripted failure")
        yield from script


CREDENTIAL_CONTRACT = (
    Path(__file__).resolve().parents[2] / "proto" / "src" / "main" / "resources" / "credential-by-service.tsv"
)


def load_credential_contract() -> dict[str, str]:
    """The credential-per-service contract as ``{service: credential}``, empty when it is not beside us.

    An empty map turns :class:`CredentialEnforcingInterceptor` into a pass-through, so a published copy of
    the tests with no reactor beside it does not fail to start a server - the tests that need enforcement
    skip themselves instead (see ``test_auth.py``).
    """
    if not CREDENTIAL_CONTRACT.is_file():
        return {}
    rows = {}
    for line in CREDENTIAL_CONTRACT.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        credential, service = stripped.split("\t", 1)
        rows[service] = credential
    return rows


class CredentialEnforcingInterceptor(grpc.ServerInterceptor):
    """A server interceptor that refuses the wrong credential for a service, per the shared contract.

    The counterpart of ``client-java``'s ``CredentialEnforcingInterceptor``. A test server that accepts any
    credential lets an auth test assert the wrong behaviour and pass (issue #464); installed here, this makes
    the split real - a definition or token service wants ``x-api-key``, the data services want the exchanged
    bearer token - and refuses the other with the same machine-readable ErrorInfo reason the real server
    attaches. A service the contract does not name passes through untouched.
    """

    def __init__(self, contract: dict[str, str]) -> None:
        self._contract = contract

    def intercept_service(self, continuation: Any, handler_call_details: Any) -> Any:
        service  = handler_call_details.method.rsplit("/", 1)[0].lstrip("/")
        expected = self._contract.get(service)
        original = continuation(handler_call_details)
        if expected is None or original is None:
            return original

        metadata     = dict(handler_call_details.invocation_metadata or ())
        has_api_key  = bool(metadata.get("x-api-key"))
        has_bearer   = str(metadata.get("authorization", "")).startswith("Bearer ")
        if (has_api_key if expected == "API_KEY" else has_bearer):
            return original

        reason = "API_KEY_REQUIRED" if expected == "API_KEY" else "BEARER_TOKEN_REQUIRED"

        def _abort(context: grpc.ServicerContext) -> None:
            packed = any_pb2.Any()
            packed.Pack(error_details_pb2.ErrorInfo(domain="cyrock.ai", reason=reason))
            context.abort_with_status(rpc_status.to_status(status_pb2.Status(
                code=code_pb2.UNAUTHENTICATED, message="wrong credential for this service", details=[packed]
            )))

        def unary(request: Any, context: grpc.ServicerContext) -> Any:
            _abort(context)

        def stream(request: Any, context: grpc.ServicerContext) -> Any:
            _abort(context)
            yield  # unreachable - _abort raises - but makes this a generator, a valid streaming handler

        # Match the arity of the handler being guarded, so a streaming method is refused as a streaming one.
        if original.response_streaming and original.request_streaming:
            return grpc.stream_stream_rpc_method_handler(stream)
        if original.response_streaming:
            return grpc.unary_stream_rpc_method_handler(stream)
        if original.request_streaming:
            return grpc.stream_unary_rpc_method_handler(unary)
        return grpc.unary_unary_rpc_method_handler(unary)


@dataclass
class RunningServer:
    """A running server, the channel that reaches it, and the service recording what arrives."""

    server:  grpc.Server
    channel: grpc.Channel
    service: RecordingTokenService
    port:    int = 0
    collections: RecordingCollectionService | None = None
    docs:        RecordingDocumentService | None   = None
    graph:       RecordingGraphService | None      = None
    graph_defs:  RecordingGraphDefinitionService | None = None
    nl:          RecordingNlSearchService | None      = None
    cdc:         RecordingChangeStreamService | None  = None

    def token_stub(self) -> Any:
        return platform_grpc.TokenGrpcServiceStub(self.channel)


@pytest.fixture
def token_server() -> Iterator[Callable[..., RunningServer]]:
    """Starts a ``TokenGrpcService``, configured per test, and tears it down afterwards."""
    started: list[RunningServer] = []

    def start(**kwargs: Any) -> RunningServer:
        cdc_kwargs        = kwargs.pop("cdc", None)
        collection_kwargs = kwargs.pop("collections", None)
        document_kwargs   = kwargs.pop("docs", None)
        graph_kwargs      = kwargs.pop("graph", None)
        service     = RecordingTokenService(**kwargs)
        collections = RecordingCollectionService(**(collection_kwargs or {}))
        docs        = RecordingDocumentService(**(document_kwargs or {}))
        graph       = RecordingGraphService(**(graph_kwargs or {}))
        graph_defs  = RecordingGraphDefinitionService()
        nl          = RecordingNlSearchService()
        cdc         = RecordingChangeStreamService(**(cdc_kwargs or {}))
        server      = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
        platform_grpc.add_TokenGrpcServiceServicer_to_server(service, server)
        platform_grpc.add_CollectionDefinitionGrpcServiceServicer_to_server(collections, server)
        data_grpc.add_DocumentGrpcServiceServicer_to_server(docs, server)
        graph_grpc.add_GraphGrpcServiceServicer_to_server(graph, server)
        platform_grpc.add_GraphDefinitionGrpcServiceServicer_to_server(graph_defs, server)
        nlsearch_grpc.add_NlSearchGrpcServiceServicer_to_server(nl, server)
        cdc_grpc.add_ChangeStreamGrpcServiceServicer_to_server(cdc, server)
        port = server.add_insecure_port("127.0.0.1:0")
        server.start()
        running = RunningServer(
            server=server,
            channel=grpc.insecure_channel(f"127.0.0.1:{port}"),
            service=service,
            port=port,
            collections=collections,
            docs=docs,
            graph=graph,
            graph_defs=graph_defs,
            nl=nl,
            cdc=cdc,
        )
        started.append(running)
        return running

    yield start

    for running in started:
        running.channel.close()
        running.server.stop(grace=None)


@pytest.fixture
def enforcing_server() -> Iterator[Callable[[], RunningServer]]:
    """A server that refuses the wrong credential per service, for the credential-split tests (issue #464)."""
    started: list[RunningServer] = []

    def start() -> RunningServer:
        interceptor = CredentialEnforcingInterceptor(load_credential_contract())
        service     = RecordingTokenService()
        collections = RecordingCollectionService()
        docs        = RecordingDocumentService()
        server      = grpc.server(futures.ThreadPoolExecutor(max_workers=8), interceptors=[interceptor])
        platform_grpc.add_TokenGrpcServiceServicer_to_server(service, server)
        platform_grpc.add_CollectionDefinitionGrpcServiceServicer_to_server(collections, server)
        data_grpc.add_DocumentGrpcServiceServicer_to_server(docs, server)
        port = server.add_insecure_port("127.0.0.1:0")
        server.start()
        running = RunningServer(
            server=server,
            channel=grpc.insecure_channel(f"127.0.0.1:{port}"),
            service=service,
            port=port,
            collections=collections,
            docs=docs,
        )
        started.append(running)
        return running

    yield start

    for running in started:
        running.channel.close()
        running.server.stop(grace=None)


def change_event(
    lsn:               int,
    op:                str  = "CREATE",
    entity_id:         int  = 1,
    snapshot_complete: bool = False,
    labels:            tuple[str, ...] = (),
) -> Any:
    """Builds a ``ChangeEvent`` for a scripted batch."""
    event = cdc_pb2.ChangeEvent(
        source=cdc_pb2.ChangeSource(resource_kind="GRAPH", resource_id="graph-1", lsn=lsn, ts_ms=1),
        snapshot_complete=snapshot_complete,
    )
    if not snapshot_complete:
        event.op = cdc_pb2.ChangeOp.Value(op)
        event.entity_kind = cdc_pb2.EntityKind.NODE
        event.entity_id = entity_id
        event.labels.extend(labels)
    return event
