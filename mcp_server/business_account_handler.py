"""
WhatsApp Business Account Handler for MCP Server.
Handles all WhatsApp Business Account (WABA) management operations.
"""

import os
import aiohttp
import json
from typing import Dict, Any, Optional, List
from .base_handler import BaseWhatsAppHandler


class BusinessAccountHandler(BaseWhatsAppHandler):
    """Handler for WhatsApp Business Account operations."""
    
    def __init__(self):
        super().__init__()
        # For business account operations, we need the business portfolio ID
        self.business_portfolio_id = os.getenv("META_BUSINESS_PORTFOLIO_ID")
        if not self.business_portfolio_id:
            raise ValueError("META_BUSINESS_PORTFOLIO_ID environment variable is required for business account operations")
        
        # Business portfolio base URL
        self.business_portfolio_url = f"{self.base_url}/{self.business_portfolio_id}"
    
    async def get_owned_wabas(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get all owned WABAs for the business portfolio.
        
        Args:
            limit: Maximum number of WABAs to return
            
        Returns:
            dict: List of owned WABAs
        """
        url = f"{self.business_portfolio_url}/owned_whatsapp_business_accounts"
        params = {"limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get owned WABAs")
    
    async def get_shared_wabas(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get all shared WABAs for the business portfolio.
        
        Args:
            limit: Maximum number of WABAs to return
            
        Returns:
            dict: List of shared WABAs
        """
        url = f"{self.business_portfolio_url}/shared_whatsapp_business_accounts"
        params = {"limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get shared WABAs")
    
    async def get_waba_details(self, waba_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific WABA.
        
        Args:
            waba_id: ID of the WABA
            
        Returns:
            dict: WABA details
        """
        url = f"{self.base_url}/{waba_id}"
        params = {
            "fields": "id,name,currency,timezone_id,message_template_namespace,account_review_status,account_type,owner_business_info,owner_business,primary_funding_id,owner"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get WABA details")
    
    async def create_waba(
        self,
        name: str,
        currency: str,
        timezone_id: str,
        message_template_namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new WABA.
        
        Args:
            name: Name of the WABA
            currency: Currency code (e.g., USD, EUR)
            timezone_id: Timezone ID (e.g., 1 for UTC)
            message_template_namespace: Optional namespace for message templates
            
        Returns:
            dict: Created WABA information
        """
        url = f"{self.business_portfolio_url}/owned_whatsapp_business_accounts"
        payload = {
            "name": name,
            "currency": currency,
            "timezone_id": timezone_id
        }
        
        if message_template_namespace:
            payload["message_template_namespace"] = message_template_namespace
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Create WABA")
    
    async def update_waba(
        self,
        waba_id: str,
        name: Optional[str] = None,
        currency: Optional[str] = None,
        timezone_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a WABA.
        
        Args:
            waba_id: ID of the WABA to update
            name: New name (optional)
            currency: New currency (optional)
            timezone_id: New timezone ID (optional)
            
        Returns:
            dict: Update response
        """
        url = f"{self.base_url}/{waba_id}"
        payload = {}
        
        if name:
            payload["name"] = name
        if currency:
            payload["currency"] = currency
        if timezone_id:
            payload["timezone_id"] = timezone_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Update WABA")
    
    async def delete_waba(self, waba_id: str) -> Dict[str, Any]:
        """
        Delete a WABA.
        
        Args:
            waba_id: ID of the WABA to delete
            
        Returns:
            dict: Delete response
        """
        url = f"{self.base_url}/{waba_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                url,
                headers=self._prepare_headers()
            ) as response:
                return await self._handle_response(response, "Delete WABA")
    
    async def migrate_account(
        self,
        source_waba_id: str,
        target_waba_id: str,
        phone_numbers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Migrate account data from one WABA to another.
        
        Args:
            source_waba_id: Source WABA ID
            target_waba_id: Target WABA ID
            phone_numbers: Optional list of phone numbers to migrate
            
        Returns:
            dict: Migration response
        """
        url = f"{self.base_url}/{source_waba_id}/migrate"
        payload = {
            "target_waba_id": target_waba_id
        }
        
        if phone_numbers:
            payload["phone_numbers"] = phone_numbers
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                return await self._handle_response(response, "Migrate account")
    
    async def get_waba_insights(
        self,
        waba_id: str,
        start_time: int,
        end_time: int,
        granularity: str = "DAY"
    ) -> Dict[str, Any]:
        """
        Get insights for a WABA.
        
        Args:
            waba_id: ID of the WABA
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            granularity: Granularity of data (DAY, HOUR, MONTH)
            
        Returns:
            dict: WABA insights data
        """
        url = f"{self.base_url}/{waba_id}"
        params = {
            "fields": f"insights.start({start_time}),insights.end({end_time}),insights.granularity({granularity})"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get WABA insights")
    
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