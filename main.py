from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from cachetools import cached, TTLCache
import re
import requests
from langchain_together import ChatTogether

app = FastAPI()

BASE_URL = "https://fawri-f7ab5f0e45b8.herokuapp.com/api"
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
API_KEY = os.getenv('API_KEY')
FACEBOOK_API = "https://graph.facebook.com/v20.0/me/messages?access_token="+PAGE_ACCESS_TOKEN
AI_TOKEN = os.getenv("AI_TOKEN")

chat = ChatTogether(
    together_api_key=AI_TOKEN,
    model="meta-llama/Llama-3-70b-chat-hf",
)
cache = TTLCache(maxsize=100, ttl=300)

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

@app.get("/webhook", response_class=PlainTextResponse)
async def fbverify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_challenge:
        if hub_verify_token != VERIFY_TOKEN:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
        return hub_challenge
    return "Hello world"



@app.post("/webhook")
async def handle_webhook(request: Request):
    print('hello from the webhook')
    try:
        data = await request.json()
        if 'entry' in data:
            for entry in data['entry']:
                for event in entry['messaging']:
                    sender_id = event['sender']['id']
                    if 'message' in event:
                        message_text = event['message']['text'].lower()

                        # Handle user input
                        product_id = extract_product_id(message_text)

                        try:
                            items_data = await fetch_all_available_items()
                            if "error" in items_data:
                                product_info = "Error fetching items data."
                            else:
                                product_info = ""
                                if product_id is not None:
                                    product = next((item for item in items_data['products'] if item['id'] == product_id), None)
                                    if product:
                                        product_info = format_product_info(product)
                                    else:
                                        product_info = f"Product with ID {product_id} not found."
                                elif "total items" in message_text:
                                    product_info = f"The total number of items is {items_data['total_items']}."
                                else:
                                    product_info = "\n".join([f"Product ID: {item['id']}, Name: {item['title']}, Price: {item['price']}" for item in items_data['products']])

                        except Exception as e:
                            print(f"Error fetching items data: {e}")
                            product_info = "Error fetching items data."

                        question_with_context = f"Question: {message_text}\n\n{product_info}"

                        # Get the chatbot response
                        chatbot_response = ""
                        for m in chat.stream(question_with_context):
                            chatbot_response += m.content

                        # Combine chatbot response and product information
                        final_response = f"{chatbot_response}\n\n{product_info}"

                        return JSONResponse(content={"message": final_response})

    except KeyError as e:
        print(f"Key error: {e}")
        raise HTTPException(status_code=400, detail="Bad request")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"status": "ok"}


# async def handle_message(event):
#     sender_id = event['sender']['id']
#     message_text = event['message'].get('text')
    
#     # Send the message to your Streamlit chatbot and get the response
#     response = await get_chatbot_response(message_text)
    
#     # Send the response back to Messenger
#     await send_message(sender_id, response)

# async def fetch_chatbot_response(message):
#     async with aiohttp.ClientSession() as session:
#         async with session.post('http://localhost:8501', json={"question": message}) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 return data['response']
#             return "Error in fetching chatbot response"

# async def get_chatbot_response(message):
#     response = await fetch_chatbot_response(message)
#     return response

# async def send_message(recipient_id, message_text):
#     headers = {
#         "Content-Type": "application/json"
#     }
#     data = {
#         "recipient": {"id": recipient_id},
#         "message": {"text": message_text}
#     }
#     url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, headers=headers, json=data) as response:
#             if response.status != 200:
#                 print("Failed to send message:", response.status, await response.text())

