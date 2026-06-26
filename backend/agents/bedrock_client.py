"""
AWS Bedrock Client for Nova Pro model interactions
"""
import boto3
import json
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for AWS Bedrock Nova Pro model"""
    
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
        
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        logger.info(f"Initialized Bedrock client with model: {self.model_id}")
    
    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        top_p: float = 0.9
    ) -> str:
        """
        Invoke Nova Pro model with a prompt
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            top_p: Top-p sampling parameter
            
        Returns:
            Model response text
        """
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        inference_config = {
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p
        }
        
        request_body = {
            "messages": messages,
            "inferenceConfig": inference_config
        }
        
        if system_prompt:
            request_body["system"] = [{"text": system_prompt}]
        
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}] if system_prompt else [],
                inferenceConfig=inference_config
            )
            
            # Extract text from response
            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            
            if content and len(content) > 0:
                return content[0].get("text", "")
            
            return ""
            
        except Exception as e:
            logger.error(f"Bedrock invocation error: {str(e)}")
            raise
    
    def invoke_with_json_output(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Invoke model and parse JSON response
        
        Args:
            prompt: The user prompt (should request JSON output)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens
            temperature: Lower temperature for more deterministic JSON
            
        Returns:
            Parsed JSON dictionary
        """
        json_system_prompt = system_prompt or ""
        json_system_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations outside the JSON."
        
        response = self.invoke(
            prompt=prompt,
            system_prompt=json_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Clean response and parse JSON
        cleaned = response.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw response: {response[:500]}")
            # Return error structure
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response[:1000]
            }
    
    def analyze_document(
        self,
        document_content: str,
        document_type: str,
        extraction_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a document and extract structured information
        
        Args:
            document_content: The text content of the document
            document_type: Type of document (pay_stub, tax_return, etc.)
            extraction_schema: Expected fields to extract
            
        Returns:
            Extracted document data
        """
        system_prompt = f"""You are a document analysis expert specializing in financial documents.
Your task is to extract information from a {document_type} document.
Be precise and accurate. If a field cannot be determined, use null.
Respond with valid JSON matching the extraction schema."""
        
        prompt = f"""Analyze this {document_type} document and extract the following fields:

Schema: {json.dumps(extraction_schema, indent=2)}

Document Content:
{document_content}

Extract all relevant information and respond with JSON."""
        
        return self.invoke_with_json_output(prompt, system_prompt)
    
    def assess_risk(
        self,
        context: str,
        risk_factors: List[str],
        assessment_criteria: str
    ) -> Dict[str, Any]:
        """
        Perform risk assessment based on provided context
        
        Args:
            context: The context/data to assess
            risk_factors: List of risk factors to consider
            assessment_criteria: Criteria for assessment
            
        Returns:
            Risk assessment results
        """
        system_prompt = """You are an expert credit risk analyst with deep knowledge of 
underwriting principles, regulatory compliance (FCRA, ECOA), and financial analysis.
Provide thorough, accurate risk assessments based on the data provided.
Always explain your reasoning and cite specific data points."""
        
        prompt = f"""Perform a risk assessment based on the following:

CONTEXT:
{context}

RISK FACTORS TO CONSIDER:
{json.dumps(risk_factors, indent=2)}

ASSESSMENT CRITERIA:
{assessment_criteria}

Provide your assessment in JSON format with:
- risk_level: "low", "medium", "high", or "critical"
- risk_score: 0-100
- key_findings: list of important observations
- recommendations: list of recommendations
- reasoning: detailed explanation of your assessment"""
        
        return self.invoke_with_json_output(prompt, system_prompt)


# Singleton instance
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """Get or create singleton Bedrock client"""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
