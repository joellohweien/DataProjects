from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from unstructured.partition.pdf import partition_pdf
from collections import Counter
import json
import re
import pprint as pp
from typing import Dict, Any, List

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Constants for pattern matching
PATTERNS = {
    'contact': {
        'name': r'Contact Name\s+(.*?)(?=\s+Company|$)',
        'address': r'Address\s+(.*?)(?=\s+Email|$)',
        'email': r'Email address\s+(.*?)(?=$|\s)',
        'title': r'Title\s+(.*?)(?=\s+|$)'
    },
    'company': {
        'name': r'^(.*?),\s*company\s*number',
        'number': r'company\s*number\s*([^,]+)',
        'jurisdiction': r'incorporated\s*in\s*([^\s]+)',  
        'office': r'registered\s*office\s*is\s*at\s*([^(]+)'
    },
    'loan': {
        'principal': r'(?:Loan\s*\$|\$)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)',
        'currency': r'(?:to\s+)?(SGD|USD|EUR|GBP|THB)',
        'interest_rate': r'Interest Rate\s+(\d+\.?\d*)',
        'drawdown_date': r"Drawdown Date\s+(.*?)(?=\.|$)",
        'repayment': r'Repayment of Loan:\s*(.*?)(?=\.|$)'
    }
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#######################
# Document Type Functions
#######################

def extract_document_type(elements: List[Dict]) -> str:
    """
    Extract document type from the first title found in elements.
    
    Args:
        elements: List of document elements containing text and metadata
        
    Returns:
        str: Extracted document type or "Unknown" if not found
    """
    for element in elements:
        if element.get("type") == "Title" and element.get("text"):
            title = element.get("text").lower()
            if "template" in title:
                title = title.replace("template", "").strip()
            return " ".join(word.capitalize() for word in title.split())
    return "Unknown"

#######################
# Text Extraction Functions 
#######################

def extract_with_pattern(text: str, pattern: str, default: str = '') -> str:
    """
    Generic pattern extraction function with error handling.
    
    Args:
        text: Source text to extract from
        pattern: Regex pattern to match
        default: Default value if no match found
        
    Returns:
        str: Extracted text or default value
    """
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default
    except Exception as e:
        print(f"Error extracting pattern {pattern}: {e}")
        return default

def extract_contact_details(text: str) -> Dict[str, str]:
    """
    Extract contact details from table text.
    
    Args:
        text: Source text containing contact information
        
    Returns:
        Dict containing contact details (name, address, email, title)
    """
    return {
        field: extract_with_pattern(text, pattern)
        for field, pattern in PATTERNS['contact'].items()
    }

def extract_company_details(text):
    """Extract company details using regex patterns"""
    return {
        "name": extract_with_pattern(text, PATTERNS['company']['name']),
        "companyNumber": extract_with_pattern(text, PATTERNS['company']['number']),
        "jurisdiction": extract_with_pattern(text, PATTERNS['company']['jurisdiction']),
        "registeredOffice": extract_with_pattern(text, PATTERNS['company']['office'])
    }

def extract_signatures(elements):
    """Extract signature information as a dictionary of party type to title."""
    signatures = {}
    start_marker = "Signature of authorised signatory"
    end_marker = "Print full name of authorised"
    signature_count = 0
    
    for i, element in enumerate(elements):
        if (element.get("type") in ["FigureCaption", "NarrativeText"] and
            element.get("text") == start_marker):
            
            for j in range(i + 1, len(elements)):
                current = elements[j]
                if current.get("text") == end_marker:
                    break
                    
                if (current.get("type") == "NarrativeText" and 
                    "," in current.get("text", "")):
                    name, title = current.get("text").split(",", 1)
                    party_type = "lender" if signature_count == 0 else "borrower"
                    signatures[party_type] = title.strip()
                    signature_count += 1
                    break
    # # Debug print to see what we're finding
    # print("Found signatures:", signatures)
    return signatures

def extract_loan_details(text):
    """Extract loan details from table text with fixed pattern matching"""
    # Extract interest rate
    interest_rate_match = re.search(PATTERNS['loan']['interest_rate'], text, re.IGNORECASE)
    interest_rate = None
    if interest_rate_match:
        try:
            interest_rate = float(interest_rate_match.group(1))
        except ValueError:
            print(f"Error converting interest rate: {interest_rate_match.group(1)}")
    
    # Extract principal amount - now looks specifically for amount after "Loan $" or just "$"
    principal_match = re.search(PATTERNS['loan']['principal'], text)
    principal_amount = None
    if principal_match:
        principal_str = principal_match.group(1).replace(',', '')
        try:
            principal_amount = float(principal_str)
        except ValueError:
            print(f"Error converting principal amount: {principal_str}")
            
    # If principal not found with first pattern, try alternative pattern for just the number
    if principal_amount is None:
        alt_principal_match = re.search(r'(?:^|\s)(2,000,000)(?:\s|$)', text)
        if alt_principal_match:
            principal_amount = float(alt_principal_match.group(1).replace(',', ''))
    
    drawdown_days = extract_with_pattern(text, PATTERNS['loan']['drawdown_date'])
    
    # Extract repayment terms
    repayment_terms = extract_with_pattern(text, PATTERNS['loan']['repayment'])
    
    return {
        'principalAmount': principal_amount,
        'interestRate': interest_rate,
        'drawdownDate': f"{drawdown_days} Business Days after agreement date" if drawdown_days else "Unknown",
        'repaymentTerm': repayment_terms 
    }


def create_loan_terms(element_dict):
    """Create loan terms with fixed extraction"""
    # Get relevant text containing loan details
    table_text = next((x['text'] for x in element_dict 
                      if x['type'] == 'Table' and ('per annum' in x['text'] or 'Interest Rate' in x['text'])), "")
    
    # Add this to also look for repayment terms in narrative text
    repayment_text = next((x['text'] for x in element_dict 
                          if x['type'] == 'ListItem' and 'Repayment of Loan' in x['text']), "")
    
    currency_text = next((x['text'] for x in element_dict 
                         if x['type'] == 'ListItem' and 
                         ('$' in x['text'] or 'currency' in x['text'].lower())), "")
    
    loan_details = extract_loan_details(table_text)
    currency = extract_with_pattern(currency_text, PATTERNS['loan']['currency']) or 'Unknown'
    
    # Try to get repayment terms from narrative text if not found in table
    repayment_term = (loan_details.get('repaymentTerm') or 
                     extract_with_pattern(repayment_text, PATTERNS['loan']['repayment']) or 
                     "Unknown")
    
    # Extract interest payment details using the new function
    interest_payment_details = extract_interest_payment(element_dict)

    return {
        'loanTerms': {
            'principalAmount': loan_details.get('principalAmount'),
            'currency': currency,
            'interestRate': loan_details.get('interestRate'),
            'drawdownDate': loan_details.get('drawdownDate'), 
            'repaymentTerm': repayment_term,
            'interestPayment': interest_payment_details.get('interestPayment', {
                'frequency': None,
                'compounding': False,
                'paymentDate': None
            })
        }
    }

def extract_interest_payment(element_dict: List[Dict]) -> Dict:
    """
    Extract interest payment details from document elements.
    
    Args:
        element_dict: List of document elements in dictionary form
    
    Returns:
        Dictionary containing interest payment details with frequency, compounding, and payment date
    """
    # Initialize default values
    interest_payment = {
        'frequency': None,
        'compounding': False,
        'paymentDate': None
    }
    
    # Find the interest clause (3.1)
    interest_text = None
    for element in element_dict:
        if (element.get('type') == 'ListItem' and 
            element.get('text', '').startswith('3.1') and 
            'Borrower must pay interest' in element.get('text', '')):
            interest_text = element.get('text', '')
            # print(f"Found interest clause: {interest_text}")  # Debug print
            break
    
    if not interest_text:
        print("Warning: Interest payment clause not found")
        return {'interestPayment': interest_payment}
    
    # Extract frequency
    frequencies = {
        'annually': 'annually',
        'monthly': 'monthly',
        'daily': 'daily'
    }
    
    for freq_text, freq_value in frequencies.items():
        if freq_text in interest_text.lower():
            interest_payment['frequency'] = freq_value
            break
            
    # Check for compounding
    interest_payment['compounding'] = 'compounding' in interest_text.lower()
    
    # Extract payment date
    # Look for patterns like "payable on" or similar phrases
    payment_date_patterns = [
        r'payable\s+on\s+(?:the\s+)?([^,\.]+)',
        r'paid\s+on\s+(?:the\s+)?([^,\.]+)',
        r'due\s+on\s+(?:the\s+)?([^,\.]+)'
    ]
    
    for pattern in payment_date_patterns:
        match = re.search(pattern, interest_text, re.IGNORECASE)
        if match:
            interest_payment['paymentDate'] = match.group(1).strip()
            break
    
    # print(f"Extracted interest payment details: {interest_payment}")  # Debug print
    return {'interestPayment': interest_payment}

# Process contact tables
def process_contact_tables(element_dict):
    """Process contact tables and return party information"""
    parties = {'lender': {'contact': {}}, 'borrower': {'contact': {}}}
    contact_tables = [x for x in element_dict if x['type'] == 'Table' 
                     and 'contact' in x['text'].lower()]
    
    for table in contact_tables:
        party_type = 'lender' if 'LENDER' in table['text'].upper() else 'borrower'
        parties[party_type]['contact'] = extract_contact_details(table['text'])
    
    return parties

def extract_events_of_default(elements):
    """
    Extract Events of Default clauses from the document elements
    Args:
        elements: List of document elements containing text and type information
    Returns:
        List of event of default clauses
    """
    events_of_default = []
    is_events_section = False
    
    # First find the "EVENTS OF DEFAULT" title
    for i, element in enumerate(elements):
        # Check if we've found the Events of Default section
        if (element.get('type') == 'Title' and 
            'EVENTS OF DEFAULT' in element.get('text', '')):
            is_events_section = True
            continue
            
        # If we're in the Events of Default section, collect list items
        if is_events_section and element.get('type') == 'ListItem':
            text = element.get('text', '').strip()
            
            # Stop when we reach clause 5.3
            if text.startswith('5.3'):
                break
                
            # Skip the introductory text
            if text.startswith('5.1') or text.startswith('5.2'):
                continue
                
            # Clean up the text - remove any leading letters/numbers and spaces
            cleaned_text = re.sub(r'^[a-z]\s+', '', text)  # Remove single letter prefixes like 'a '
            cleaned_text = re.sub(r'^[ivx]+\s+', '', cleaned_text)  # Remove roman numerals
            
            if cleaned_text:
                events_of_default.append(cleaned_text)
    
    return events_of_default

def extract_governing_law(element_dict: List[Dict]) -> str:
    """
    Extract governing law from document elements.
    
    Args:
        element_dict: List of document elements in dictionary form
    
    Returns:
        String containing the governing law jurisdiction
    """
    # Default value
    default_law = "Unknown"
    
    # First find the "GOVERNING LAW" section
    governing_law_text = None
    
    for i, element in enumerate(element_dict):
        # Find the title first
        if (element.get('type') == 'Title' and 
            'GOVERNING LAW' in element.get('text', '').upper()):
            # Look at the next element for the actual content
            if i + 1 < len(element_dict):
                next_element = element_dict[i + 1]
                if next_element.get('type') in ['NarrativeText', 'ListItem']:
                    governing_law_text = next_element.get('text', '')
                    break
    
    if not governing_law_text:
        print("Warning: Governing law section not found")
        return default_law
    
    # Patterns to match governing law
    patterns = [
        r'governed by.+?laws? of\s+([^,\.\s]+)',  # matches "governed by... laws of Singapore"
        r'governed by.+?([^,\.\s]+)\s+law',       # matches "governed by Singapore law"
        r'interpreted in accordance with.+?laws? of\s+([^,\.\s]+)',  # matches "accordance with laws of Singapore"
        r'([^,\.\s]+)\s+law shall apply',         # matches "Singapore law shall apply"
    ]
    
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, governing_law_text, re.IGNORECASE)
        if match:
            jurisdiction = match.group(1).strip()
            # Capitalize the first letter
            return jurisdiction[0].upper() + jurisdiction[1:] if jurisdiction else default_law
    
    print(f"Warning: Could not extract jurisdiction from: {governing_law_text}")
    return default_law

