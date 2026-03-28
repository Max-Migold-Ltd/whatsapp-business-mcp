"""
WhatsApp Flow Handler for MCP Server.
Handles all WhatsApp Flow operations for interactive experiences.
"""

import os
import aiohttp
import json
from typing import Dict, Any, Optional, List
from .base_handler import BaseWhatsAppHandler


class FlowHandler(BaseWhatsAppHandler):
    """Handler for WhatsApp Flow operations."""
    
    def __init__(self):
        super().__init__()
        # Validate WABA ID is available for flow operations
        if not (self.waba_id or self.business_account_id):
            raise ValueError("Either WABA_ID or META_BUSINESS_ACCOUNT_ID environment variable is required for flow operations")
        
        # Use WABA_ID for flow operations (fallback to business_account_id)
        waba_for_operations = self.waba_id or self.business_account_id
        self.flows_url = f"{self.base_url}/{waba_for_operations}/flows"
    
    async def create_flow(
        self,
        name: str,
        categories: List[str],
        clone_flow_id: Optional[str] = None,
        endpoint_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new WhatsApp Flow.
        
        Args:
            name: Name of the flow
            categories: List of flow categories
            clone_flow_id: Optional ID of flow to clone from
            endpoint_uri: Optional endpoint URI for the flow
            
        Returns:
            dict: Created flow information
        """
        payload = {
            "name": name,
            "categories": categories
        }
        
        if clone_flow_id:
            payload["clone_flow_id"] = clone_flow_id
        if endpoint_uri:
            payload["endpoint_uri"] = endpoint_uri
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.flows_url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Create flow")
    
    async def list_flows(self, limit: int = 100) -> Dict[str, Any]:
        """
        List all flows for the WABA.
        
        Args:
            limit: Maximum number of flows to return
            
        Returns:
            dict: List of flows
        """
        params = {"limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.flows_url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "List flows")
    
    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Get details of a specific flow.
        
        Args:
            flow_id: ID of the flow
            
        Returns:
            dict: Flow details
        """
        url = f"{self.flows_url}/{flow_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers()
            ) as response:
                return await self._handle_response(response, "Get flow")
    
    async def update_flow(
        self,
        flow_id: str,
        name: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update a flow.
        
        Args:
            flow_id: ID of the flow to update
            name: New name (optional)
            categories: New categories (optional)
            
        Returns:
            dict: Update response
        """
        url = f"{self.flows_url}/{flow_id}"
        payload = {}
        
        if name:
            payload["name"] = name
        if categories:
            payload["categories"] = categories
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Update flow")
    
    async def publish_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Publish a flow.
        
        Args:
            flow_id: ID of the flow to publish
            
        Returns:
            dict: Publish response
        """
        url = f"{self.flows_url}/{flow_id}/publish"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers()
            ) as response:
                return await self._handle_response(response, "Publish flow")
    
    async def upload_flow_json(self, flow_id: str, flow_json_content: str) -> Dict[str, Any]:
        """
        Upload flow JSON content.
        
        Args:
            flow_id: ID of the flow
            flow_json_content: JSON content of the flow
            
        Returns:
            dict: Upload response
        """
        url = f"{self.flows_url}/{flow_id}/flow_json"
        payload = {
            "flow_json": flow_json_content
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Upload flow JSON")
    
    async def get_flow_preview(self, flow_id: str, invalidate: bool = False) -> Dict[str, Any]:
        """
        Get flow preview.
        
        Args:
            flow_id: ID of the flow
            invalidate: Whether to invalidate cache
            
        Returns:
            dict: Flow preview
        """
        url = f"{self.flows_url}/{flow_id}/preview"
        params = {}
        
        if invalidate:
            params["invalidate"] = "true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get flow preview")
    
    async def migrate_flows(
        self,
        source_waba_id: str,
        source_flow_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Migrate flows from one WABA to another.
        
        Args:
            source_waba_id: Source WABA ID
            source_flow_names: Optional list of flow names to migrate
            
        Returns:
            dict: Migration response
        """
        url = f"{self.flows_url}/migrate"
        payload = {
            "source_waba_id": source_waba_id
        }
        
        if source_flow_names:
            payload["source_flow_names"] = source_flow_names
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Migrate flows")
    
    async def get_flow_metrics(
        self,
        flow_id: str,
        metric_name: str = "ENDPOINT_REQUEST_COUNT",
        granularity: str = "DAY",
        since: str = None,
        until: str = None
    ) -> Dict[str, Any]:
        """
        Get metrics for a flow.
        
        Args:
            flow_id: ID of the flow
            metric_name: Name of the metric
            granularity: Granularity of data (DAY, HOUR, MONTH)
            since: Start date (optional)
            until: End date (optional)
            
        Returns:
            dict: Flow metrics data
        """
        url = f"{self.flows_url}/{flow_id}/metrics"
        params = {
            "metric_name": metric_name,
            "granularity": granularity
        }
        
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get flow metrics")
    
    async def _handle_response(self, response, operation_name: str) -> Dict[str, Any]:
        """Handle API response"""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    "status": "success",
                    "data": data,
                    "operation": operation_name
                }
            else:
                error_data = await response.json()
                return {
                    "status": "error",
                    "error": error_data.get("error", {}).get("message", f"Failed to {operation_name}"),
                    "operation": operation_name,
                    "status_code": response.status
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "operation": operation_name
            } 