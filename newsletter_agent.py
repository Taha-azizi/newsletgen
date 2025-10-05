"""
TechCrunch AI & Startup Newsletter Generator
A simple agentic framework using Ollama's web search and web fetch APIs
"""

from ollama import Client
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import os
from dotenv import load_dotenv

load_dotenv() 


# Configuration
MODEL = 'gpt-oss:20b'
TECHCRUNCH_DOMAIN = 'techcrunch.com'

# Setup Ollama API key
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
if not OLLAMA_API_KEY:
    print("WARNING: OLLAMA_API_KEY not found in environment variables")
    print("Please set your API key:")
    print("   1. Get your API key from: https://ollama.com/settings/keys")
    print("   2. Set env variable- i.e: in PowerShell: $env:OLLAMA_API_KEY='your_api_key'")
    raise ValueError("OLLAMA_API_KEY environment variable is required")

# Initialize Ollama client with API key
client = Client()


def create_search_agent(query, context=""):
    """
    Simple search agent that uses web_search and web_fetch
    """
    messages = [
        {
            'role': 'system',
            'content': 'You are a tech news analyst. Focus on finding breakthrough news about AI and technology startups from TechCrunch.'
        },
        {
            'role': 'user',
            'content': f"{context}\n\n{query}" if context else query
        }
    ]
    
    print(f"\nQuery: {query}")
    
    conversation_history = []
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.chat(
            model=MODEL,
            messages=messages,
            tools=[
                {
                    'type': 'function',
                    'function': {
                        'name': 'web_search',
                        'description': 'Search the web for information',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'query': {
                                    'type': 'string',
                                    'description': 'Search query'
                                }
                            },
                            'required': ['query']
                        }
                    }
                },
                {
                    'type': 'function',
                    'function': {
                        'name': 'web_fetch',
                        'description': 'Fetch content from a specific URL',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'url': {
                                    'type': 'string',
                                    'description': 'URL to fetch'
                                }
                            },
                            'required': ['url']
                        }
                    }
                }
            ],
            options={'temperature': 0.7}
        )
        
        if hasattr(response, 'message') and hasattr(response.message, 'content') and response.message.content:
            print(f"Response: {response.message.content[:200]}...")
            conversation_history.append(response.message.content)
        
        messages.append(response.message)
        
        if hasattr(response.message, 'tool_calls') and response.message.tool_calls:
            print(f"Using tools: {[tc.function.name for tc in response.message.tool_calls]}")
            
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                args = tool_call.function.arguments
                
                try:
                    if tool_name == 'web_search':
                        print(f"Searching: {args.get('query', '')}")
                        result = client.web_search(query=args['query'])
                        print(f"Found {len(result.get('results', []))} results")
                    elif tool_name == 'web_fetch':
                        print(f"   Fetching: {args.get('url', '')}")
                        result = client.web_fetch(url=args['url'])
                        print(f"Fetched content")
                    else:
                        result = {'error': f'Unknown tool: {tool_name}'}
                    
                    # Truncate for context limits
                    result_str = str(result)[:8000]
                    
                    messages.append({
                        'role': 'tool',
                        'content': result_str
                    })
                    
                except Exception as e:
                    print(f"Tool error: {str(e)}")
                    messages.append({
                        'role': 'tool',
                        'content': f'Error: {str(e)}'
                    })
        else:
            # No more tool calls, we're done
            break
    
    final_content = response.message.content if hasattr(response.message, 'content') else ""
    return final_content, conversation_history


def gather_techcrunch_news():
    """
    Step 1: Search for recent TechCrunch AI and startup news
    """
    print("\n" + "="*60)
    print("GATHERING TECHCRUNCH NEWS")
    print("="*60)
    
    # Get date range for last week
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    query = f"site:techcrunch.com artificial intelligence startups latest news"
    
    result, history = create_search_agent(
        query,
        context="Find the most important AI and startup news from TechCrunch in the last week. Focus on breakthrough announcements, funding rounds, and major product launches."
    )
    
    return result


def analyze_and_rank_news(news_data):
    """
    Step 2: Have the AI analyze and identify the most important stories
    """
    print("\n" + "="*60)
    print("ANALYZING & RANKING NEWS")
    print("="*60)
    
    query = """Based on the news you found, identify the TOP 5 most important and breakthrough stories.
    
    For each story, provide:
    1. Title
    2. Brief summary (2-3 sentences)
    3. Why it's important
    4. Source URL
    
    Focus on: Major funding announcements, breakthrough AI technologies, significant partnerships, and disruptive startups."""
    
    result, history = create_search_agent(query, context=news_data)
    
    return result


def create_detailed_summaries(ranked_news):
    """
    Step 3: Create detailed summaries of top stories
    """
    print("\n" + "="*60)
    print("CREATING DETAILED SUMMARIES")
    print("="*60)
    
    query = """For each of the top stories you identified, create a detailed summary (4-5 sentences) that includes:
    - What happened
    - Who is involved
    - Why it matters for the AI and startup ecosystem
    - Potential impact
    
    Format each story clearly with the title, URL, and detailed summary."""
    
    result, history = create_search_agent(query, context=ranked_news)
    
    return result


def generate_pdf_report(content):
    """
    Generate a PDF report from the newsletter content
    """
    print("\n" + "="*60)
    print("📄 GENERATING PDF REPORT")
    print("="*60)
    
    filename = f"techcrunch_ai_newsletter_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor="#1B1B1B",
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor="#1B1B1B",
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=10
    )
    
    # Add title and date
    elements.append(Paragraph("TechCrunch AI & Startup Newsletter", title_style))
    today = datetime.now().strftime('%B %d, %Y')
    elements.append(Paragraph(f"Weekly Report - {today}", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Process content and handle markdown
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if not para.strip():
            continue
            
        # Clean up markdown formatting
        text = para.strip()
        # Remove markdown headers
        text = text.replace('###', '').replace('##', '').replace('#', '')
        # Remove markdown bold/italic
        text = text.replace('**', '').replace('*', '')
        # Convert markdown links to plain text
        text = text.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        
        # Determine style based on content
        style = body_style
        if any(text.lower().startswith(h) for h in ['title:', 'source:', 'why it']):
            style = heading_style
            
        # Handle bullet points
        if text.startswith('- '):
            text = '• ' + text[2:]
            text = text.replace('\n- ', '\n• ')
        
        # Add paragraph with proper style
        elements.append(Paragraph(text, style))
        
    # Build PDF
    doc.build(elements)
    print(f"PDF report generated: {filename}")
    return filename


def main():
    """
    Main execution pipeline
    """
    print("\n" + "="*70)
    print("TECHCRUNCH AI & STARTUP NEWSLETTER GENERATOR")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Model: {MODEL}")
    print(f"Source: TechCrunch.com")
    print(f"API Key: {'Set' if OLLAMA_API_KEY else 'Missing'}")
    print("="*70)
    
    try:
        # Step 1: Gather news
        news_data = gather_techcrunch_news()
        
        # Step 2: Analyze and rank
        ranked_news = analyze_and_rank_news(news_data)
        
        # Step 3: Create detailed summaries
        detailed_summaries = create_detailed_summaries(ranked_news)
        
        # Step 4: Generate PDF
        pdf_file = generate_pdf_report(detailed_summaries)
        
        print("\n" + "="*70)
        print("NEWSLETTER GENERATION COMPLETE!")
        print("="*70)
        print(f"Report saved as: {pdf_file}")
        
        return pdf_file
        
    except Exception as e:
        print(f"\n Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Run the newsletter generator
    main()