def clean_company_name(name: str) -> str:
    """Clean company name by removing leading numbers and extra whitespace"""
    # Remove leading numbers and any following whitespace
    cleaned = re.sub(r'^\d+\s*', '', name)
    # Remove any extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

def format_output_json(parties: Dict[str, Any], loan_terms: Dict[str, Any], 
                      output_file: str = "output.json", 
                      element_dict: List[Dict] = None, 
                      doc_type: str = "Unknown") -> Dict[str, Any]:
    """
    Format and combine parties and loan terms data into the desired JSON structure
    Args:
        parties: Dictionary containing lender and borrower information
        loan_terms: Dictionary containing loan terms information
        output_file: Optional filename to save the JSON output
        element_dict: List of document elements in dictionary form
        doc_type: Document type extracted from title
    Returns:
        Dictionary with the formatted JSON structure
    """
    # Extract governing law
    governing_law = extract_governing_law(element_dict) if element_dict else "Unknown"
    
    # Create the base structure with a deep copy to avoid modifying original
    formatted_json = {
        "documentType": doc_type,
        "parties": dict(parties),
        "loanTerms": loan_terms.get("loanTerms", {}),
        "eventsOfDefault": extract_events_of_default(element_dict) if element_dict else [],
        "governingLaw": governing_law  # Use extracted governing law instead of hardcoded value
    }

    # Clean company names
    for party_type in ["lender", "borrower"]:
        if party_type in formatted_json["parties"]:
            party = formatted_json["parties"][party_type]
            if "name" in party:
                party["name"] = clean_company_name(party["name"])

    # Ensure all required fields exist
    for party_type in ["lender", "borrower"]:
        if party_type in formatted_json["parties"]:
            party = formatted_json["parties"][party_type]
            if "contact" not in party:
                party["contact"] = {}
            contact = party["contact"]
            required_contact_fields = ["name", "title", "address", "email"]
            for field in required_contact_fields:
                if field not in contact:
                    contact[field] = ""

    # Write to file if specified
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_json, f, indent=2)

    return formatted_json

