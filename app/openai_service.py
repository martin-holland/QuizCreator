"""
OpenAI service for generating quiz questions
"""
import requests
import json
import os
import time
from typing import List, Dict, Optional

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.api_url = OPENAI_API_URL
        self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency, can be changed to gpt-4o if needed
    
    @staticmethod
    def _smart_content_selection(content: str, max_chars: int) -> str:
        """
        Intelligently select content to preserve quality while managing token usage.
        Uses a strategy that captures beginning, middle, and end portions.
        
        Args:
            content: Full content string
            max_chars: Maximum characters to return
            
        Returns:
            Selected content string that preserves key information
        """
        content = content.strip()
        
        # If content is already short enough, return it all
        if len(content) <= max_chars:
            return content
        
        # Strategy: Take beginning (40%), middle sample (20%), and end (40%)
        # This preserves context from intro, middle, and conclusion
        # Reserve space for separators (about 50 chars total)
        separator_length = 50
        available_chars = max_chars - separator_length
        
        begin_chars = int(available_chars * 0.4)
        middle_chars = int(available_chars * 0.2)
        end_chars = int(available_chars * 0.4)
        
        # Get beginning portion
        beginning = content[:begin_chars]
        
        # Get middle portion (sample from middle of document)
        middle_start = len(content) // 2 - middle_chars // 2
        middle_end = middle_start + middle_chars
        middle = content[max(0, middle_start):middle_end]
        
        # Get end portion
        ending = content[-end_chars:] if end_chars > 0 else ""
        
        # Combine with separators to indicate gaps
        selected = f"{beginning}\n\n[... content continues ...]\n\n{middle}\n\n[... content continues ...]\n\n{ending}"
        
        # Trim if still too long (shouldn't happen with proper calculation)
        if len(selected) > max_chars:
            # Trim from the end if needed
            selected = selected[:max_chars]
        
        return selected
    
    def generate_content(self, prompt: str, model: Optional[str] = None, max_retries: int = 3) -> str:
        """
        Generate content from OpenAI API with retry logic for rate limits
        
        Args:
            prompt: The prompt to send to OpenAI
            model: Optional model override
            max_retries: Maximum number of retry attempts for rate limit errors
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            "model": model or self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60  # OpenAI can take longer
                )
                
                # Handle rate limit errors (429) with retry
                if response.status_code == 429:
                    # Get retry-after header if available
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        # Exponential backoff: 2^attempt seconds
                        wait_time = 2 ** attempt
                    
                    # Try to get error message from response
                    error_msg = 'Rate limit exceeded'
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Rate limit exceeded')
                    except:
                        pass
                    
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Last attempt failed
                        raise ValueError(
                            f"OpenAI API rate limit exceeded after {max_retries} attempts. "
                            f"Please wait a few minutes and try again. "
                            f"Error: {error_msg}"
                        )
                
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    error_msg = data['error'].get('message', 'Unknown OpenAI API error')
                    error_type = data['error'].get('type', '')
                    
                    # Don't retry on non-rate-limit errors
                    if error_type == 'rate_limit_error' and attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"Rate limit error (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    
                    raise ValueError(f"OpenAI API error: {error_msg}")
                
                # Extract text from response
                if 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    
                    # Check finish reason
                    finish_reason = choice.get('finish_reason', '')
                    if finish_reason == 'content_filter':
                        raise ValueError("OpenAI blocked the request due to content filters")
                    elif finish_reason == 'length':
                        raise ValueError("Response was cut off due to token limit")
                    
                    message = choice.get('message', {})
                    text = message.get('content', '')
                    if not text:
                        raise ValueError("OpenAI API returned empty text in response")
                    return text
                
                # If we get here, the response format is unexpected
                raise ValueError(f"Unexpected response format from OpenAI API. Response keys: {list(data.keys())}")
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    # Retry on rate limit
                    wait_time = 2 ** attempt
                    print(f"HTTP 429 error (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                last_error = e
            except requests.RequestException as e:
                # For network errors, retry with backoff
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Request error (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                last_error = e
            except json.JSONDecodeError as e:
                # Don't retry JSON decode errors
                raise ValueError(f"Failed to parse OpenAI API response: {str(e)}")
        
        # If we get here, all retries failed
        if last_error:
            if isinstance(last_error, requests.exceptions.HTTPError) and last_error.response.status_code == 429:
                raise ValueError(
                    f"OpenAI API rate limit exceeded after {max_retries} attempts. "
                    f"This usually means:\n"
                    f"1. You've made too many requests too quickly\n"
                    f"2. Your API key has hit its rate limit (check your OpenAI dashboard)\n"
                    f"3. You're on a free tier with lower limits\n\n"
                    f"Please wait a few minutes before trying again, or upgrade your OpenAI plan for higher rate limits."
                )
            raise ValueError(f"Failed to call OpenAI API after {max_retries} attempts: {str(last_error)}")
        
        raise ValueError(f"Failed to call OpenAI API after {max_retries} attempts")
    
    def generate_questions(self, content: str, num_questions: int = 5, is_url: bool = False) -> List[Dict]:
        """
        Generate quiz questions from content
        Returns list of questions with answers
        
        Args:
            content: Text content
            num_questions: Number of questions to generate
            is_url: Not used for OpenAI (always False since we extract content first)
        """
        # Regular text content
        prompt = f"""You are a quiz question generator. Based on the following content, generate exactly {num_questions} multiple-choice questions.

For each question, you must provide:
- 1 question text
- 6 answer options total:
  * 4 correct answers (each worth +0.25 points)
  * 2 incorrect answers (each worth -0.5 points)

