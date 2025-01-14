import subprocess
import os
import fitz  # PyMuPDF

# Define inputs in one place
dataset_folder = r"C:\\Users\\omrha\\Desktop\\projects\\dataset"  # Input directory
output_file = os.path.join(dataset_folder, "results.txt")  # Output file
prompt = """Process the following images and return ONLY in JSON format. 
             Extract relevant key-value pairs for the invoice. For example:
             {{"invoice_number":2514885}}
          """  # Prompt for Llama model

def list_llm_models():
    """
    Retrieves a list of all available Ollama models.

    Returns:
    - list of str: Names of available models, or an empty list if an error occurs.
    """
    print("Fetching available Llama models...")
    try:
        result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error listing models: {result.stderr}")
            return []
        models = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
        print(f"Available models: {models}")
        return models
    except FileNotFoundError:
        print("Ollama CLI not found. Ensure it is installed and available in your PATH.")
        return []

def select_llm_model(models):
    """
    Prompts the user to select an Ollama model from a list.

    Returns:
    - str: The selected model name.
    """
    print("Available Models:")
    for idx, model in enumerate(models):
        print(f"{idx + 1}: {model}")
    
    while True:
        try:
            choice = int(input("Enter the number of the model to select: "))
            if 1 <= choice <= len(models):
                print(f"Model selected: {models[choice - 1]}")
                return models[choice - 1]
            else:
                print("Invalid choice. Please select a valid model number.")
        except ValueError:
            print("Please enter a numeric value.")

def convert_pdf_pages_to_png(pdf_path, output_folder):
    """
    Converts all pages of a PDF file to PNG images and saves them in the specified folder.

    Returns:
    - bool: True if conversion is successful, False otherwise.
    """
    try:
        print(f"Converting PDF '{pdf_path}' into PNGs...")
        doc = fitz.open(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        for page_number in range(len(doc)):
            print(f"Rendering page {page_number + 1} of {len(doc)}...")
            page = doc[page_number]
            pix = page.get_pixmap(dpi=300)  # Set DPI for quality
            output_file = os.path.join(output_folder, f"{pdf_name}_page_{page_number + 1}.png")
            pix.save(output_file)
        doc.close()
        print(f"PDF '{pdf_path}' successfully converted to PNGs.")
        return True
    except Exception as e:
        print(f"Error converting {pdf_path} to PNG: {e}")
        return False

def pdf_to_text(folder_path, model, prompt):
    """
    Processes all PDF files in the specified folder by:

    1. Converting each page of the PDFs into PNG files, stored in a subdirectory named after the PDF file.
       - Calls the `convert_pdf_pages_to_png` function to handle the conversion.
    2. Processing the PNG files using the specified Llama model to extract key-value pairs.
       - The Llama model is invoked via `subprocess.run`.
    3. Writing the extracted data to a text file in JSON format.
       - The output for each PDF is saved in its corresponding folder.

    Outputs:
    - PNG files for each page, stored in a folder named after the PDF within the 'converted_pngs' directory.
    - A text file containing JSON-formatted results for each PDF, saved in the respective folder.
    """
    output_folder = os.path.join(folder_path, "converted_pngs")
    os.makedirs(output_folder, exist_ok=True)
    
    print("Starting PDF-to-text conversion...")
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            pdf_name = os.path.splitext(filename)[0]
            pdf_output_folder = os.path.join(output_folder, pdf_name)
            os.makedirs(pdf_output_folder, exist_ok=True)

            # Output file for the specific PDF
            pdf_output_file = os.path.join(pdf_output_folder, f"{pdf_name}_results.txt")

            print(f"Processing PDF: {filename}")
            if convert_pdf_pages_to_png(pdf_path, pdf_output_folder):
                with open(pdf_output_file, "w", encoding="utf-8") as outfile:
                    for page_filename in sorted(os.listdir(pdf_output_folder)):
                        if page_filename.endswith(".png"):
                            page_path = os.path.join(pdf_output_folder, page_filename)
                            print(f"Processing PNG: {page_filename} using model '{model}'...")
                            try:
                                result = subprocess.run(
                                    ["ollama", "run", model],
                                    input=prompt + f" File: {page_path}",
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    encoding="utf-8"  # Ensure utf-8 decoding
                                )
                                if result.returncode != 0:
                                    print(f"Error processing {page_filename}: {result.stderr}")
                                    outfile.write(f"Error processing {page_filename}: {result.stderr}\n")
                                else:
                                    print(f"Successfully processed {page_filename}")
                                    outfile.write(result.stdout + "\n")
                            except FileNotFoundError:
                                print("Ollama CLI not found. Ensure it is installed and available in your PATH.")
                                outfile.write(f"Error processing {page_filename}: Ollama CLI not found\n")
            print(f"Finished processing PDF: {filename}")

    print("All PDFs processed successfully!")

# Driver Code
if __name__ == "__main__":
    print("Initializing program...")
    selected_model = "llama3.2-vision:latest"  # Replace with your selected model
    llama_prompt = """Process the following image and return ONLY in JSON format.
    Extract relevant key-value pairs for the invoice. Example: {"invoice_number": 123456}."""

    # Call the main function
    pdf_to_text(dataset_folder, selected_model, llama_prompt)
    print("Program complete!")
