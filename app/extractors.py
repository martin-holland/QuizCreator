"""
Document extraction services for URLs, PDFs, Word docs, and Images
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import os
import re
from urllib.parse import urlparse

class DocumentExtractor:
    """Base extractor class"""
    
    @staticmethod
    def extract(text: str) -> str:
        """Extract text from content"""
        raise NotImplementedError

class URLExtractor(DocumentExtractor):
    """Extract text from URLs using multiple methods"""
    
    @staticmethod
    def extract(url: str) -> Dict[str, str]:
        """Extract text from a URL using best available method"""
        try:
            # Normalize and validate URL
            url = URLExtractor._normalize_url(url)
            
            # Try Playwright first (handles JavaScript-rendered pages)
            try:
                return URLExtractor._extract_with_playwright(url)
            except Exception as playwright_error:
                # Fall back to requests + Trafilatura (better content extraction)
                try:
                    return URLExtractor._extract_with_trafilatura(url)
                except Exception as trafilatura_error:
                    # Final fallback to requests + BeautifulSoup
                    try:
                        return URLExtractor._extract_with_requests(url)
                    except Exception as requests_error:
                        # If all methods fail, raise with helpful message
                        raise ValueError(
                            f"Failed to extract content using all methods. "
                            f"Playwright error: {str(playwright_error)[:100]}. "
                            f"Trafilatura error: {str(trafilatura_error)[:100]}. "
                            f"Requests error: {str(requests_error)[:100]}"
                        )
        except Exception as e:
            raise ValueError(f"Failed to extract URL content: {str(e)}")
    
    @staticmethod
    def _extract_with_playwright(url: str) -> Dict[str, str]:
        """Extract content using Playwright (handles JavaScript)"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate and wait for content to load
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait a bit for any dynamic content
                page.wait_for_timeout(2000)
                
                # Get the rendered HTML
                html = page.content()
                
                # Get title
                title = page.title() or urlparse(url).netloc
                
                browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove non-content elements
                for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
                    element.decompose()
                
                # Extract main content
                main_content = None
                for selector in ['main', 'article', '[role="main"]', '.content', '#content', 'body']:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                content_element = main_content if main_content else soup.find('body') or soup
                text = content_element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if not text or len(text) < 50:
                    raise ValueError("Content too short after Playwright extraction")
                
                return {
                    'title': title,
                    'content': text,
                    'metadata': {
                        'url': url,
                        'method': 'playwright',
                        'content_length': len(text)
                    }
                }
        except ImportError:
            raise ValueError("Playwright is not installed. Install with: pip install playwright && playwright install chromium")
        except Exception as e:
            raise ValueError(f"Playwright extraction failed: {str(e)}")
    
    @staticmethod
    def _extract_with_trafilatura(url: str) -> Dict[str, str]:
        """Extract content using Trafilatura (excellent for article extraction)"""
        try:
            import trafilatura
            
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise ValueError("Trafilatura could not fetch URL")
            
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if not text or len(text.strip()) < 50:
                raise ValueError("Trafilatura extracted content is too short")
            
            # Get metadata
            metadata = trafilatura.extract_metadata(downloaded)
            title = metadata.title if metadata and metadata.title else urlparse(url).netloc
            
            return {
                'title': title,
                'content': text.strip(),
                'metadata': {
                    'url': url,
                    'method': 'trafilatura',
                    'content_length': len(text)
                }
            }
        except ImportError:
            raise ValueError("Trafilatura is not installed. Install with: pip install trafilatura")
        except Exception as e:
            raise ValueError(f"Trafilatura extraction failed: {str(e)}")
    
    @staticmethod
    def _extract_with_requests(url: str) -> Dict[str, str]:
        """Extract content using requests + BeautifulSoup (fallback)"""
        # Enhanced headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Create session to handle cookies and redirects
        session = requests.Session()
        session.max_redirects = 10
        
        # Make request
        response = session.get(
            url, 
            headers=headers, 
            timeout=30,
            allow_redirects=True,
            verify=True
        )
        response.raise_for_status()
        
        # Check if response is HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' not in content_type and 'text' not in content_type:
            raise ValueError(f"URL does not return HTML content. Content-Type: {content_type}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove non-content elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.content', '#content', 'body']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        content_element = main_content if main_content else soup.find('body') or soup
        text = content_element.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Get title
        title = None
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title.get('content').strip()
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
        if not title:
            parsed = urlparse(url)
            title = parsed.netloc or url
        
        if not text or len(text) < 50:
            raise ValueError("Extracted content is too short or empty")
        
        return {
            'title': title,
            'content': text,
            'metadata': {
                'url': url,
                'final_url': response.url,
                'status_code': response.status_code,
                'method': 'requests',
                'content_length': len(text)
            }
        }
    
    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize and validate URL"""
        url = url.strip()
        
        # Remove leading/trailing whitespace
        url = url.strip()
        
        # Check if it's a valid-looking URL
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Basic validation - check if it looks like a URL
        if not ('.' in url or url.startswith('http')):
            raise ValueError(f"'{url}' does not appear to be a valid URL. Please include the full URL (e.g., https://example.com)")
        
        # If URL doesn't start with http:// or https://, add https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.netloc or parsed.netloc == 'test' or len(parsed.netloc.split('.')) < 2:
            raise ValueError(f"Invalid URL format: '{url}'. Please provide a complete URL (e.g., https://www.example.com/page)")
        
        return url

class PDFExtractor(DocumentExtractor):
    """Extract text from PDF files"""
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, str]:
        """Extract text from a PDF file"""
        try:
            import PyPDF2
            
            text_parts = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_parts.append(page.extract_text())
            
            text = '\n\n'.join(text_parts)
            title = os.path.basename(file_path)
            
            return {
                'title': title,
                'content': text,
                'metadata': {'pages': num_pages, 'filename': title}
            }
        except ImportError:
            raise ValueError("PyPDF2 is not installed. Install it with: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"Failed to extract PDF: {str(e)}")

class WordExtractor(DocumentExtractor):
    """Extract text from Word documents"""
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, str]:
        """Extract text from a Word document"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            text = '\n\n'.join(text_parts)
            title = os.path.basename(file_path)
            
            return {
                'title': title,
                'content': text,
                'metadata': {'paragraphs': len(text_parts), 'filename': title}
            }
        except ImportError:
            raise ValueError("python-docx is not installed. Install it with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to extract Word document: {str(e)}")

class ImageExtractor(DocumentExtractor):
    """Extract text from images using OCR"""
    
    @staticmethod
    def _check_tesseract_installed() -> bool:
        """Check if Tesseract OCR is installed and accessible"""
        try:
            import pytesseract
            # Try to get tesseract version - this will raise an exception if not found
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, str]:
        """Extract text from an image file using Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ValueError(
                "pytesseract or Pillow is not installed. Install with: pip install pytesseract Pillow"
            )
        
        # Check if Tesseract is installed before attempting extraction
        if not ImageExtractor._check_tesseract_installed():
            import platform
            system = platform.system().lower()
            
            install_instructions = {
                'darwin': (
                    "Tesseract OCR is not installed. To install on macOS:\n"
                    "  brew install tesseract\n"
                    "If you don't have Homebrew: https://brew.sh"
                ),
                'linux': (
                    "Tesseract OCR is not installed. To install on Linux:\n"
                    "  sudo apt-get install tesseract-ocr\n"
                    "Or for other distributions, check: https://github.com/tesseract-ocr/tesseract"
                ),
                'windows': (
                    "Tesseract OCR is not installed. To install on Windows:\n"
                    "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                    "2. Install the executable\n"
                    "3. Add Tesseract to your PATH, or set the path in code:\n"
                    "   pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'"
                )
            }
            
            message = install_instructions.get(system, 
                "Tesseract OCR is not installed. Please install Tesseract OCR for your operating system.\n"
                "See: https://github.com/tesseract-ocr/tesseract"
            )
            
            raise ValueError(f"Tesseract OCR is not installed or not in PATH.\n\n{message}")
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            title = os.path.basename(file_path)
            
            if not text or len(text.strip()) < 10:
                raise ValueError(
                    "Could not extract text from image. The image may not contain readable text, "
                    "or the text quality may be too low for OCR."
                )
            
            return {
                'title': title,
                'content': text,
                'metadata': {'filename': title, 'original_filename': os.path.basename(file_path), 'image_size': image.size}
            }
        except ValueError as ve:
            # Re-raise ValueError as-is (these are our custom error messages)
            raise
        except Exception as e:
            error_msg = str(e)
            if 'tesseract' in error_msg.lower() or 'not found' in error_msg.lower():
                raise ValueError(
                    f"Tesseract OCR error: {error_msg}\n\n"
                    "Please ensure Tesseract is installed and in your PATH. "
                    "See README.md for installation instructions."
                )
            raise ValueError(f"Failed to extract text from image: {str(e)}")

def extract_from_source(source_type: str, source_input: str) -> Dict[str, str]:
    """
    Unified extraction function
    source_type: 'url', 'pdf', 'word', 'image'
    source_input: URL string or file path
    """
    extractors = {
        'url': URLExtractor,
        'pdf': PDFExtractor,
        'word': WordExtractor,
        'image': ImageExtractor
    }
    
    if source_type not in extractors:
        raise ValueError(f"Unsupported source type: {source_type}")
    
    extractor = extractors[source_type]()
    return extractor.extract(source_input)

