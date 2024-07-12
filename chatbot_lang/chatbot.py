from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
import streamlit as st
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from cachetools import cached, TTLCache
import re

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://fawri-f7ab5f0e45b8.herokuapp.com/api"

# Initialize cache (TTL in seconds)
cache = TTLCache(maxsize=100, ttl=300)

# Function to fetch all available items handling pagination
@cached(cache)
async def fetch_all_available_items():
    page = 1
    all_products = []
    total_items = 0

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(f"{BASE_URL}/getAvailableItems?api_key={API_KEY}&page={page}") as response:
                if response.status == 200:
                    data = await response.json()
                    all_products.extend(data['items'])
                    total_items = data['total_items']
                    if page >= len(data['pagination']):
                        break
                    page += 1
                else:
                    return {"error": "Failed to fetch data"}

    return {"products": all_products, "total_items": total_items}

# Prompt Template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are FawriBot, an intelligent assistant for Fawri, an e-commerce platform. You have comprehensive knowledge of the e-commerce database, including products, customers, and orders. Your purpose is to assist with inquiries related to the e-commerce system. Please provide accurate and relevant information for any e-commerce-related questions you receive."),
        ("user", "Question: {question}")
    ]
)

st.title("Fawri Chatbot")
input_text = st.text_input("Ask me a question!")

# Initialize the LLM
llm = Ollama(model="llama2")
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

def extract_product_id(question):
    # Use regex to find the first sequence of digits in the question
    match = re.search(r'\b\d+\b', question)
    if match:
        return int(match.group())
    return None

# Function to format the product information
def format_product_info(product):
    product_info = (f"Hello! As FawriBot, I'm here to help you with your inquiry. "
                    f"The product ID you provided is indeed for a luxury item from the brand {product.get('brand', 'N/A')}. "
                    f"The name of this product is \"{product['title']}\" and its current price is {product['price']}.\n\n"
                    f"Here's some additional information about this product:\n\n"
                    f"Name: {product['title']}\n"
                    f"Brand: {product.get('brand', 'N/A')}\n"
                    f"Product ID: {product['id']}\n"
                    f"Size: {product.get('size', 'N/A')}\n"
                    f"Weight: {product.get('weight', 'N/A')}\n"
                    f"Material: {product.get('material', 'N/A')}\n"
                    f"Color: {product.get('color', 'N/A')}\n"
                    f"![Product Image]({product.get('thumbnail', '')})")
    return product_info

# Handle user input
if input_text:
    async def main():
        # Fetch all available items
        items_data = await fetch_all_available_items()
        
        # Process and filter the data based on the user's question
        if "error" not in items_data:
            question_lower = input_text.lower()
            product_id = extract_product_id(question_lower)
            product_info = ""
            if product_id is not None:
                product = next((item for item in items_data['products'] if item['id'] == product_id), None)
                if product:
                    product_info = format_product_info(product)
                else:
                    product_info = f"Product with ID {product_id} not found."
            elif "total items" in question_lower:
                product_info = f"The total number of items is {items_data['total_items']}."
            else:
                product_info = "\n".join([f"Product ID: {item['id']}, Name: {item['title']}, Price: {item['price']}" for item in items_data['products']])
            question_with_context = f"Question: {input_text}\n\n{product_info}"
        else:
            question_with_context = input_text
        
        # Get the chatbot response
        response = chain.invoke({"question": question_with_context})
        st.write(response)
        # Display product image if available
        if product_id is not None and product:
            st.image(product.get('thumbnail', ''))

    # Run the async main function
    asyncio.run(main())
