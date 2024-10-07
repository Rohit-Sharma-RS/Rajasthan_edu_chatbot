import json
import pandas as pd
import cohere
import re
from thefuzz import fuzz, process
import os
from dotenv import load_dotenv

load_dotenv('api.env')
def load_data(file_path='data.json'):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return pd.json_normalize(data)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Unable to parse JSON from {file_path}.")
        return None

df = load_data()
if df is None:
    print("Exiting due to data loading error.")
    exit(1)
cohere_api_key = os.getenv('COHERE_API_KEY')
if not cohere_api_key:
    print("Error: COHERE_API_KEY not found in api.env file.")
    exit(1)

try:
    co = cohere.Client(cohere_api_key)
except Exception as e:
    print(f"Error initializing Cohere client: {str(e)}")
    exit(1)

conversation_history = []

def parse_user_input(user_input):
    score = ''.join(filter(str.isdigit, user_input))
    score = int(score) if score else None
    
    college_match = re.search(r"(?:cutoff|information|fees|package|salary|life|placements|recruiters).*?\b([A-Za-z\s]+)\b", user_input, re.IGNORECASE)
    college_name = college_match.group(1).strip() if college_match else None
    
    year_match = re.search(r'\b(2023|2022|2021)\b', user_input)
    year = year_match.group(0) if year_match else '2023'
    
    return score, college_name, year

def get_unique_exams():
    return list(df['admission.exam'].unique())

unique_exams = get_unique_exams()
def fuzzy_match_college(college_name, threshold=70):
    if not college_name:
        return None
    def match_score(x):
        full_name_score = fuzz.ratio(x.lower(), college_name.lower())
        acronym_score = fuzz.ratio(''.join(word[0] for word in x.split() if word).lower(), college_name.lower())
        return max(full_name_score, acronym_score)

    best_match = max(df['name'], key=match_score)
    if match_score(best_match) > threshold:
        return best_match
    return None
def get_college_cutoff(college_name, year='2023'):
    matched_college = fuzzy_match_college(college_name)
    if matched_college:
        college = df[df['name'] == matched_college]
        if not college.empty:
            cutoff_column = f'admission.cutoff.{year}'
            if cutoff_column in college.columns:
                cutoff_info = college.iloc[0][cutoff_column]
                if pd.notna(cutoff_info):
                    return f"The cutoff for {matched_college} in {year} is {cutoff_info}."
                else:
                    return f"Cutoff information for the year {year} is not available."
            else:
                return f"Cutoff information for the year {year} is not available."
    return f"College '{college_name}' not found."


def normalize_column(column):
    return (column - column.min()) / (column.max() - column.min())

def find_best_college(eligible_colleges):
    if eligible_colleges is None or eligible_colleges.empty:
        return "There are no eligible colleges available. Please ask for eligible colleges first."

    eligible_colleges['normalized_avg_package'] = normalize_column(eligible_colleges['placements.average_package'].astype(float))
    eligible_colleges['normalized_rating'] = normalize_column(eligible_colleges['rating'].astype(float))
    eligible_colleges['normalized_highest_package'] = normalize_column(eligible_colleges['placements.highest_package'].astype(float))
    eligible_colleges['normalized_cutoff'] = 1 - normalize_column(eligible_colleges['admission.cutoff.2023'].astype(float))

    weights = {
        'avg_package': 0.4,
        'rating': 0.1,
        'highest_package': 0.2,
        'cutoff': 0.3
    }

    eligible_colleges['composite_score'] = sum(weights[param] * eligible_colleges[f'normalized_{param}'] for param in weights)

    best_college = eligible_colleges.loc[eligible_colleges['composite_score'].idxmax()]
    ai_prompt = f"The best college is {best_college['name']} in {best_college['location']}. It has an average package of ₹{best_college['placements.average_package']} and a rating of {best_college['rating']}. Please provide a reason why this college is the best based on its rating, placement, and cutoff score."
    
    try:
        explanation = co.generate(
            model='command',
            prompt=ai_prompt,
            max_tokens=100,
            temperature=0.7
        ).generations[0].text.strip()

        return f"The best college is {best_college['name']} in {best_college['location']}.\n\nAI Explanation: {explanation}"
    
    except Exception as e:
        return f"The best college is {best_college['name']} in {best_college['location']} but there was an issue generating an AI explanation: {str(e)}"

