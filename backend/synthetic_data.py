"""
Synthetic data generator for Credit Risk Assessment Platform
Generates realistic test data for applications
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid


class SyntheticDataGenerator:
    """Generates realistic synthetic data for loan applications"""
    
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
    ]
    
    EMPLOYERS = [
        "Tech Solutions Inc", "Global Finance Corp", "Healthcare Systems LLC",
        "Manufacturing Partners", "Retail Excellence Group", "Energy Dynamics",
        "Education First Foundation", "Transportation Services Co", "Media & Entertainment Inc",
        "Construction Innovations", "Legal Associates LLP", "Consulting Partners Group",
        "Software Dynamics Corp", "Data Analytics Inc", "Cloud Services LLC"
    ]
    
    JOB_TITLES = [
        "Software Engineer", "Financial Analyst", "Project Manager", "Marketing Director",
        "Sales Representative", "Operations Manager", "Data Scientist", "Product Manager",
        "Human Resources Manager", "Accountant", "Business Analyst", "UX Designer",
        "Quality Assurance Engineer", "Customer Success Manager", "Technical Lead"
    ]
    
    LOAN_PURPOSES = [
        "home_purchase", "refinance", "debt_consolidation", 
        "business", "personal", "auto", "education"
    ]
    
    @classmethod
    def generate_application(cls, risk_profile: str = "random") -> Dict[str, Any]:
        """
        Generate a complete synthetic loan application
        
        Args:
            risk_profile: "low_risk", "medium_risk", "high_risk", or "random"
        """
        if risk_profile == "random":
            risk_profile = random.choice(["low_risk", "medium_risk", "high_risk"])
        
        # Base profiles for different risk levels
        profiles = {
            "low_risk": {
                "credit_score_range": (750, 850),
                "income_range": (120000, 500000),
                "dti_range": (0.10, 0.25),
                "years_employed_range": (5, 30),
                "delinquencies": 0,
                "utilization_range": (5, 20),
            },
            "medium_risk": {
                "credit_score_range": (640, 720),
                "income_range": (50000, 120000),
                "dti_range": (0.30, 0.43),
                "years_employed_range": (2, 8),
                "delinquencies": random.choice([0, 1, 1]),
                "utilization_range": (30, 55),
            },
            "high_risk": {
                # Truly high risk profile - should result in DENY or high-risk CONDITIONAL
                "credit_score_range": (300, 580),  # Below fair credit threshold
                "income_range": (20000, 45000),    # Low income
                "dti_range": (0.50, 0.75),         # Very high DTI
                "years_employed_range": (0, 2),    # Job instability
                "delinquencies": random.randint(2, 6),  # Multiple delinquencies
                "utilization_range": (75, 99),     # Maxed out credit
            }
        }
        
        profile = profiles[risk_profile]
        
        # Generate applicant info
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        age = random.randint(25, 65)
        
        # Generate financial info based on risk profile
        annual_income = random.randint(*profile["income_range"])
        credit_score = random.randint(*profile["credit_score_range"])
        years_employed = round(random.uniform(*profile["years_employed_range"]), 1)
        credit_utilization = random.randint(*profile["utilization_range"])
        
        # Calculate loan amount based on income (typically 2-5x annual income for mortgages)
        loan_purpose = random.choice(cls.LOAN_PURPOSES)
        if loan_purpose == "home_purchase":
            loan_amount = random.randint(
                int(annual_income * 2), 
                min(int(annual_income * 5), 1000000)
            )
            loan_term = random.choice([180, 240, 360])
        elif loan_purpose == "auto":
            loan_amount = random.randint(15000, 75000)
            loan_term = random.choice([36, 48, 60, 72])
        elif loan_purpose == "personal":
            loan_amount = random.randint(5000, 50000)
            loan_term = random.choice([24, 36, 48, 60])
        else:
            loan_amount = random.randint(10000, 250000)
            loan_term = random.choice([36, 60, 84, 120])
        
        # Calculate monthly debt based on DTI ratio
        monthly_income = annual_income / 12
        dti_ratio = random.uniform(*profile["dti_range"])
        monthly_debt = round(monthly_income * dti_ratio, 2)
        
        # Generate savings (typically 3-12 months of expenses for low risk)
        if risk_profile == "low_risk":
            savings = random.randint(int(annual_income * 0.2), int(annual_income * 0.5))
        elif risk_profile == "medium_risk":
            savings = random.randint(int(annual_income * 0.05), int(annual_income * 0.2))
        else:
            savings = random.randint(0, int(annual_income * 0.05))
        
        application = {
            "applicant": {
                "name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
                "phone": f"+1{random.randint(2000000000, 9999999999)}",
                "age": age,
                "ssn_last_four": f"{random.randint(1000, 9999)}"
            },
            "loan": {
                "amount": loan_amount,
                "purpose": loan_purpose,
                "term_months": loan_term,
                "collateral_type": "real_estate" if loan_purpose == "home_purchase" else None,
                "collateral_value": int(loan_amount * random.uniform(1.1, 1.5)) if loan_purpose == "home_purchase" else None
            },
            "employment": {
                "status": random.choice(["employed", "self_employed"]) if years_employed > 0 else "unemployed",
                "employer_name": random.choice(cls.EMPLOYERS),
                "job_title": random.choice(cls.JOB_TITLES),
                "years_employed": years_employed,
                "annual_income": annual_income
            },
            "credit": {
                "credit_score": credit_score,
                "years_credit_history": round(random.uniform(max(1, age - 25), age - 18), 1),
                "num_credit_lines": random.randint(2, 15),
                "credit_utilization": credit_utilization,
                "delinquencies_2yrs": profile["delinquencies"],
                "public_records": 0 if risk_profile == "low_risk" else (
                    random.choice([0, 0, 1, 1, 2]) if risk_profile == "high_risk" else random.choice([0, 0, 0, 1])
                ),
                "hard_inquiries_6mo": random.randint(0, 2) if risk_profile == "low_risk" else (
                    random.randint(3, 8) if risk_profile == "high_risk" else random.randint(1, 4)
                )
            },
            "financial": {
                "monthly_debt": monthly_debt,
                "savings": savings,
                "checking_balance": random.randint(1000, 25000),
                "investment_accounts": random.randint(0, int(annual_income * 0.5)) if risk_profile != "high_risk" else 0,
                "other_income": random.randint(0, int(annual_income * 0.1))
            },
            "documents": [],
            "_metadata": {
                "risk_profile": risk_profile,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        return application
    
    @classmethod
    def generate_batch(cls, count: int = 10, risk_distribution: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple synthetic applications
        
        Args:
            count: Number of applications to generate
            risk_distribution: Dict with keys "low_risk", "medium_risk", "high_risk" 
                             and values as percentages (should sum to 1.0)
        """
        if risk_distribution is None:
            risk_distribution = {"low_risk": 0.4, "medium_risk": 0.4, "high_risk": 0.2}
        
        applications = []
        
        for _ in range(count):
            # Select risk profile based on distribution
            rand = random.random()
            cumulative = 0
            selected_profile = "medium_risk"
            
            for profile, probability in risk_distribution.items():
                cumulative += probability
                if rand <= cumulative:
                    selected_profile = profile
                    break
            
            applications.append(cls.generate_application(selected_profile))
        
        return applications
    
    @classmethod
    def generate_document_extraction(cls, document_type: str, application: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic document extraction results"""
        
        if document_type == "pay_stub":
            return {
                "employer_name": application["employment"]["employer_name"],
                "employee_name": application["applicant"]["name"],
                "pay_period": "Bi-weekly",
                "gross_pay": round(application["employment"]["annual_income"] / 26, 2),
                "net_pay": round(application["employment"]["annual_income"] / 26 * 0.72, 2),
                "ytd_gross": round(application["employment"]["annual_income"] * 0.75, 2),
                "pay_date": (datetime.utcnow() - timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
                "confidence": random.uniform(0.92, 0.99)
            }
        
        elif document_type == "tax_return":
            return {
                "tax_year": datetime.utcnow().year - 1,
                "filing_status": random.choice(["Single", "Married Filing Jointly", "Head of Household"]),
                "total_income": application["employment"]["annual_income"],
                "adjusted_gross_income": round(application["employment"]["annual_income"] * 0.95, 2),
                "taxable_income": round(application["employment"]["annual_income"] * 0.85, 2),
                "total_tax": round(application["employment"]["annual_income"] * 0.22, 2),
                "confidence": random.uniform(0.90, 0.98)
            }
        
        elif document_type == "bank_statement":
            return {
                "account_holder": application["applicant"]["name"],
                "account_type": "Checking",
                "statement_period": f"{(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}",
                "beginning_balance": application["financial"]["checking_balance"] + random.randint(-5000, 5000),
                "ending_balance": application["financial"]["checking_balance"],
                "total_deposits": round(application["employment"]["annual_income"] / 12, 2),
                "total_withdrawals": round(application["employment"]["annual_income"] / 12 * 0.85, 2),
                "confidence": random.uniform(0.94, 0.99)
            }
        
        elif document_type == "id_document":
            return {
                "document_type": random.choice(["Driver's License", "Passport", "State ID"]),
                "full_name": application["applicant"]["name"],
                "date_of_birth": (datetime.utcnow() - timedelta(days=application["applicant"]["age"] * 365)).strftime("%Y-%m-%d"),
                "expiration_date": (datetime.utcnow() + timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d"),
                "document_number": f"{random.choice(['DL', 'PP', 'ID'])}{random.randint(100000000, 999999999)}",
                "confidence": random.uniform(0.95, 0.99)
            }
        
        return {"error": "Unknown document type"}


# Convenience function for quick testing
def get_sample_application(risk_profile: str = "random") -> Dict[str, Any]:
    return SyntheticDataGenerator.generate_application(risk_profile)


def get_sample_batch(count: int = 10) -> List[Dict[str, Any]]:
    return SyntheticDataGenerator.generate_batch(count)
