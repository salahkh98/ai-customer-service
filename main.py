import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether
from langchain.agents import ChatPromptTemplate, ChatTogether, create_structured_chat_agent
import os
app = FastAPI()




PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
API_KEY = os.getenv('API_KEY')
FACEBOOK_API = "https://graph.facebook.com/v20.0/me/messages?access_token="+PAGE_ACCESS_TOKEN
AI_TOKEN = os.getenv("AI_TOKEN")

chat = ChatTogether(together_api_key=AI_TOKEN, model="meta-llama/Llama-3-70b-chat-hf")

# Memory to store conversation context
memory = ConversationBufferMemory()

# Facebook API URL
FACEBOOK_API = "https://graph.facebook.com/v12.0/me/messages?access_token=YOUR_PAGE_ACCESS_TOKEN"

# Delivery and Shipping Info
delivery_regions = {
    'Ramallah': 20, 'نابلس': 20, 'جنين': 20, 'طولكرم': 20, 'سلفيت': 20,
    'طوباس': 20, 'أريحا': 20, 'الخليل': 20, 'بيت لحم': 20, 'القدس': 35,
    'غرب القدس': 35, 'الداخل': 60, 'جنوب الداخل': 60, 'قرى رام الله': 20
}

# Memory to store conversation context
memory = ConversationBufferMemory()

# Initialize the chat model
chat = ChatTogether(
    together_api_key=AI_TOKEN,
    model="meta-llama/Llama-3-70b-chat-hf",
)

# Define the prompt template
prompt_template = ChatPromptTemplate.from_template("""
    You are a highly accurate customer service chatbot for ShopXPS, an e-commerce platform based in Palestine. 
    You assist customers with product inquiries, order tracking, and delivery details. 
    Be sure to respond accurately, provide useful details, and handle all conversations in Arabic.

    Delivery times are typically between 10-14 business days. 
    Delivery regions and fees are as follows: {regions}.
    
    Current conversation history:
    {history}
    
    User's input:
    {input}
    
    Your response in Arabic:
""")

# Convert delivery info to a string for the prompt
delivery_info = ", ".join([f"{region}: {fee} شيكل" for region, fee in delivery_regions.items()])

# Create the structured chat agent
agent_chain = create_structured_chat_agent(
    chat_model=chat,
    prompt_template=prompt_template
)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        message_data = data['entry'][0]['messaging'][0]
        sender_id = message_data['sender']['id']
        user_message = message_data.get('message', {}).get('text', '').strip().lower()

        if not user_message:
            raise ValueError("Empty message received")

        # Load conversation memory and prepare context
        context = memory.load_memory()

        # Prepare prompt with memory and current input
        prompt = prompt_template.format_prompt(
            history=context, 
            input=user_message, 
            regions=delivery_info
        )
        
        # Generate response from the LLM agent
        response_message = agent_chain.run(input=user_message)

        # Send the generated message back to the user on Facebook Messenger
        send_message_to_facebook(sender_id, response_message)

        # Save conversation to memory for context in future messages
        memory.save_context({"input": user_message}, {"output": response_message})

        return JSONResponse(content={"status": "message sent"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def send_message_to_facebook(recipient_id: str, message_text: str):
    """Sends a response to a user on Facebook Messenger."""
    try:
        response_body = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        response = requests.post(FACEBOOK_API, json=response_body)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to send message")


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