def get_colleges_by_score(score, exam):
    eligible_colleges = df[df['admission.exam'] == exam]
    
    if exam in ["JEE Main", "REAP", "MET"]:
        eligible_colleges = eligible_colleges[eligible_colleges['admission.cutoff.2023'].astype(int) >= score]
    elif exam == "BITSAT":
        eligible_colleges = eligible_colleges[eligible_colleges['admission.cutoff.2023'].astype(int) <= score]
    else:
        return f"I'm sorry, but I don't have specific information about how to interpret scores for the {exam} exam."
    
    if eligible_colleges.empty:
        return f"I'm sorry, but with the given {exam} score/rank of {score}, you may not be eligible for any of the colleges in our database. Consider exploring other options or improving your score."
    else:
        result = eligible_colleges[['name', 'location', 'rating']].head(10).to_string(index=False)
        return f"Based on your {exam} score/rank of {score}, you may be eligible for the following colleges:\n\n{result}", eligible_colleges

def get_college_fees(college_name):
    matched_college = fuzzy_match_college(college_name)
    if matched_college:
        college = df[df['name'] == matched_college]
        if not college.empty:
            courses = college.iloc[0]['courses']
            fees_info = "\n".join([f"{course['name']}: ₹{course['annual_fee']} per year" for course in courses])
            return f"Annual fees for {matched_college}:\n{fees_info}"
    else:
        return f"College '{college_name}' not found."

def get_median_salary(college_name):
    matched_college = fuzzy_match_college(college_name)
    if matched_college:
        college = df[df['name'] == matched_college]
        if not college.empty:
            avg_package = college['placements.average_package'].iloc[0]
            return f"The average package for {matched_college} is ₹{avg_package} per annum."
    return f"College '{college_name}' not found."

def get_college_info(college_name):
    matched_college = fuzzy_match_college(college_name)
    if matched_college:
        college = df[df['name'] == matched_college]
        if not college.empty:
            info = college.iloc[0]
            return f"""
College: {info['name']}
Location: {info['location']}
Type: {info['type']}
Rating: {info['rating']}
Admission Exam: {info['admission.exam']}
Average Package: ₹{info['placements.average_package']}
Highest Package: ₹{info['placements.highest_package']}
Top Recruiters: {', '.join(info['placements.top_recruiters'])}
Facilities: {', '.join(info['facilities'])}
            """
    return f"College '{college_name}' not found."
def handle_general_questions(user_input):
    try:
        ai_prompt = f"""
        You are an expert on engineering colleges in Rajasthan. Answer the following question in a detailed and helpful manner:
        {user_input}.
        
        Provide a clear, factual, and informative response based on common knowledge about Rajasthan engineering colleges, their environment, placements, facilities, and courses.
        """
        
        response = co.generate(
            model='command',
            prompt=ai_prompt,
            max_tokens=200,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return f"An error occurred while using AI: {str(e)}"
    
def truncate_conversation_history(max_length=10):
    # Keep only the last `max_length` exchanges in the history
    if len(conversation_history) > max_length:
        conversation_history[:] = conversation_history[-max_length:]
    
def process_query(user_input):
    global eligible_colleges
    lower_input = user_input.lower()

    # Append user input to conversation history
    conversation_history.append(f"You: {user_input}")

    if any(greet in lower_input for greet in ["hi", "hello", "hey", "howdy", "what's up"]):
        response = "Hello! How can I assist you with information about engineering colleges in Rajasthan?"
        conversation_history.append(f"Chatbot: {response}")
        return response

    score, college_name, year = parse_user_input(user_input)
    
    if "which colleges can i get" in lower_input:
        if score is not None:
            exam = next((exam for exam in unique_exams if exam.lower() in lower_input), None)
            if exam:
                result, eligible_colleges = get_colleges_by_score(score, exam)
                return result
            else:
                return "Please specify a valid exam (e.g., JEE Main, BITSAT, REAP, MET)."
        else:
            return "Please provide a valid rank or score."

    elif "which college is best" in lower_input:
        if eligible_colleges is None:
            return "Please specify a score and exam first to find eligible colleges."
        return find_best_college(eligible_colleges)
    
    elif "cutoff" in lower_input:
        if college_name:
            return get_college_cutoff(college_name, year)
        else:
            return "I'm sorry, I couldn't find the college name in your request."
    
    elif "fees" in lower_input:
        if college_name:
            return get_college_fees(college_name)
        else:
            return "Please provide a college name for fee information."

    elif "median salary" in lower_input or "average package" in lower_input:
        if college_name:
            return get_median_salary(college_name)
        else:
            return "Please provide a college name for placement package information."
    
    else:
        ai_prompt = "\n".join(conversation_history) + f"\nChatbot: "
        response = co.generate(
            model='command',
            prompt=ai_prompt,
            max_tokens=100,
            temperature=0.7
        ).generations[0].text.strip()

        conversation_history.append(f"Chatbot: {response}")
        return response

def run_chatbot():
    print("Welcome to the Rajasthan Engineering College Chatbot!")
    print(f"You can ask about college eligibility based on these exams: {', '.join(unique_exams)}")
    print("You can also ask about college fees, placements, and general information.")
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