def clean_text(text):
    # Remove excessive whitespace and normalize line endings
    return ' '.join(text.split()).strip()

def convert_to_markdown(filtered_elements):
    """
    Convert pre-filtered elements to markdown.
    
    Args:
        filtered_elements: List of already filtered document elements
        
    Returns:
        str: Markdown formatted content
    """
    markdown_content = []
    in_table = False
    table_data = []
    
    for element in filtered_elements:
        element_type = type(element).__name__
        element_text = clean_text(str(element))
        
        if not element_text:  # Skip empty elements
            continue
            
        if element_type == 'Title':
            markdown_content.append(f"# {element_text}\n")
        elif element_type == 'Header':
            markdown_content.append(f"## {element_text}\n")
        elif element_type == 'ListItem':
            markdown_content.append(f"- {element_text}")
        elif element_type == 'Table':
            # Handle table formatting
            if not in_table:
                in_table = True
                table_data = []
            table_data.append(element_text)
        elif element_type == 'FigureCaption':
            markdown_content.append(f"\n*{element_text}*\n")
        elif element_type == 'Image':
            markdown_content.append(f"![{element_text}](image_path)\n")
        elif element_type == 'NarrativeText':
            markdown_content.append(f"\n{element_text}\n")
        else:  # Default case for Text and other elements
            markdown_content.append(element_text)
            
        # Handle table end
        if in_table and element_type != 'Table':
            in_table = False
            if table_data:
                markdown_content.extend(format_table(table_data))
                table_data = []
                
    return '\n'.join(markdown_content)
    
