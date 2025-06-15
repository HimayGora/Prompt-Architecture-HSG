from dotenv import load_dotenv
import os
import google.generativeai as genai
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

print(f"Current Python: {os.path.dirname(os.__file__)}")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in environment variables")
else:
    print(f"API key found: {api_key[:5]}...")

# --- Configuration ---
# Ensure GEMINI_API_KEY is set in your .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Generative Model
# Using 'gemini-1.5-flash' for faster responses and lower cost,
# or 'gemini-1.5-pro' for more advanced reasoning.
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Global Variables ---
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts")  # Base directory for prompts

# --- Utility Functions ---
def read_prompt_file(file_path="prompt.md"):
    """
    Read the content of the prompt file, ignoring HTML/Markdown comments.
    """
    full_path = os.path.join(PROMPT_PATH, file_path) if not os.path.isabs(file_path) else file_path
    print(f"Reading from: {full_path}")  # Debug info

    try:
        with open(full_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            content_lines = []
            in_html_comment = False

            for line in lines:
                stripped_line = line.strip()
                
                # Handle HTML comments
                if '<!--' in stripped_line:
                    in_html_comment = True
                    continue
                if '-->' in stripped_line:
                    in_html_comment = False
                    continue
                
                # Skip comments and empty lines
                if not in_html_comment and stripped_line and not stripped_line.startswith('//'):
                    content_lines.append(line)

            content = ''.join(content_lines).strip()
            print(f"Content length: {len(content)} characters")  # Debug info
            return content

    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found at {full_path}")
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        return ""

def generate_text_with_gemini(prompt_text, temperature=.4, max_output_tokens=500):
    """
    Generate text using the Gemini model.

    Args:
        prompt_text (str): The input prompt for text generation.
        temperature (float): Controls the randomness of the output (0.0 to 0.8 any higher is unusable in nomral marketing copy).
                             Lower values produce more deterministic results.
        max_output_tokens (int): Maximum number of tokens to generate.

    Returns:
        str: The generated text, or an error message if generation fails.
    """
    if not prompt_text:
        return "Error: Prompt text is empty."

    try:
        # CORRECTED: Use model.generate_content() instead of model.generate_text()
        response = model.generate_content(
            [prompt_text],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
        )
        # Access the text from the response object
        if response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            return "No content generated. Possible safety or other issues."
    except Exception as e:
        return f"An error occurred during text generation: {e}"

def save_output(generated_text, prompt_file_name="prompt.md"):
    """
    Save the generated text to a new file with timestamp.
    Includes the prompt file name in the output filename for better organization.

    Args:
        generated_text (str): The text to save.
        prompt_file_name (str): The name of the prompt file used.

    Returns:
        str: Path to the created output file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "outputs"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use the base name of the prompt file for the output file name
    base_prompt_name = os.path.splitext(os.path.basename(prompt_file_name))[0]
    output_file = os.path.join(output_dir, f"{base_prompt_name}_output_{timestamp}.txt")

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(generated_text)

    return output_file

# --- Main Execution ---
if __name__ == "__main__":
    prompt_file = "prompt.md"  # Just the filename

    try:
        # Ensure prompts directory exists
        if not os.path.exists(PROMPT_PATH):
            os.makedirs(PROMPT_PATH)
            
        print(f"Reading from: {os.path.join(PROMPT_PATH, prompt_file)}")
        prompt_content = read_prompt_file(prompt_file)
        
        if prompt_content:
            print(f"--- Running prompt from '{prompt_file}' ---")
            result = generate_text_with_gemini(
                prompt_content, 
                temperature=0.7,
                max_output_tokens=800
            )
            output_path = save_output(result, prompt_file)
            print(f"\nGenerated text saved to: {output_path}")
            print("\nGenerated content:")
            print(result)
        else:
            print("No valid prompt content found. Please check your prompt file.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Make sure the prompt file exists in {PROMPT_PATH}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")