import json
import pandas as pd
import cohere
import re
from thefuzz import fuzz
import os
from dotenv import load_dotenv

load_dotenv('api.env')

def load_data(file_path='data.json'):
    """Load and normalize JSON data."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return pd.json_normalize(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {str(e)}")
        return None

df = load_data()
if df is None:
    exit("Data loading error. Exiting.")

cohere_api_key = os.getenv('COHERE_API_KEY')
if not cohere_api_key:
    exit("Error: COHERE_API_KEY not found.")

co = cohere.Client(cohere_api_key)
conversation_history = []

def parse_user_input(user_input):
    """Extract score, college name, and year from user input."""
    score = next((int(s) for s in re.findall(r'\d+', user_input)), None)
    college_name = re.search(r"(?:cutoff|information|fees|package|salary|life|placements|recruiters).*?\b([A-Za-z\s]+)\b", user_input, re.IGNORECASE)
    college_name = college_name.group(1).strip() if college_name else None
    year = re.search(r'\b(2023|2022|2021)\b', user_input)
    year = year.group(0) if year else '2023'
    return score, college_name, year

def fuzzy_match_college(college_name, threshold=70):
    """Fuzzy match college names."""
    if not college_name:
        return None
    best_match = max(df['name'], key=lambda x: max(fuzz.ratio(x.lower(), college_name.lower()), 
                                                   fuzz.ratio(''.join(word[0] for word in x.split()).lower(), college_name.lower())))
    return best_match if fuzz.ratio(best_match.lower(), college_name.lower()) > threshold else None

def get_college_cutoff(college_name, year='2023'):
    """Retrieve college cutoff information."""
    matched_college = fuzzy_match_college(college_name)
    if matched_college:
        college = df[df['name'] == matched_college]
        cutoff_column = f'admission.cutoff.{year}'
        cutoff_info = college.iloc[0][cutoff_column] if not college.empty and cutoff_column in college.columns else None
        return (f"The cutoff for {matched_college} in {year} is {cutoff_info}."
                if cutoff_info is not None else "Cutoff information for the year is not available.")
    return f"College '{college_name}' not found."

def get_colleges_by_score(score, exam):
    """Get eligible colleges based on exam scores."""
    eligible_colleges = df[df['admission.exam'] == exam]
    condition = (eligible_colleges['admission.cutoff.2023'].astype(int) >= score if exam in ["JEE Main", "REAP", "MET"] 
                 else eligible_colleges['admission.cutoff.2023'].astype(int) <= score if exam == "BITSAT" 
                 else None)
    eligible_colleges = eligible_colleges[condition] if condition is not None else eligible_colleges
    
    if eligible_colleges.empty:
        return "No eligible colleges found."
    return eligible_colleges[['name', 'location', 'rating']].head(10).to_string(index=False), eligible_colleges

def find_best_college(eligible_colleges):
    """Determine the best college based on composite scoring."""
    if eligible_colleges.empty:
        return "No eligible colleges available."
    
    weights = {'avg_package': 0.4, 'rating': 0.1, 'highest_package': 0.2, 'cutoff': 0.3}
    eligible_colleges['composite_score'] = sum(weights[param] * (eligible_colleges[param].astype(float) - eligible_colleges[param].min()) / (eligible_colleges[param].max() - eligible_colleges[param].min()) 
                                                for param in weights)
    
    best_college = eligible_colleges.loc[eligible_colleges['composite_score'].idxmax()]
    return f"The best college is {best_college['name']} located in {best_college['location']}."

def process_query(user_input):
    """Process the user's query and return an appropriate response."""
    global eligible_colleges
    conversation_history.append(f"You: {user_input}")
    lower_input = user_input.lower()

    if any(greet in lower_input for greet in ["hi", "hello", "hey"]):
        response = "Hello! How can I assist you today?"
    elif "which colleges can i get" in lower_input:
        score, _, exam = parse_user_input(user_input)
        if score is not None and exam in df['admission.exam'].unique():
            result, eligible_colleges = get_colleges_by_score(score, exam)
            response = result
        else:
            response = "Please provide a valid score and exam."
    elif "which college is best" in lower_input:
        if eligible_colleges is None or eligible_colleges.empty:
            response = "Please specify a score and exam first."
        else:
            response = find_best_college(eligible_colleges)
    elif "cutoff" in lower_input:
        score, college_name, year = parse_user_input(user_input)
        response = get_college_cutoff(college_name, year)
    else:
        # Handle general queries
        response = f"Sorry, I can't help with that right now."

    conversation_history.append(f"Chatbot: {response}")
    return response

def run_chatbot():
    """Run the chatbot interface."""
    print("Welcome to the Rajasthan Engineering College Chatbot!")
    print("Type 'quit' to exit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            print("Thank you for using the chatbot. Goodbye!")
            break
        
        response = process_query(user_input)
        print(f"\nChatbot: {response}")

if __name__ == "__main__":
    run_chatbot()
