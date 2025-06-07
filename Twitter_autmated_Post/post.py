import os
import sys
import tweepy
import logging
import requests
import argparse
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Twitter API credentials
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OpenAI API credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def authenticate_twitter() -> Optional[tweepy.Client]:
    """Authenticate with Twitter API."""
    try:
        logger.info("Authenticating with Twitter")
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        logger.info("Twitter authentication successful")
        return client
    except Exception as e:
        logger.error(f"Twitter authentication failed: {e}")
        return None

def upload_media(image_path: str) -> Optional[str]:
    """Upload media to Twitter."""
    try:
        logger.info(f"Uploading image: {image_path}")
        auth = tweepy.OAuth1UserHandler(
            CONSUMER_KEY, 
            CONSUMER_SECRET,
            ACCESS_TOKEN, 
            ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        media = api.media_upload(filename=image_path)
        logger.info("Media upload successful")
        return media.media_id_string
    except Exception as e:
        logger.error(f"Media upload failed: {e}")
        return None

def post_tweet(client: tweepy.Client, text: str, media_id: Optional[str] = None) -> bool:
    """Post a tweet to Twitter with optional media."""
    try:
        logger.info("Posting tweet")
        
        # Create tweet parameters
        tweet_params = {"text": text}
        if media_id:
            tweet_params["media_ids"] = [media_id]
            
        response = client.create_tweet(**tweet_params)
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
        logger.info(f"Tweet posted successfully: {tweet_url}")
        return True
    except Exception as e:
        logger.error(f"Tweet posting failed: {e}")
        return False

def setup_openai():
    """Set up OpenAI client."""
    try:
        # Create OpenAI client with API key
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client set up successfully")
        return client
    except Exception as e:
        logger.error(f"OpenAI setup failed: {e}")
        return None

def research_topic(topic: str, tweet_length: int = 255) -> str:
    """Research a topic using OpenAI and generate tweet content."""
    try:
        logger.info(f"Researching topic: {topic}")
        
        prompt = f"""
        Research the topic: "{topic}" and create an engaging tweet about it.
        The tweet should be informative, accurate, and attention-grabbing.
        Include relevant hashtags if appropriate.
        Keep the tweet under {tweet_length} characters.
        """
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Generate content using the new API format
        response = client.chat.completions.create(
            model="gpt-4",  # or whatever model you prefer
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, engaging tweets based on research."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        tweet_content = response.choices[0].message.content.strip()
        
        # Ensure the tweet isn't too long
        if len(tweet_content) > tweet_length:
            logger.warning(f"Generated tweet exceeds {tweet_length} characters, truncating...")
            tweet_content = tweet_content[:tweet_length]
        
        logger.info(f"Tweet content generated: {tweet_content}")
        return tweet_content
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        return f"Check out this information about {topic}! #research #information"

def validate_image(image_path: str) -> bool:
    """Validate that the image exists and is a valid image file."""
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False
        
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    file_ext = os.path.splitext(image_path)[1].lower()
    
    if file_ext not in valid_extensions:
        logger.error(f"Invalid image format: {file_ext}. Must be one of {valid_extensions}")
        return False
        
    # Check file size (Twitter has a limit of 5MB for images)
    file_size = os.path.getsize(image_path) / (1024 * 1024)  # Convert to MB
    if file_size > 5:
        logger.error(f"Image size too large: {file_size:.2f}MB. Maximum allowed is 5MB.")
        return False
        
    return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AI-powered Twitter posting tool')
    parser.add_argument('--topic', '-t', type=str, help='Topic to research and post about')
    parser.add_argument('--image', '-i', type=str, help='Path to image file to include with tweet')
    parser.add_argument('--manual', '-m', action='store_true', help='Enable manual mode to input tweet text')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Check Twitter API credentials
    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        logger.error("Twitter API credentials not found in environment variables")
        print("Please set the following environment variables:\n"
              "TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET\n"
              "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET")
        sys.exit(1)
    
    # Authenticate with Twitter
    client = authenticate_twitter()
    if not client:
        logger.error("Twitter authentication failed")
        sys.exit(1)
    
    # Determine tweet content
    tweet_text = ""
    if args.manual:
        # Manual mode
        tweet_text = input("Enter tweet text: ")
        if not tweet_text:
            logger.error("Tweet text is required in manual mode")
            sys.exit(1)
    elif args.topic:
        # Check OpenAI API key
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment variables")
            print("Please set the OPENAI_API_KEY environment variable")
            sys.exit(1)
            
        # No need to explicitly set up OpenAI client here as we create it in the research_topic function
            
        # Research topic and generate tweet
        tweet_text = research_topic(args.topic)
    else:
        logger.error("Either --topic or --manual flag must be specified")
        sys.exit(1)
    
    # Check tweet length
    if len(tweet_text) > 280:  # Twitter's character limit
        logger.error(f"Tweet text exceeds the 280-character limit: {len(tweet_text)} characters")
        print("Error: Tweet text must not exceed 280 characters.")
        sys.exit(1)
    
    # Handle image if provided
    media_id = None
    if args.image:
        if not validate_image(args.image):
            sys.exit(1)
        
        media_id = upload_media(args.image)
        if not media_id:
            logger.error("Media upload failed")
            sys.exit(1)
    
    # Post tweet
    success = post_tweet(client, tweet_text, media_id)
    if not success:
        logger.error("Tweet posting failed")
        sys.exit(1)
    
    logger.info("Tweet successfully posted")
    print("Tweet successfully posted!")

if __name__ == "__main__":
    main()
