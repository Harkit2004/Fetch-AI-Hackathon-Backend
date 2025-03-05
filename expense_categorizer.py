import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load API keys from .env file

openai.api_key = os.getenv("OPENAI_API_KEY")

CATEGORIES = ["Groceries", "Rent", "Bills", "Entertainment", "Transport", "Healthcare", "Education", "Shopping"]

def categorize_expense(description: str) -> str:
    """
    Uses OpenAI's API to categorize an expense description into predefined categories.
    """
    prompt = f"Classify this expense: '{description}' into one of the following categories: {', '.join(CATEGORIES)}."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    category = response["choices"][0]["message"]["content"].strip()
    
    if category not in CATEGORIES:
        category = "Other"

    return category

# Example usage
if __name__ == "__main__":
    print(categorize_expense("Netflix monthly subscription"))
