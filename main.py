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




PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
API_KEY = os.getenv('API_KEY')
FACEBOOK_API = "https://graph.facebook.com/v20.0/me/messages?access_token="+PAGE_ACCESS_TOKEN
AI_TOKEN = os.getenv("AI_TOKEN")


chat = ChatTogether(
    together_api_key=AI_TOKEN,
    model="meta-llama/Llama-3-70b-chat-hf",
)


# Templating system for ShopX's chatbot context
COMPANY_CONTEXT = """
حولنا
مرحبًا بك في Shopxps.net، الوجهة الموثوقة لتجربة تسوق إلكتروني آمنة ومريحة. نحن هنا لتلبية احتياجاتك من خلال منصة متطورة تجمع بين المنتجات المحلية والعروض العالمية، وتهدف لتقديم تجربة تسوق ممتعة وسلسة للسوق الفلسطيني في الضفة الغربية.

رؤيتنا
في Shopxps.net، نسعى لجعل تجربة التسوق أكثر من مجرد شراء منتجات. نحن نؤمن بأنها رحلة فريدة، تبدأ من التصفح حتى استلام المنتج بأمان. هدفنا هو إنشاء سوق رقمي يدعم الأعمال المحلية ويوفر مجموعة واسعة من المنتجات التي تلبي احتياجات وتفضيلات المجتمع الفلسطيني.

لماذا اختيار Shopxps.net؟
- **الأمان والموثوقية:** نحمي معلوماتك الشخصية ونضمن أن بياناتك ومعاملاتك آمنة باستخدام أحدث معايير الأمان.
- **التركيز المحلي:** فخورون بتقديم منتجات تعكس احتياجات السوق المحلي مع توفير تشكيلة عالمية من المنتجات التي تناسب نمط حياتك.
- **واجهة استخدام سهلة:** منصة مصممة بعناية لتسهيل تجربة التسوق من البداية إلى النهاية.
- **الابتكار المستمر:** نسعى باستمرار لتطوير خدماتنا وتقديم حلول مبتكرة تجعل التسوق أكثر سلاسة وراحة.

سياسة الخصوصية
نحن في ShopXPS.net ملتزمون بحماية خصوصيتك وضمان أمان معلوماتك الشخصية. يتم جمع بياناتك الشخصية فقط لتنفيذ طلباتك وتحسين تجربتك معنا. لا نشارك معلوماتك مع أطراف خارجية إلا في حدود الضرورة لتنفيذ طلباتك، مثل شركات الشحن أو مزودي خدمات الدفع. نحافظ على سرية معلوماتك ونطبق أعلى معايير الأمان لحمايتها.

نحن هنا لتقديم أفضل خدمة تسوق إلكتروني ممكنة، ونسعى دائمًا إلى تحسين تجربتك. لا تتردد في التواصل معنا لأي استفسارات أو طلبات، فنحن نسعد بخدمتك.

شكرًا لاختيارك Shopxps.net. لنتسوق ونتواصل وننجح معًا.
"""


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
    data = await request.json()
    try:
        # Extract message and sender information
        message = data['entry'][0]['messaging'][0]['message']
        sender_id = data['entry'][0]['messaging'][0]['sender']['id']
        user_message = message.get('text', '').lower()

        # Template for prompt generation
        prompt_template = f"""
        You are a professional and friendly chatbot that speaks Arabic and represents ShopX, an e-commerce platform.
        
        The user asked: {user_message}
        Provide a professional, helpful, and informative response in Arabic based on the following context:

        {COMPANY_CONTEXT}
        """

        # Stream and compile the response from the chatbot
        chatbot_response = ""
        for message_chunk in chat.stream(prompt_template):
            chatbot_response += message_chunk.content

        # Send the response to the Facebook Messenger API
        response_body = {
            "recipient": {"id": sender_id},
            "message": {"text": chatbot_response}
        }
        response = requests.post(FACEBOOK_API, json=response_body).json()

        return JSONResponse(content=response)

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