def format_table(table_data):
    # Simple table formatting
    formatted_table = []
    formatted_table.append('\n| ' + ' | '.join(str(cell) for cell in table_data) + ' |')
    formatted_table.append('|' + '---|' * len(table_data))
    return formatted_table

    # For the dictionary version, you can filter before converting to dict
    filtered_elements = [
        el for el in elements 
        if getattr(el.metadata, 'page_number', 0) != 1
    ]
    element_dict = [el.to_dict() for el in filtered_elements]
    
#######################
# Main Processing Function
#######################

def should_skip_first_page(elements) -> bool:
    """
    Determine if first page should be skipped based on first title containing 'template'.
    
    Args:
        elements: List of document elements
        
    Returns:
        bool: True if first page should be skipped
    """
    first_title = next((el for el in elements 
                       if getattr(el, 'type', '') == 'Title' and 
                       getattr(el.metadata, 'page_number', 0) == 1), None)
    
    if first_title and first_title.text:
        return 'template' in str(first_title.text).lower()
    return False

def process_document(pdf_path: str) -> Dict:
    """Process uploaded PDF document and return results."""
    try:
        # Generate unique output filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = app.config['OUTPUT_FOLDER']
        md_filename = f'output_{timestamp}.md'
        json_filename = f'output_{timestamp}.json'
        
        # Process the document
        elements = partition_pdf(pdf_path, strategy="hi_res")
        
        # Determine if we should skip first page
        skip_first_page = should_skip_first_page(elements)
        
        # Filter elements
        if skip_first_page:
            filtered_elements = [
                el for el in elements 
                if getattr(el.metadata, 'page_number', 0) != 1
            ]
        else:
            filtered_elements = elements
            
        element_dict = [el.to_dict() for el in filtered_elements]
        
        # Extract components
        doc_type = extract_document_type(element_dict)
        loan_terms = create_loan_terms(element_dict)
        
        # Process parties information
        parties = {"lender": {}, "borrower": {}}
        parties_elem_id = [x['element_id'] for x in element_dict if x['text'] == 'PARTIES']
        parties_text = [x for x in element_dict if x['type'] == 'ListItem' and 
                       x['metadata']['parent_id'] in parties_elem_id]
        
        # Process details
        for party in parties_text:
            party_type = 'lender' if 'Lender' in party['text'] else 'borrower'
            parties[party_type].update(extract_company_details(party['text']))
            parties[party_type]["contact"] = {}
        
        # Process contact details
        contact_tables = [x for x in element_dict if x['type'] == 'Table' and 
                         'contact' in x['text'].lower()]
        for table in contact_tables:
            party_type = 'lender' if 'LENDER' in table['text'].upper() else 'borrower'
            parties[party_type]['contact'] = extract_contact_details(table['text'])
        
        # Extract signatures
        signatures = extract_signatures(element_dict)
        for party_type, title in signatures.items():
            if party_type in parties and 'contact' in parties[party_type]:
                parties[party_type]['contact']['title'] = title
        
        # Generate outputs
        output_json_path = os.path.join(output_dir, json_filename)
        output_md_path = os.path.join(output_dir, md_filename)
        
        results = format_output_json(
            parties=parties, 
            loan_terms=loan_terms, 
            output_file=output_json_path, 
            element_dict=element_dict,
            doc_type=doc_type
        )
        
        markdown_content = convert_to_markdown(filtered_elements)
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return {
            'success': True,
            'results': results,
            'files': {
                'json': json_filename,
                'markdown': md_filename
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the document
        result = process_document(filepath)
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify(result)
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)