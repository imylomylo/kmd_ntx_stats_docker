#!/usr/bin/env python3
from kmd_ntx_api.serializers import *
from django.contrib.auth.models import User, Group
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, \
                                          NumberFilter
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework import permissions, viewsets, authentication
from kmd_ntx_api.filters import *
from kmd_ntx_api.serializers import *
from kmd_ntx_api.models import *
from kmd_ntx_api.lib_query import * 
from kmd_ntx_api.base_58 import get_addr_from_pubkey

# Tool views
class api_decode_op_return_tool(viewsets.ViewSet):
    """
    Decodes notarization OP_RETURN strings.
    USAGE: decode_opret/?OP_RETURN=<OP_RETURN>
    """    
    serializer_class = decodeOpRetSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, validated_data):
        return Task(id=None, **validated_data)

    def get(self, request, format=None):
        """
        Returns decoded notarisation information from OP_RETURN strings
        """
        if 'OP_RETURN' in request.GET:

            decoded = decode_opret(request.GET['OP_RETURN'])
        else:
            decoded = {}
        return Response(decoded)

class api_address_from_pubkey_tool(viewsets.ViewSet):
    serializer_class = addrFromPubkeySerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, validated_data):
        return Task(id=None, **validated_data)

    def get(self, request, format=None):
        """
        Returns address from pubkey using CONST base 58 params
        """
        chain = "KMD"
        if "chain" in request.GET:
            if request.GET["chain"] in COIN_PARAMS:
                chain = request.GET["chain"]

        if "pubkey" in request.GET:
            pubkey = request.GET["pubkey"]
            resp = {
                "chain": chain,
                "pubkey": pubkey,
                "address": get_addr_from_pubkey(chain, pubkey)
            }

        else:
            resp ={
                "Error": "You need to specify a pubkey and coin like '?coin=KMD&pubkey=<YOUR_PUBKEY>' If coin not specified or unknown, will revert to KMD"
            }
        return Response(resp)

class api_addr_from_base58_tool(viewsets.ViewSet):
    serializer_class = addrFromPubkeySerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, validated_data):
        return Task(id=None, **validated_data)

    def get(self, request, format=None):
        """
        Returns address from pubkey using INPUT base 58 params
        """
        missing_params = []
        for x in addrFromBase58Serializer.Meta.fields:
            if x not in request.GET:
                missing_params.append(f"{x}=<{x}>")

        if len(missing_params) > 0:
            params = '&'.join(missing_params)
            error = f"You need to specify params like '?{params}'"
            return Response({"error":f"Missing params: {error}"})

        resp = get_addr_tool(request.GET["pubkey"], request.GET["pub_addr"],
                             request.GET["script_addr"], request.GET["secret_key"])
        return Response(resp)
