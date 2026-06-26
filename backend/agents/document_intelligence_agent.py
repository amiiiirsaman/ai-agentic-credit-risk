"""
Document Intelligence Agent - OCR and document verification
"""
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class DocumentIntelligenceAgent(BaseAgent):
    """
    Document Intelligence Agent
    
    Responsibilities:
    - Process and verify uploaded documents
    - Extract key information using OCR (simulated for synthetic data)
    - Detect potential document fraud
    - Cross-reference extracted data with application
    """
    
    def __init__(self):
        super().__init__(
            name="DocumentIntelligence",
            description="Document processing, verification, and fraud detection"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and verify application documents"""
        
        documents = application_data.get("documents", [])
        
        # Generate synthetic document verification results
        verification_results = await self._verify_documents(application_data, documents)
        
        # Cross-reference with application data
        cross_reference_results = self._cross_reference_data(application_data, verification_results)
        
        # Calculate overall verification status
        overall_verified = all(doc.get("verified", False) for doc in verification_results)
        overall_confidence = sum(doc.get("confidence", 0) for doc in verification_results) / max(len(verification_results), 1)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(application_data, verification_results, cross_reference_results) or {}
        
        return {
            "documents_verified": overall_verified,
            "verification_confidence": round(overall_confidence, 4),
            "document_results": verification_results,
            "cross_reference_status": cross_reference_results,
            "fraud_indicators": llm_analysis.get("fraud_indicators", []) if llm_analysis else [],
            "fraud_risk_score": llm_analysis.get("fraud_risk_score", 0) if llm_analysis else 0,
            "data_consistency_score": cross_reference_results.get("consistency_score", 0.95),
            "extracted_data_summary": llm_analysis.get("extracted_data_summary", {}) if llm_analysis else {},
            "confidence": overall_confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    async def _verify_documents(self, application_data: Dict[str, Any], documents: List[Dict]) -> List[Dict]:
        """Verify each document (synthetic verification for demo)"""
        
        # If no documents provided, create synthetic verification for expected documents
        if not documents:
            documents = [
                {"document_type": "pay_stub", "filename": "pay_stub.pdf"},
                {"document_type": "bank_statement", "filename": "bank_statement.pdf"},
                {"document_type": "id_document", "filename": "drivers_license.pdf"},
            ]
        
        results = []
        
        for doc in documents:
            doc_type = doc.get("document_type", "unknown")
            
            # Simulate extraction based on document type
            extracted_data = self._simulate_extraction(application_data, doc_type)
            
            # Dynamic confidence based on document type and extraction quality
            verification_confidence = self._calculate_doc_confidence(doc_type, extracted_data)
            
            results.append({
                "document_id": doc.get("id", f"doc_{len(results)}"),
                "document_type": doc_type,
                "filename": doc.get("filename", "unknown"),
                "verified": verification_confidence > 0.75,
                "confidence": round(verification_confidence, 4),
                "extracted_data": extracted_data,
                "fraud_indicators": [],
                "processing_notes": f"Document processed successfully with {verification_confidence:.0%} confidence"
            })
        
        return results
    
    def _calculate_doc_confidence(self, doc_type: str, extracted_data: Dict) -> float:
        """Calculate confidence based on document type and extraction completeness"""
        # Base confidence by document type (some are easier to verify)
        type_confidence = {
            "id_document": 0.92,    # IDs are straightforward
            "pay_stub": 0.87,       # Pay stubs vary in format
            "bank_statement": 0.85, # Bank statements can be complex
            "tax_return": 0.90,     # Tax returns are standardized
            "unknown": 0.65
        }.get(doc_type, 0.75)
        
        # Extraction completeness bonus
        if extracted_data:
            non_null_fields = sum(1 for v in extracted_data.values() if v is not None and v != "")
            total_fields = len(extracted_data)
            completeness_bonus = (non_null_fields / max(total_fields, 1)) * 0.10
        else:
            completeness_bonus = 0
        
        # Add slight randomness to avoid all same values
        import random
        variance = random.uniform(-0.05, 0.05)
        
        confidence = type_confidence + completeness_bonus + variance
        return max(0.60, min(0.98, confidence))
    
    def _simulate_extraction(self, application_data: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """Simulate document data extraction"""
        
        applicant = application_data.get("applicant", {})
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        
        if doc_type == "pay_stub":
            return {
                "employer_name": employment.get("employer_name", "Unknown Employer"),
                "employee_name": applicant.get("name", "Unknown"),
                "pay_period": "Bi-weekly",
                "gross_pay": round(employment.get("annual_income", 0) / 26, 2),
                "net_pay": round(employment.get("annual_income", 0) / 26 * 0.72, 2),
                "ytd_gross": round(employment.get("annual_income", 0) * 0.75, 2),
            }
        
        elif doc_type == "bank_statement":
            return {
                "account_holder": applicant.get("name", "Unknown"),
                "account_type": "Checking",
                "ending_balance": financial.get("checking_balance", 0),
                "average_balance": financial.get("checking_balance", 0) * 0.9,
                "total_deposits": round(employment.get("annual_income", 0) / 12, 2),
            }
        
        elif doc_type == "id_document":
            return {
                "full_name": applicant.get("name", "Unknown"),
                "document_type": "Driver's License",
                "is_valid": True,
                "is_expired": False,
            }
        
        elif doc_type == "tax_return":
            return {
                "filing_status": "Single",
                "total_income": employment.get("annual_income", 0),
                "adjusted_gross_income": round(employment.get("annual_income", 0) * 0.95, 2),
            }
        
        return {"document_type": doc_type, "status": "processed"}
    
    def _cross_reference_data(self, application_data: Dict[str, Any], verification_results: List[Dict]) -> Dict[str, Any]:
        """Cross-reference extracted document data with application"""
        
        mismatches = []
        matches = []
        
        applicant = application_data.get("applicant", {})
        employment = application_data.get("employment", {})
        
        for result in verification_results:
            extracted = result.get("extracted_data", {})
            doc_type = result.get("document_type", "")
            
            # Check name consistency
            if "employee_name" in extracted or "full_name" in extracted or "account_holder" in extracted:
                doc_name = extracted.get("employee_name") or extracted.get("full_name") or extracted.get("account_holder")
                if doc_name and applicant.get("name"):
                    if doc_name.lower() == applicant.get("name", "").lower():
                        matches.append(f"Name matches on {doc_type}")
                    else:
                        mismatches.append(f"Name mismatch on {doc_type}: '{doc_name}' vs '{applicant.get('name')}'")
            
            # Check employer consistency
            if "employer_name" in extracted:
                if extracted["employer_name"] == employment.get("employer_name"):
                    matches.append(f"Employer matches on {doc_type}")
                else:
                    mismatches.append(f"Employer mismatch on {doc_type}")
            
            # Check income consistency (within 10% tolerance)
            if "gross_pay" in extracted:
                expected_pay = employment.get("annual_income", 0) / 26
                actual_pay = extracted["gross_pay"]
                if abs(actual_pay - expected_pay) / max(expected_pay, 1) < 0.10:
                    matches.append(f"Income matches on {doc_type}")
                else:
                    mismatches.append(f"Income discrepancy on {doc_type}")
        
        consistency_score = len(matches) / max(len(matches) + len(mismatches), 1)
        
        return {
            "matches": matches,
            "mismatches": mismatches,
            "consistency_score": round(consistency_score, 4),
            "all_consistent": len(mismatches) == 0
        }
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        verification_results: List[Dict],
        cross_reference_results: Dict
    ) -> Dict[str, Any]:
        """Get LLM analysis for document verification"""
        
        system_prompt = """You are a document verification specialist with expertise in 
detecting fraudulent documents and verifying applicant information.
Analyze the document verification results and provide insights."""
        
        prompt = f"""Analyze these document verification results:

Application Data:
- Applicant: {application_data.get('applicant', {}).get('name')}
- Claimed Income: ${application_data.get('employment', {}).get('annual_income', 0):,.2f}
- Employer: {application_data.get('employment', {}).get('employer_name')}

Document Verification Results:
{json.dumps(verification_results, indent=2, default=str)}

Cross-Reference Results:
{json.dumps(cross_reference_results, indent=2)}

Provide analysis in JSON format:
{{
    "fraud_indicators": ["list any potential fraud red flags"],
    "fraud_risk_score": 0-100 (0 = no fraud risk, 100 = definite fraud),
    "extracted_data_summary": {{"key extracted data points"}},
    "verification_notes": "summary of verification status",
    "reasoning": "detailed explanation of document analysis"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
