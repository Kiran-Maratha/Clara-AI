import json
import os
import argparse

DATASET_PATH = os.path.join(os.path.dirname(__file__), 'dataset.jsonl')

def add_example(user_input, model_response):
    """Appends a new conversation example to the JSONL dataset."""
    entry = {
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "model", "content": model_response}
        ]
    }
    
    with open(DATASET_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
        
    print(f"Successfully added example to {DATASET_PATH}")
    print(f"Total examples: {count_examples()}")

def count_examples():
    """Counts the number of examples currently in the dataset."""
    if not os.path.exists(DATASET_PATH):
        return 0
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        return sum(1 for line in f if line.strip())

def export_for_google_ai_studio():
    """Provides instructions on how to use this data with Google Gemini."""
    print("\n--- HOW TO TRAIN YOUR CLARA AI MODEL ---")
    print("1. Go to Google AI Studio: https://aistudio.google.com/")
    print("2. Click on 'New tuned model' in the left sidebar.")
    print("3. Select your base model (e.g., gemini-1.5-flash or gemini-1.5-flash-lite).")
    print(f"4. Click 'Import' and upload this file: {os.path.abspath(DATASET_PATH)}")
    print("5. Click 'Tune' to start the process.")
    print("6. Once tuning completes, copy the newly generated 'Model ID'.")
    print("7. Open 'ai_service.py' in your codebase and replace the 'answer_model' variable with your new Model ID.")
    print("----------------------------------------\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Clara AI Training Data")
    parser.add_argument('--add', action='store_true', help='Add a new conversational example via prompts')
    parser.add_argument('--info', action='store_true', help='Show dataset info and training instructions')
    
    args = parser.parse_args()
    
    if args.add:
        print("--- Add New Training Example ---")
        try:
            u_input = input("User Question/Input: ").strip()
            m_response = input("Ideal AI Response: ").strip()
            
            if u_input and m_response:
                add_example(u_input, m_response)
            else:
                print("Error: Both input and response are required.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            
    elif args.info or not any(vars(args).values()):
        print(f"Current Dataset: {DATASET_PATH}")
        print(f"Total Training Examples: {count_examples()}")
        export_for_google_ai_studio()
