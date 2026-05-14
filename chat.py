from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os

load_dotenv()

SYSTEM_PROMPT = """
You are FinanceGPT, a friendly personal finance coach for 
Indian salaried professionals aged 24-32.

You help users with:
- Building an emergency fund (target: 6x monthly expenses)
- Starting SIPs in mutual funds (suggest Groww or Zerodha)
- Saving tax under Section 80C (PPF, ELSS, EPF — max ₹1.5L/year)
- HRA optimization for rent-paying employees
- Basic budgeting using the 50/30/20 rule
- Planning for first big goals: home loan, marriage, travel

USER PROFILE:
Name: {name}
Monthly income: ₹{income}
Monthly expenses: ₹{expenses}
Current savings: ₹{savings}
Goals: {goals}

RULES YOU MUST FOLLOW:
- Always use the user profile above to personalize advice
- Use ₹ symbol and Indian number system (lakhs, not millions)
- Never recommend specific stocks — suggest index funds instead
- Never claim to be SEBI registered
- Always double-check your math. Show calculations step by step.
- Keep responses friendly and under 150 words unless asked for more
- Be encouraging — never shame bad money habits
- If user has no savings, start with emergency fund before SIP
"""

def get_user_profile():
    print("=" * 40)
    print("  Welcome to FinanceGPT!")
    print("  Let's set up your profile first.")
    print("=" * 40)
    print()

    name     = input("Your name: ")
    income   = input("Monthly income (₹): ")
    expenses = input("Monthly expenses (₹): ")
    savings  = input("Current total savings (₹): ")
    goals    = input("Your financial goals (e.g. emergency fund, SIP, buy bike): ")

    print()
    print(f"Got it, {name}! Starting your session...\n")

    return {
        "name": name,
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "goals": goals
    }

llm = ChatMistralAI(
    model="mistral-large-latest",
    api_key=os.getenv("MISTRAL_API_KEY")
)

# Ask user for their real data
user_profile = get_user_profile()

system = SYSTEM_PROMPT.format(**user_profile)
chat_history = [SystemMessage(content=system)]

print("FinanceGPT ready! Type 'quit' to exit.\n")
print("-" * 40)

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    chat_history.append(HumanMessage(content=user_input))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response.content))

    print(f"\nFinanceGPT: {response.content}\n")
    print("-" * 40)

