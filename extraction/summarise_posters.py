import google.generativeai as genai
from PIL import Image
import os
from getpass import getpass
import html

# --- Configuration ---
# Set your Gemini API key securely.

genai.configure(api_key=getpass("Enter your Gemini API key: "))

# --- Main Script ---
def create_poster_summary_document_html():
    """
    Scans a folder for poster images, generates summaries using the
    Gemini 1.5 Flash API, and creates an HTML document with the
    images and their summaries.
    """
    # Get the folder containing the poster images from the user.
    image_folder = input("Enter the path to the folder containing your poster photos: ")
    if not os.path.isdir(image_folder):
        print(f"Error: The folder '{image_folder}' does not exist.")
        return

    # Get the desired output filename from the user.
    output_filename = input("Enter the name for the output HTML file (e.g., conference_summary.html): ")
    if not output_filename.lower().endswith(".html"):
        output_filename += ".html"

    # Initialize the Gemini model.
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Create and open the HTML file for writing.
    with open(output_filename, "w", encoding="utf-8") as html_file:
        # --- HTML Header and Style ---
        html_file.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conference Poster Summaries</title>
    <script>
        // Add a click handler to make images open in a new tab
        document.addEventListener('DOMContentLoaded', function() {
            const thumbnails = document.querySelectorAll('.thumbnail');
            thumbnails.forEach(img => {
                img.title = "Click to view full size image in a new tab";
            });
        });
    </script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 960px;
            margin: 20px auto;
            padding: 0 20px;
            background-color: #f9f9f9;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        h1 {
            text-align: center;
            border-bottom: 2px solid #eaeaea;
            padding-bottom: 10px;
        }
        .poster-entry {
            background-color: #ffffff;
            border: 1px solid #dddddd;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .thumbnail {
            max-width: 300px;
            height: auto;
            border-radius: 4px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .thumbnail:hover {
            transform: scale(1.05);
        }
        .authors {
            color: #666;
            font-style: italic;
            margin-bottom: 15px;
        }
        .section {
            margin-top: 20px;
        }
        .section-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        p {
            white-space: pre-wrap; /* Preserves line breaks from the API response */
        }
        hr {
            border: 0;
            height: 1px;
            background: #e0e0e0;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <h1>Conference Poster Summaries</h1>
""")

        print("\nProcessing poster images...")

        # Iterate through each file in the specified folder.
        for filename in sorted(os.listdir(image_folder)):
            # Check for common image file extensions.
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".heic")):
                image_path = os.path.join(image_folder, filename)
                print(f"  - Processing: {filename}")

                try:
                    # Open the image file.
                    img = Image.open(image_path)

                    # Generate structured information using the Gemini API.
                    response = model.generate_content(
                        [
                            """Extract the following information from this academic conference poster and format as JSON:
                            {
                              "title": "The main title of the poster",
                              "authors": "List of authors and their affiliations",
                              "research_question": "The key research question or objective",
                              "methods": "The methodologies used in the research",
                              "results": "The key findings of the research",
                              "conclusions": "The main conclusions and implications"
                            }
                            
                            Note: Keep each field concise but informative. If any field is not clearly visible, write "Not specified in poster".""",
                            img
                        ]
                    )
                    
                    # Try to parse the JSON response, but handle cases where response might not be proper JSON
                    try:
                        import json
                        import re
                        
                        # Try to extract JSON from the response if there's any surrounding text
                        json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL) or \
                                     re.search(r'```\s*(.*?)\s*```', response.text, re.DOTALL) or \
                                     re.search(r'({.*})', response.text, re.DOTALL)
                        
                        if json_match:
                            poster_data = json.loads(json_match.group(1).strip())
                        else:
                            poster_data = json.loads(response.text.strip())
                            
                        # Extract the structured data
                        poster_title = html.escape(poster_data.get("title", "Untitled Poster"))
                        authors = html.escape(poster_data.get("authors", "Unknown Authors"))
                        research_question = html.escape(poster_data.get("research_question", ""))
                        methods = html.escape(poster_data.get("methods", ""))
                        results = html.escape(poster_data.get("results", ""))
                        conclusions = html.escape(poster_data.get("conclusions", ""))
                        
                    except Exception as json_error:
                        print(f"    - Could not parse structured data: {json_error}")
                        # Fall back to using filename as title and full text as summary
                        poster_title = html.escape(os.path.splitext(filename)[0])
                        authors = "Unknown Authors"
                        summary_text = html.escape(response.text)


                    # Write the HTML content for this entry.
                    html_file.write(f'    <div class="poster-entry">\n')
                    html_file.write(f'        <h2>{poster_title}</h2>\n')
                    html_file.write(f'        <div class="authors">{authors}</div>\n')
                    
                    # Create a thumbnail that opens the full image in a new tab when clicked
                    html_file.write(f'        <a href="{html.escape(image_path)}" target="_blank">\n')
                    html_file.write(f'            <img class="thumbnail" src="{html.escape(image_path)}" alt="Poster image: {poster_title}">\n')
                    html_file.write(f'        </a>\n')
                    
                    # If we successfully parsed structured data, display it in sections
                    if 'research_question' in locals():
                        html_file.write(f'        <div class="section">\n')
                        html_file.write(f'            <div class="section-title">Research Question / Objective</div>\n')
                        html_file.write(f'            <p>{research_question}</p>\n')
                        html_file.write(f'        </div>\n')
                        
                        html_file.write(f'        <div class="section">\n')
                        html_file.write(f'            <div class="section-title">Methods</div>\n')
                        html_file.write(f'            <p>{methods}</p>\n')
                        html_file.write(f'        </div>\n')
                        
                        html_file.write(f'        <div class="section">\n')
                        html_file.write(f'            <div class="section-title">Results</div>\n')
                        html_file.write(f'            <p>{results}</p>\n')
                        html_file.write(f'        </div>\n')
                        
                        html_file.write(f'        <div class="section">\n')
                        html_file.write(f'            <div class="section-title">Conclusions</div>\n')
                        html_file.write(f'            <p>{conclusions}</p>\n')
                        html_file.write(f'        </div>\n')
                    else:
                        # Fallback to simple summary
                        html_file.write(f'        <h3>Summary</h3>\n')
                        html_file.write(f'        <p>{summary_text}</p>\n')
                        
                    html_file.write(f'    </div>\n')


                except Exception as e:
                    print(f"    - Error processing {filename}: {e}")
                    html_file.write(f'<div class="poster-entry">\n')
                    html_file.write(f'    <h2>Error processing {html.escape(filename)}</h2>\n')
                    html_file.write(f'    <div class="authors">Could not process this poster</div>\n')
                    html_file.write(f'    <a href="{html.escape(image_path)}" target="_blank">\n')
                    html_file.write(f'        <img class="thumbnail" src="{html.escape(image_path)}" alt="Error processing poster">\n')
                    html_file.write(f'    </a>\n')
                    html_file.write(f'    <p>{html.escape(str(e))}</p>\n')
                    html_file.write(f'</div>\n')


        # --- HTML Footer ---
        html_file.write("""
</body>
</html>""")

    print(f"\nSuccessfully created the summary document: {output_filename}")
    print("\nThe summary includes:")
    print("  - Extracted poster titles and authors")
    print("  - Structured information (research question, methods, results, conclusions)")
    print("  - Thumbnail images that open full-size when clicked")
    print("\nOpen the HTML file in your browser to view the summaries.")

if __name__ == "__main__":
    create_poster_summary_document_html()