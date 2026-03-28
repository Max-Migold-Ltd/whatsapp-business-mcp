"""
WhatsApp Analytics Handler for MCP Server.
Handles all WhatsApp analytics and metrics operations.
"""

import os
import aiohttp
import json
from typing import Dict, Any, Optional, List
from .base_handler import BaseWhatsAppHandler


class AnalyticsHandler(BaseWhatsAppHandler):
    """Handler for WhatsApp Analytics operations."""
    
    def __init__(self):
        super().__init__()
        # Validate WABA ID is available for analytics operations
        if not (self.waba_id or self.business_account_id):
            raise ValueError("Either WABA_ID or META_BUSINESS_ACCOUNT_ID environment variable is required for analytics operations")
        
        # Use WABA_ID for analytics operations (fallback to business_account_id)
        waba_for_operations = self.waba_id or self.business_account_id
        self.analytics_url = f"{self.base_url}/{waba_for_operations}"
    
    async def get_analytics(
        self,
        start_time: int,
        end_time: int,
        granularity: str = "DAY",
        phone_numbers: Optional[List[str]] = None,
        country_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get WhatsApp analytics data.
        
        Args:
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            granularity: Granularity of data (DAY, HOUR, MONTH)
            phone_numbers: Optional list of phone numbers to filter by
            country_codes: Optional list of country codes to filter by
            
        Returns:
            dict: Analytics data
        """
        # Build the fields parameter
        fields_parts = [
            f"analytics.start({start_time})",
            f"analytics.end({end_time})",
            f"analytics.granularity({granularity})"
        ]
        
        if phone_numbers:
            fields_parts.append(f"analytics.phone_numbers({json.dumps(phone_numbers)})")
        if country_codes:
            fields_parts.append(f"analytics.country_codes({json.dumps(country_codes)})")
            
        params = {
            "fields": ".".join(fields_parts)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.analytics_url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get analytics")
    
    async def get_conversation_analytics(
        self,
        start_time: int,
        end_time: int,
        granularity: str = "MONTHLY",
        conversation_directions: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get conversation analytics data.
        
        Args:
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            granularity: Granularity of data (DAY, HOUR, MONTHLY)
            conversation_directions: Optional list of conversation directions (business_initiated, user_initiated)
            dimensions: Optional list of dimensions (conversation_type, conversation_direction)
            
        Returns:
            dict: Conversation analytics data
        """
        # Build the fields parameter
        fields_parts = [
            f"conversation_analytics.start({start_time})",
            f"conversation_analytics.end({end_time})",
            f"conversation_analytics.granularity({granularity})"
        ]
        
        if conversation_directions:
            fields_parts.append(f"conversation_analytics.conversation_directions({json.dumps(conversation_directions)})")
        if dimensions:
            fields_parts.append(f"conversation_analytics.dimensions({json.dumps(dimensions)})")
            
        params = {
            "fields": ".".join(fields_parts)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.analytics_url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get conversation analytics")
    
    async def get_quality_rating(
        self,
        phone_number_id: str,
        start_time: int,
        end_time: int
    ) -> Dict[str, Any]:
        """
        Get quality rating for a phone number.
        
        Args:
            phone_number_id: Phone number ID
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            
        Returns:
            dict: Quality rating data
        """
        url = f"{self.base_url}/{phone_number_id}"
        params = {
            "fields": f"quality_rating.start({start_time}),quality_rating.end({end_time})"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get quality rating")
    
    async def get_phone_number_analytics(
        self,
        phone_number_id: str,
        start_time: int,
        end_time: int,
        granularity: str = "DAY"
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific phone number.
        
        Args:
            phone_number_id: Phone number ID
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            granularity: Granularity of data (DAY, HOUR, MONTH)
            
        Returns:
            dict: Phone number analytics data
        """
        url = f"{self.base_url}/{phone_number_id}"
        params = {
            "fields": f"analytics.start({start_time}),analytics.end({end_time}),analytics.granularity({granularity})"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get phone number analytics")
    
    async def get_business_analytics(
        self,
        start_time: int,
        end_time: int,
        granularity: str = "DAY",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get business analytics data.
        
        Args:
            start_time: Start timestamp (Unix timestamp)
            end_time: End timestamp (Unix timestamp)
            granularity: Granularity of data (DAY, HOUR, MONTH)
            metrics: Optional list of metrics to include
            
        Returns:
            dict: Business analytics data
        """
        # Build the fields parameter
        fields_parts = [
            f"business_analytics.start({start_time})",
            f"business_analytics.end({end_time})",
            f"business_analytics.granularity({granularity})"
        ]
        
        if metrics:
            fields_parts.append(f"business_analytics.metrics({json.dumps(metrics)})")
            
        params = {
            "fields": ".".join(fields_parts)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.analytics_url,
                headers=self._prepare_headers(),
                params=params
            ) as response:
                return await self._handle_response(response, "Get business analytics")
    
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