Format your response as JSON with this exact structure:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "answers": [
        {{"text": "Answer 1", "is_correct": true, "points": 0.25}},
        {{"text": "Answer 2", "is_correct": true, "points": 0.25}},
        {{"text": "Answer 3", "is_correct": true, "points": 0.25}},
        {{"text": "Answer 4", "is_correct": true, "points": 0.25}},
        {{"text": "Answer 5", "is_correct": false, "points": -0.5}},
        {{"text": "Answer 6", "is_correct": false, "points": -0.5}}
      ]
    }}
  ]
}}

Content to generate questions from:
{self._smart_content_selection(content, 6000)}

IMPORTANT: Return ONLY valid JSON, no additional text, no markdown formatting, no code blocks. Just the raw JSON object."""

        try:
            response_text = self.generate_content(prompt)
            
            # Check if response is empty
            if not response_text or not response_text.strip():
                raise ValueError("OpenAI API returned an empty response")
            
            # Try to extract JSON from response
            # Sometimes OpenAI wraps JSON in markdown code blocks
            original_response = response_text
            
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end == -1:
                    response_text = response_text[start:].strip()
                else:
                    response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end == -1:
                    response_text = response_text[start:].strip()
                else:
                    response_text = response_text[start:end].strip()
            
            # Try to find JSON object in the response
            # Look for first { and last }
            if '{' in response_text:
                start_idx = response_text.find('{')
                # Find the matching closing brace
                brace_count = 0
                end_idx = -1
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx]
            
            # Remove any leading/trailing whitespace
            response_text = response_text.strip()
            
            # If still empty after processing, use original
            if not response_text:
                response_text = original_response.strip()
            
            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                # Try to find and extract just the JSON part more aggressively
                json_start = -1
                json_end = -1
                
                # Find first {
                for i, char in enumerate(response_text):
                    if char == '{':
                        json_start = i
                        break
                
                if json_start >= 0:
                    # Find matching closing }
                    brace_count = 0
                    for i in range(json_start, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > json_start:
                        try:
                            json_text = response_text[json_start:json_end]
                            data = json.loads(json_text)
                        except json.JSONDecodeError:
                            # Still failed, raise with details
                            raise ValueError(
                                f"Failed to parse JSON from OpenAI response. "
                                f"Response preview (first 1000 chars): {response_text[:1000]}. "
                                f"Error: {str(e)}"
                            )
                    else:
                        raise ValueError(
                            f"Could not find complete JSON object in response. "
                            f"Response preview: {response_text[:500]}. Error: {str(e)}"
                        )
                else:
                    # No JSON found at all
                    raise ValueError(
                        f"No JSON found in OpenAI response. "
                        f"Response preview: {response_text[:500]}. "
                        f"Full response length: {len(response_text)}. "
                        f"Error: {str(e)}"
                    )
            
            if 'questions' not in data:
                raise ValueError("Invalid response format: missing 'questions' key")
            
            questions = data['questions']
            
            # Validate and format questions
            formatted_questions = []
            for q in questions:
                if 'question' not in q or 'answers' not in q:
                    continue
                
                # Ensure answers have IDs
                answers = []
                for idx, answer in enumerate(q['answers']):
                    answer['id'] = idx + 1
                    answers.append(answer)
                
                formatted_questions.append({
                    'question_text': q['question'],
                    'answers': answers
                })
            
            return formatted_questions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to generate questions: {str(e)}")
    
    def generate_topic_name(self, content: str) -> Dict[str, str]:
        """
        Generate a topic name and description from content using AI
        Analyzes the content to identify the main topic/theme
        
        Returns:
            Dict with 'title' and 'description' keys
        """
        # Use smart content selection for topic analysis
        # Takes beginning, middle sample, and end to preserve context
        # Increased to 3000 chars for better topic identification while managing tokens
        content_sample = self._smart_content_selection(content, 3000)
        
        prompt = f"""Analyze the following content and generate a concise, descriptive topic name and brief description.

The topic name should:
- Be 3-8 words long
- Accurately reflect the main subject or theme
- Be clear and specific (not generic like "General Information")
- Use title case (e.g., "Type Safety and Type Inference")

The description should:
- Be 1-2 sentences summarizing the key concepts
- Be helpful for understanding what questions will be generated from this topic

Content sample:
{content_sample}

Return your response as JSON with this exact structure:
{{
  "title": "Topic Name Here",
  "description": "Brief description of the topic and key concepts covered."
}}

IMPORTANT: Return ONLY valid JSON, no additional text, no markdown formatting, no code blocks."""

        try:
            response_text = self.generate_content(prompt)
            
            # Extract JSON (same logic as generate_questions)
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end == -1:
                    response_text = response_text[start:].strip()
                else:
                    response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end == -1:
                    response_text = response_text[start:].strip()
                else:
                    response_text = response_text[start:end].strip()
            
            # Find JSON object
            if '{' in response_text:
                start_idx = response_text.find('{')
                brace_count = 0
                end_idx = -1
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx]
            
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate and return
            title = data.get('title', 'Generated Topic').strip()
            description = data.get('description', '').strip()
            
            # Fallback if title is too generic or empty
            if not title or len(title) < 3:
                title = 'Generated Topic'
            
            return {
                'title': title,
                'description': description
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to a default topic name
            return {
                'title': 'Generated Topic',
                'description': 'Questions generated from source content.'
            }
        except Exception as e:
            # Fallback on any error
            return {
                'title': 'Generated Topic',
                'description': 'Questions generated from source content.'
            }

# Global instance
openai_service = OpenAIService()

