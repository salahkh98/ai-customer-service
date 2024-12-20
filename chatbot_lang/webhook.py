# import os
# import logging
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from fastapi import FastAPI, Query, HTTPException
# load_dotenv()

# app = FastAPI()
# PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
# VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

# class Entry(BaseModel):
#     id: str
#     time: int
#     messaging: list

# class WebhookEvent(BaseModel):
#     object: str
#     entry: list[Entry]

# @app.get("/webhook")
# async def verify_webhook(hub_mode: str = Query(..., alias="hub.mode"), hub_challenge: str = Query(..., alias="hub.challenge"), hub_verify_token: str = Query(..., alias="hub.verify.token")):
#     logging.info(f"Received webhook verification request: mode={hub_mode}, challenge={hub_challenge}, verify_token={hub_verify_token}")
#     if hub_verify_token == VERIFY_TOKEN:
#         return hub_challenge
#     else:
#         raise HTTPException(status_code=403, detail="Verification token mismatch")

# @app.post("/webhook")
# async def handle_webhook(event: WebhookEvent):
#     for entry in event.entry:
#         for message in entry.messaging:
#             print(message)
#     return {"status": "ok"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# # @app.get('/webhook')
# # async def verify_token(hub_mode: str, hub_challenge: str, hub_verify_token: str):
# #     if hub_verify_token == VERIFY_TOKEN:
# #         return hub_challenge
# #     raise HTTPException(status_code=403, detail="Verification token mismatch")

# # @app.post('/webhook')
# # async def webhook(event: WebhookEvent):
# #     for entry in event.entry:
# #         for messaging_event in entry['messaging']:
# #             if 'message' in messaging_event:
# #                 await handle_message(messaging_event)
# #     return "OK"

# # async def handle_message(event):
# #     sender_id = event['sender']['id']
# #     message_text = event['message'].get('text')
    
# #     # Send the message to your Streamlit chatbot and get the response
# #     response = await get_chatbot_response(message_text)
    
# #     # Send the response back to Messenger
# #     await send_message(sender_id, response)

# # async def fetch_chatbot_response(message):
# #     async with aiohttp.ClientSession() as session:
# #         async with session.post('http://localhost:8501', json={"question": message}) as response:
# #             if response.status == 200:
# #                 data = await response.json()
# #                 return data['response']
# #             return "Error in fetching chatbot response"

# # async def get_chatbot_response(message):
# #     response = await fetch_chatbot_response(message)
# #     return response

# # async def send_message(recipient_id, message_text):
# #     headers = {
# #         "Content-Type": "application/json"
# #     }
# #     data = {
# #         "recipient": {"id": recipient_id},
# #         "message": {"text": message_text}
# #     }
# #     url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
# #     async with aiohttp.ClientSession() as session:
# #         async with session.post(url, headers=headers, json=data) as response:
# #             if response.status != 200:
# #                 print("Failed to send message:", response.status, await response.text())

