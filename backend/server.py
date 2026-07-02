from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import hmac
import random
import re
import csv
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

JWT_SECRET = os.environ["JWT_SECRET"]
DEMO_OTP = os.environ.get("DEMO_OTP", "123456")
JWT_ALGORITHM = "HS256"

STORE_INFO = {
    "name": "BARNAWAL PROVISION STORE",
    "contacts": ["8381869505", "8858351010"],
    "primary_whatsapp": "918381869505",
    "secondary_whatsapp": "918858351010",
    "primary_whatsapp_link": "https://wa.me/918381869505",
    "secondary_whatsapp_link": "https://wa.me/918858351010",
    "delivery_time": "30 Minutes",
    "delivery_message": "Delivery in 30 Minutes",
    "payment_method": "Cash on Delivery",
    "payment_note": "Pay when your order is delivered.",
    "min_order_amount": 200,
    "delivery_fee": 20,
}

CATEGORY_IMAGES = {
    "Face Cream": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/rfx3oqpm_Screenshot%202026-06-25%20at%206.55.35%E2%80%AFPM.png",
    "Tea": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/cpl8s31x_Screenshot%202026-06-25%20at%207.04.04%E2%80%AFPM.png",
    "Jam & Spread": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/fydrkpc2_Screenshot%202026-06-25%20at%206.57.45%E2%80%AFPM.png",
    "Pickles": "https://images.unsplash.com/photo-1635349121894-810bc93d8531?auto=format&fit=crop&w=900&q=80",
    "Masala": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=900&q=80",
    "Oats": "https://images.unsplash.com/photo-1614961233913-a5113a4a34ed?auto=format&fit=crop&w=900&q=80",
    "Salt": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/7nth68qm_Screenshot%202026-06-25%20at%207.02.31%E2%80%AFPM.png",
    "Hair Oils": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/5vv2am1m_Screenshot%202026-06-25%20at%206.56.15%E2%80%AFPM.png",
    "Shampoo & Hair Care": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/sokkfbzt_Screenshot%202026-06-25%20at%207.02.54%E2%80%AFPM.png",
    "Toothpaste": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/b2sn7j3q_Screenshot%202026-06-25%20at%207.04.31%E2%80%AFPM.png",
    "Oral Care": "https://images.unsplash.com/photo-1606811971618-4486d14f3f99?auto=format&fit=crop&w=900&q=80",
    "Baby Care": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/5tupu61t_WhatsApp%20Image%202026-06-25%20at%203.38.56%20PM.jpeg",
    "Health Drinks": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/jfth2sz8_Screenshot%202026-06-25%20at%206.56.46%E2%80%AFPM.png",
    "Baby Food": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=900&q=80",
    "Breakfast": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/yxi1aehb_Screenshot%202026-06-25%20at%207.24.22%E2%80%AFPM.png",
    "Murabba": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/jjg9p1av_Screenshot%202026-06-25%20at%206.59.20%E2%80%AFPM.png",
    "Candy": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/d20mgz6b_Screenshot%202026-06-25%20at%206.53.12%E2%80%AFPM.png",
    "Chutney": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/1qrvwqjj_Screenshot%202026-06-25%20at%206.52.21%E2%80%AFPM.png",
    "Instant Food": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?auto=format&fit=crop&w=900&q=80",
    "Coffee": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/4iqt9kec_Screenshot%202026-06-25%20at%206.52.42%E2%80%AFPM.png",
    "Biscuits": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/h2xmlasi_WhatsApp%20Image%202026-06-25%20at%203.38.55%20PM.jpeg",
    "Flour & Millets": "https://images.unsplash.com/photo-1627485937980-221c88ac04f9?auto=format&fit=crop&w=900&q=80",
    "Sugar & Sweeteners": "https://images.unsplash.com/photo-1581441363689-1f3c3c414635?auto=format&fit=crop&w=900&q=80",
    "Cooking Oils": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/lf61j2um_Screenshot%202026-06-25%20at%206.53.36%E2%80%AFPM.png",
    "Fasting Items": "https://images.unsplash.com/photo-1607349913338-fca6f7fc42d0?auto=format&fit=crop&w=900&q=80",
    "Besan & Sattu": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/isa8ss96_WhatsApp%20Image%202026-06-25%20at%203.38.55%20PM%20%281%29.jpeg",
    "Dry Fruits & Seeds": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/zm4v3ylh_Screenshot%202026-06-25%20at%206.54.58%E2%80%AFPM.png",
    "Whole Spices": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/uqswtxjb_Screenshot%202026-06-25%20at%207.03.24%E2%80%AFPM.png",
    "Dalia & Grains": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=900&q=80",
    "Pulses & Lentils": "https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=900&q=80",
    "Pujan Materials": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/y6244cgj_Screenshot%202026-06-25%20at%207.25.29%E2%80%AFPM.png",
    "Puja Essentials": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/y6244cgj_Screenshot%202026-06-25%20at%207.25.29%E2%80%AFPM.png",
    "Chocolates & Sweets": "https://customer-assets.emergentagent.com/job_quick-order-hub-37/artifacts/9egdcmf7_Screenshot%202026-06-25%20at%206.51.49%E2%80%AFPM.png",
    "Ayurveda & Juices": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=900&q=80",
}

HINDI_CATEGORY_NAMES = {
    "Face Cream": "फेस क्रीम", "Tea": "चाय", "Jam & Spread": "जैम और स्प्रेड",
    "Pickles": "अचार", "Masala": "मसाला", "Oats": "ओट्स", "Salt": "नमक",
    "Hair Oils": "हेयर ऑयल", "Shampoo & Hair Care": "शैम्पू और हेयर केयर",
    "Toothpaste": "टूथपेस्ट", "Oral Care": "ओरल केयर", "Baby Care": "बेबी केयर",
    "Health Drinks": "हेल्थ ड्रिंक्स", "Baby Food": "बेबी फूड", "Breakfast": "नाश्ता",
    "Murabba": "मुरब्बा", "Candy": "कैंडी", "Chutney": "चटनी", "Instant Food": "इंस्टेंट फूड",
    "Coffee": "कॉफी", "Biscuits": "बिस्कुट",
    "Flour & Millets": "आटा एवं अनाज", "Sugar & Sweeteners": "चीनी एवं मिठास",
    "Cooking Oils": "तेल", "Fasting Items": "व्रत सामग्री", "Besan & Sattu": "बेसन एवं सत्तू",
    "Dry Fruits & Seeds": "सूखा मेवा", "Whole Spices": "खड़े मसाले", "Dalia & Grains": "दलिया एवं अनाज",
    "Pulses & Lentils": "दालें", "Pujan Materials": "पूजन सामग्री", "Puja Essentials": "पूजा आवश्यक सामग्री",
    "Chocolates & Sweets": "चॉकलेट एवं मिठाई", "Ayurveda & Juices": "आयुर्वेद एवं जूस",
}

CATALOG = {
    "Face Cream": {
        "sub": "Skin Care",
        "items": {
            "Glow & Lovely": ["Small Pack", "Medium Pack", "Large Pack"],
            "Vicco Turmeric Cream": ["Small", "Medium", "Large"],
            "Boroplus": ["Small", "Medium", "Large"],
            "Boroline": ["Small", "Medium", "Large"],
            "Joy Almond Cream": ["Small", "Medium", "Large"],
            "Joy Fruit Cream": ["Small", "Medium", "Large"],
            "Nivea Cream": ["Small", "Medium", "Large"],
            "Pond's Cream": ["Small", "Medium", "Large"],
            "White Tone Cream": ["Small", "Medium", "Large"],
        },
    },
    "Tea": {
        "sub": "Beverages",
        "items": {
            "Tata Tea Premium": ["100g", "250g", "500g", "1kg"],
            "Tata Tea Gold": ["250g", "500g"],
            "Tata Tea Agni": ["250g", "500g", "1kg"],
            "Tata Tea Elaichi": ["250g"],
            "Lipton Tea Taza": ["100g", "250g", "500g", "1kg"],
            "Red Label Tea": ["100g", "250g", "500g", "1kg"],
            "Chaivik Elaichi Tea": ["250g"],
            "Wagh Bakri Premium Leaf Tea": ["250g", "1kg"],
            "Vikram Premium Tea": ["250g"],
            "Lipton Green Tea": ["25g", "50g", "100g", "250g"],
            "Mohini Evergreen Tea": ["250g"],
            "Elaichi Tea": ["250g"],
        },
    },
    "Jam & Spread": {
        "sub": "Spreads",
        "items": {
            "Kissan Mixed Fruit Jam": ["90g", "200g", "500g", "900g"],
            "Kissan Mango Jam": ["500g"], "Kissan Pineapple Jam": ["500g"],
            "Kissan Orange Jam": ["500g"], "Peanut Spread Cream": ["200g", "500g"],
            "Peanut Butter": ["200g", "500g"], "Gulkand": ["200g", "500g"],
        },
    },
    "Pickles": {
        "sub": "Indian Pickles",
        "items": {
            "Red Chilli Pickle": ["200g", "500g", "1kg"], "Green Chilli Pickle": ["200g", "500g", "1kg"],
            "Pachmel Mix Pickle": ["200g", "500g", "1kg"], "Mango Pickle": ["200g", "500g", "1kg"],
            "Stuffed Red Chilli Pickle": ["200g", "500g", "1kg"], "Karela Pickle": ["200g"],
            "Jackfruit Pickle": ["200g"], "Mushroom Pickle": ["400g"], "Amla Pickle": ["400g"],
            "Ginger Pickle": ["200g"], "Garlic Pickle": ["200g", "500g"], "Mix Panchmel Pickle": ["200g", "500g", "1kg"],
        },
    },
    "Masala": {
        "sub": "Spices",
        "items": {
            "Sabzi Masala": ["50g", "100g", "200g"], "Garam Masala": ["50g", "100g", "200g"],
            "Meat Masala": ["50g", "100g", "200g"], "Red Chilli Powder": ["50g", "100g", "200g", "500g"],
            "Turmeric Powder": ["50g", "100g", "200g", "500g"], "Coriander Powder": ["100g", "200g", "500g"],
            "Kashmiri Mirch": ["50g", "100g"], "Deggi Mirch": ["50g", "100g"],
            "Kasoori Methi": ["25g", "50g", "100g"], "Jaljeera Powder": ["50g", "100g"],
            "Chaat Masala": ["100g"], "Rajma Masala": ["100g"], "Chhola Masala": ["50g", "100g"],
            "Chana Masala": ["50g", "100g"], "Kitchen King": ["50g", "100g"],
            "Sambhar Masala": ["50g", "100g"], "Pav Bhaji Masala": ["50g", "100g"],
            "Sonth Dry Ginger Powder": ["50g", "100g"], "Roasted Jeera Powder": ["100g"],
            "Jeera Powder": ["50g", "100g", "200g", "500g"], "Kali Mirch Powder": ["50g", "100g", "200g", "500g"],
        },
    },
    "Oats": {"sub": "Breakfast", "items": {"Plain Oats": ["200g", "400g", "1kg"], "Masala Oats": ["40g", "200g", "500g"], "Quaker Oats": ["200g", "400g", "1kg"], "Saffola Oats": ["40g", "200g", "500g"]}},
    "Salt": {"sub": "Essentials", "items": {"Olive Salt": ["1kg"], "Sendha Salt": ["1kg"], "Black Salt": ["200g"], "Tata Salt": ["1kg"], "Sajjikhar Salt": ["200g"], "Nausadar Salt": ["100g"], "Khapadia Salt": ["200g"], "Muli Khar Salt": ["200g"], "Kalaunji Salt": ["100g"]}},
    "Hair Oils": {"sub": "Hair Care", "items": {"Himgange Tel": ["100ml", "200ml", "500ml"], "Navratna Oil": ["50ml", "100ml", "200ml"], "Rahat Rooh Tel": ["100ml"], "Roghan Shukun Oil": ["50ml", "100ml", "200ml"], "Roghan Dimag Roshan": ["80ml", "150ml"], "Dudhi Tel": ["100ml"], "Tulsi Tel": ["100ml"], "Ghrit Kumari Tel": ["100ml"], "Kesh Kanti Tel": ["100ml"], "Almond Drops Bajaj": ["100ml", "200ml"], "Jasmine Tel Parachute": ["100ml", "200ml"], "Figaro Olive Oil": ["100ml", "200ml"], "Dabur Amla Hair Oil": ["50ml", "100ml", "200ml"], "Amla Hair Oil": ["50ml", "100ml", "200ml"], "Chameli Tel": ["100ml"], "Sarson Amla Tel": ["100ml"], "Coconut Oil": ["100ml", "200ml", "500ml"], "Hair Care Oil": ["100ml"], "Keo Karpin Oil": ["100ml"], "7 Oil": ["100ml"], "Dhool Tel": ["100ml"], "Dithori Tel": ["100ml"], "Erand Oil": ["100ml"], "Mahua Oil": ["100ml"], "Peppermint Oil": ["150ml"], "Kunjab Oil": ["80ml", "150ml"], "Patanjali Dant Kanti Oil": ["50ml", "100ml", "200ml"]}},
    "Shampoo & Hair Care": {"sub": "Hair Wash", "items": {"Patanjali Kesh Kanti Natural Shampoo": ["150ml"], "Patanjali Kesh Kanti Aloe Vera Shampoo": ["80ml"], "Patanjali Kesh Kanti Conditioner": ["80ml"], "Patanjali Kesh Kanti Silk & Shine": ["50ml"], "Vitamin Color Shampoo": ["80ml", "150ml", "320ml", "500ml"], "Vita Herbal Shampoo": ["80ml", "150ml"], "Kun Shampoo": ["80ml", "180ml", "320ml", "500ml"], "Sunsilk Premium": ["40ml", "80ml", "150ml"], "Sunsilk Pink": ["80ml", "180ml", "320ml", "500ml"], "Sunsilk Yellow": ["80ml", "180ml", "320ml", "500ml"], "Sunsilk Black": ["40ml", "80ml", "150ml", "320ml", "500ml"], "Sunsilk Hair Fall Rescue": ["40ml", "70ml"], "Head & Shoulders": ["80ml", "180ml", "320ml", "500ml", "1L"], "Dove Shampoo": ["180ml", "340ml"], "Dove Hair Fall Rescue": ["180ml"], "Dove Intense Repair": ["180ml"], "Dove Daily Shine": ["180ml"], "Clinic Plus": ["80ml", "175ml"], "Clinic Plus Strong & Long": ["80ml", "175ml"], "Pantene Hair Fall Control": ["80ml", "180ml"], "Pantene Advanced Hair Fall Solution": ["80ml", "180ml"], "Tresemme Keratin Smooth": ["185ml"], "Tresemme Hair Fall Defense": ["185ml"], "Herbal Shampoo": ["80ml", "150ml"], "Premium Hair Oil": ["80ml", "150ml"]}},
    "Toothpaste": {"sub": "Oral Care", "items": {"Babool Paste": ["40g", "80g", "150g"], "Dabur Red Paste": ["50g", "100g", "200g"], "Dabur Meswak Toothpaste": ["100g", "200g"], "Dabur Herbal Toothpaste": ["100g", "200g"], "Patanjali Dant Kanti Natural": ["50g", "100g", "200g"], "Patanjali Dant Kanti Advanced": ["100g", "200g"], "Patanjali Dant Kanti Medicated": ["100g", "200g"], "Patanjali Dant Kanti Junior": ["50g"], "Colgate Strong Teeth": ["100g", "200g"], "Colgate Max Fresh": ["80g", "150g"], "Colgate Visible White": ["100g"], "Colgate Active Salt": ["100g", "200g"], "Colgate Vedshakti": ["100g", "200g"], "Pepsodent Germicheck": ["100g", "200g"], "Pepsodent Expert Protection": ["100g", "200g"], "Closeup Red Hot": ["80g", "150g"], "Closeup Ever Fresh": ["80g", "150g"], "Sensodyne Rapid Relief": ["80g", "150g"], "Sensodyne Repair & Protect": ["70g", "100g"], "Sensodyne Fresh Mint": ["70g", "100g"], "Meswak Toothpaste": ["70g", "100g", "200g"], "Vicco Vajradanti": ["50g", "100g", "200g"], "Himalaya Complete Care": ["80g", "150g"], "Himalaya Sparkling White": ["80g", "150g"], "Oral-B Gum & Enamel Repair": ["75g", "150g"], "Neem Toothpaste": ["100g", "200g"], "Charcoal Toothpaste": ["100g", "200g"], "Herbal Toothpaste": ["100g", "200g"]}},
    "Oral Care": {"sub": "Dental Accessories", "items": {"Toothbrush Soft": ["1pc"], "Toothbrush Medium": ["1pc"], "Toothbrush Hard": ["1pc"], "Kids Toothbrush": ["1pc"], "Tongue Cleaner": ["1pc"], "Dental Floss": ["1pc"], "Mouthwash": ["100ml", "250ml", "500ml"]}},
    "Baby Care": {"sub": "Baby Essentials", "items": {"Johnson Baby Powder": ["100g"], "Johnson Baby Cream": ["50g"], "Johnson Baby Massage Oil": ["50ml", "100ml", "200ml"], "Himalaya Baby Powder": ["100g"], "Himalaya Baby Cream": ["50g"], "Dabur Lal Tail": ["100ml"], "Baby Shampoo": ["100ml"], "Baby Hair Oil": ["50ml", "100ml"], "Baby Wipes": ["1pack"], "Baby Cream": ["25g", "50g", "100g"], "Noorani Tel": ["25ml", "50ml", "100ml", "200ml"]}},
    "Health Drinks": {"sub": "Nutrition", "items": {"Bournvita": ["200g", "500g", "1kg"], "Horlicks Chocolate": ["500g", "1kg"], "Horlicks Plain": ["500g", "1kg"], "Complan Chocolate": ["500g", "1kg"], "Complan Kesar Badam": ["500g"], "Boost": ["200g", "500g", "1kg"], "ProteinX Vanilla": ["400g"], "ProteinX Chocolate": ["400g"]}},
    "Baby Food": {"sub": "Cerelac", "items": {"Cerelac 6 Months": ["300g"], "Cerelac 8 Months": ["300g"], "Cerelac 10 Months": ["300g"], "Cerelac 12 Months": ["300g"], "Cerelac 18 Months": ["300g"], "Cerelac 24 Months": ["300g"]}},
    "Breakfast": {"sub": "Cereals", "items": {"Kellogg's Chocos": ["200g", "500g"], "Kellogg's Cornflakes": ["200g", "500g"], "Cornflakes": ["200g", "500g"], "Kellogg's Muesli": ["500g"], "Yogabar Muesli": ["500g"]}},
    "Murabba": {"sub": "Traditional Sweets", "items": {"Amla Murabba": ["500g"], "Bel Murabba": ["500g"], "Bamboo Murabba": ["500g"], "Apple Murabba": ["500g"]}},
    "Candy": {"sub": "Sweets", "items": {"Amla Candy": ["200g"], "Bel Candy": ["200g"]}},
    "Chutney": {"sub": "Sauces", "items": {"Red Chilli Chutney": ["200g"], "Apple Chutney": ["200g"], "Amla Chutney": ["200g"], "Mango Chutney": ["200g"], "Garlic Chutney": ["200g"], "Schezwan Chutney": ["200g"]}},
    "Instant Food": {"sub": "Noodles", "items": {"Maggi": ["75g", "150g", "300g", "600g"], "Maggi Masala": ["1pack"], "Yippee Noodles Classic": ["70g"], "Yippee Noodles Magic Masala": ["70g"]}},
    "Coffee": {"sub": "Beverages", "items": {"Nescafe Classic": ["1g", "2.2g", "5g", "25g", "50g", "100g", "200g", "500g"], "Bru Coffee": ["50g", "100g"], "Tata Coffee": ["50g", "100g"]}},
    "Biscuits": {"sub": "Snacks", "items": {"Good Day Butter": ["1pack"], "Good Day Cashew": ["1pack"], "Good Day Pistachio": ["1pack"], "50-50": ["1pack"], "Monaco": ["1pack"], "Parle-G": ["1pack"], "Marie Gold": ["1pack"], "Biscutie": ["1pack"], "Nutri Choice": ["1pack"], "Hello": ["1pack"], "Tops Herb": ["1pack"], "Googly": ["1pack"], "Golmol": ["1pack"], "Timepass": ["1pack"], "Jadoo": ["1pack"], "Bourbon": ["1pack"], "Oreo": ["1pack"], "Hide & Seek": ["1pack"], "Krackjack": ["1pack"], "Milk Bikis": ["1pack"], "Treat": ["1pack"]}},
}

ADDITIONAL_CATALOG = {
    "Flour & Millets": {"sub": "Atta & Grains", "items": {"Ragi Flour": ["500g"], "Bajra Flour": ["500g"], "Jowar Flour": ["500g"], "Makka Flour": ["500g"], "Barley Flour": ["500g"], "Chana Flour": ["500g"], "Wheat Flour": ["5kg", "10kg"]}},
    "Sugar & Sweeteners": {"sub": "Sugar", "items": {"Sugar Loose": ["Loose"], "Sugar Packet": ["1kg", "5kg"]}},
    "Cooking Oils": {"sub": "Edible Oils", "items": {"Refined Soyabean Oil": ["750ml", "1L", "2L", "5L", "14L"], "Groundnut Oil": ["500ml", "900ml", "1L"], "Rice Bran Oil": ["1L"], "Sunflower Oil": ["1L"], "Saffola Blended Oil": ["1L", "2L", "5L"], "Mustard Oil": ["200ml", "500ml", "1L", "2L", "5L", "15L"]}},
    "Fasting Items": {"sub": "Vrat Samagri", "items": {"Singhada Flour": ["250g"], "Kuttu Flour": ["250g"]}},
    "Besan & Sattu": {"sub": "Gram Flour", "items": {"Chana Besan": ["500g", "Loose"], "Chana Sattu": ["250g", "500g"]}},
    "Dry Fruits & Seeds": {"sub": "Dry Fruits", "items": {"Gari": ["100g"], "Chohada": ["100g"], "Almonds": ["100g"], "Poppy Seeds": ["100g"], "Watermelon Seeds": ["100g"], "Muskmelon Seeds": ["100g"], "Cucumber Seeds": ["100g"], "Raisins": ["100g"], "Chaman Raisins": ["100g"], "Chironji": ["50g"], "Cashew Whole": ["100g"], "Cashew Broken": ["100g"], "Walnut": ["100g"], "Pistachio": ["100g"], "Pistachio Coco": ["100g"], "Munakka": ["100g"], "Fig": ["100g"]}},
    "Whole Spices": {"sub": "Khade Masale", "items": {"Badi Elaichi": ["50g"], "Dalchini": ["50g"], "Cloves": ["50g"], "Choti Elaichi": ["50g"], "Black Cumin": ["50g"], "Javitri": ["25g"], "Jaiphal": ["25g"], "Kababchini": ["25g"], "Star Anise": ["25g"], "Chhadila": ["25g"], "Sonth White": ["50g"], "Sonth Red": ["50g"], "Peepar": ["25g"], "Satavar": ["50g"], "Ratanjot": ["25g"], "Tejpatta": ["50g"]}},
    "Dalia & Grains": {"sub": "Dalia", "items": {"Wheat Dalia": ["500g"]}},
    "Pulses & Lentils": {"sub": "Dal", "items": {"Rajma": ["500g"], "Rajma Chitra": ["500g"], "Arhar Dal Patka": ["500g"], "Arhar Dal Aakhri": ["500g"], "Chana Dal": ["500g"], "Matar Dal": ["500g"], "Moong Dal Chilka": ["500g"], "Moong Dal Dhuli": ["500g"], "Masoor Dal": ["500g"], "Urad Dal Green": ["500g"], "Urad Dal Black": ["500g"], "Urad Dal Dhuli": ["500g"], "Kabuli Chana": ["500g"], "Red Chana Small": ["500g"], "Red Chana Big": ["500g"], "Whole Peas": ["500g"]}},
    "Pujan Materials": {"sub": "Puja Samagri", "items": {"Roli": ["1pc"], "Sindoor": ["1pc"], "Kapoor": ["1pc"], "Raksha Sutra": ["₹5", "₹10", "₹20", "₹30"], "Supari": ["100g"], "Dhoop Kati": ["1pack"], "Dhoop Chapad": ["1pack"], "Dhoop Sankla": ["1pack"], "Havan Samagri Pack": ["250g", "500g", "1kg", "5kg", "Loose"], "Agarbatti": ["₹10", "₹25", "₹50", "₹100"], "Matchbox": ["1pc"], "Cotton": ["1pack"], "Honey": ["25g", "50g", "100g", "250g", "500g", "1kg"], "Haldi": ["₹5", "₹10", "50g", "100g"], "Janeu / Yagyopavit": ["1pc"], "White Chandan": ["1pc"], "Yellow Chandan": ["1pc"], "Red Chandan": ["1pc"], "Ashtagandh": ["1pc"], "Bhasm": ["₹5", "₹10", "₹20", "₹50", "₹100"], "Raw Thread": ["1pc"], "Saptdhanya": ["1pack"], "Sarvoshadhi": ["1pack"], "Saptmritika": ["1pack"], "Ittar": ["1pc"], "Spray": ["1pc"], "Naav Kanta": ["1pc"], "Ghoda Naal": ["1pc"], "Abir": ["1pack"], "Gulal": ["1pack"], "Abhrak": ["1pc"], "Panchratna": ["1pack"], "Panchdhatu": ["1pack"], "Tulsi Mala": ["1pc"], "Haldi Mala": ["1pc"], "Rudraksh Mala": ["1pc"], "Kamal Gatta Mala": ["1pc"], "Red Chandan Mala": ["1pc"], "White Mala": ["1pc"], "Gunja Red Mala": ["1pc"], "Gunja White Mala": ["1pc"], "Gunja Black Mala": ["1pc"], "Brahm Ganth Janeu": ["1pc"], "Gulab Jal": ["1pc"], "Kevda Jal": ["1pc"], "Batasha": ["100g"], "Kesar": ["1g"], "Kasturi": ["1pc"], "Gorochan": ["1pc"], "Vanshlochan": ["1pc"]}},
    "Puja Essentials": {"sub": "Puja Essentials", "items": {"Panchmeva": ["100g", "250g", "500g"], "Black Til Chamki": ["100g"], "Black Til Puja": ["100g"], "Yellow Mustard": ["100g"], "Coconut Whole": ["1pc"], "Coconut Water Filled": ["1pc"], "Coconut Havan": ["1pc"], "Guggul Normal": ["50g"], "Guggul Pure": ["50g"], "Loban Colored": ["50g"], "Loban Pure": ["50g"], "Jatamansi": ["50g"], "Jatamansi Pure": ["50g"], "Indra Jaw": ["50g"], "Nagarmotha": ["50g"], "Kamalgatta": ["50g"], "Navgrah Wood": ["1pack"]}},
    "Chocolates & Sweets": {"sub": "Chocolate Bars", "items": {"Cadbury 5 Star": ["₹5", "₹10", "₹20", "40g"], "Cadbury Dairy Milk": ["₹10", "₹20", "₹40", "55g", "110g"], "Cadbury Dairy Milk Silk": ["60g", "150g"], "Cadbury Bournville": ["80g"], "Cadbury Fuse": ["25g", "48g"], "Cadbury Perk": ["₹5", "₹10", "₹20"], "Cadbury Gems": ["₹10", "₹20", "₹50"], "Cadbury Nutties": ["30g"], "Cadbury Crispello": ["35g"], "Nestle KitKat": ["₹10", "₹20", "38.5g"], "Nestle Munch": ["₹5", "₹10", "₹20"], "Nestle Milkybar": ["₹10", "₹20"], "Nestle Bar One": ["₹10", "₹20"], "Nestle Alpino": ["1pack"], "Amul Dark Chocolate": ["40g", "55g", "150g"], "Amul Milk Chocolate": ["40g", "150g"], "Snickers": ["22g", "50g"], "Mars": ["51g"], "Bounty": ["57g"], "Galaxy Smooth Milk": ["36g"], "Ferrero Rocher": ["3pc", "16pc"], "Toblerone": ["50g", "100g"], "LuvIt Chocwich": ["1pc"], "LuvIt Choco Bar": ["1pc"], "Parle Melody": ["₹1", "₹5"], "Parle Kismi": ["₹1", "₹5"], "Alpenliebe Eclairs": ["₹1", "₹5"], "Pulse Candy": ["₹1", "₹5"], "Center Fresh": ["₹1", "₹5"], "Center Fruit": ["₹1", "₹5"]}},
    "Ayurveda & Juices": {"sub": "Herbal Health", "items": {"Amla Juice": ["500ml", "1L"], "Aloe Vera Juice": ["500ml", "1L"], "Patanjali Amla Juice": ["500ml", "1L"], "Patanjali Aloe Vera Juice": ["500ml", "1L"], "Dabur Chyawanprash": ["250g", "500g", "1kg"], "Dabur Chyawanprakash Sugar Free": ["500g"], "Baidyanath Chyawanprash": ["500g", "1kg"], "Zandu Chyawanprash": ["450g", "900g"], "Amla Candy Sweet": ["100g", "250g"], "Amla Candy Chatpata": ["100g", "250g"], "Giloy Juice": ["500ml", "1L"], "Karela Jamun Juice": ["500ml", "1L"], "Triphala Juice": ["500ml"], "Neem Juice": ["500ml"], "Ashwagandha Powder": ["100g"], "Triphala Churna": ["100g"], "Amla Powder": ["100g"]}},
}

CATALOG.update(ADDITIONAL_CATALOG)


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


class SignupRequest(BaseModel):
    full_name: str
    mobile: str
    email: EmailStr
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


class AdminLoginRequest(BaseModel):
    mobile: str
    password: str


class OtpRequest(BaseModel):
    identifier: str


class OtpVerifyRequest(BaseModel):
    identifier: str
    otp: str


class AddressModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: Optional[str] = "Home"
    house: str
    area: str
    city: str = "Ghazipur"
    pincode: str = "233001"
    landmark: Optional[str] = ""


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    variant: str
    quantity: int
    selling_price: float
    image: Optional[str] = ""


class CustomerDetails(BaseModel):
    name: str
    mobile: str
    email: Optional[str] = ""


class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    address: AddressModel
    customer: Optional[CustomerDetails] = None
    coupon_code: Optional[str] = None


class ProductUpsert(BaseModel):
    product_name: str
    hindi_name: Optional[str] = ""
    english_name: Optional[str] = ""
    category: str
    subcategory: Optional[str] = "General"
    brand: Optional[str] = "Generic"
    variant: str = "1pc"
    unit: str = "pc"
    mrp: float
    selling_price: float
    stock_quantity: int
    product_image: Optional[str] = ""
    description: Optional[str] = ""
    status: str = "active"


class InventoryAdjust(BaseModel):
    product_id: str
    change_type: str
    quantity: int
    note: Optional[str] = ""


class OrderStatusUpdate(BaseModel):
    status: str
    delivery_boy_id: Optional[str] = None


class DeliveryBoyUpsert(BaseModel):
    name: str
    mobile: str
    vehicle: Optional[str] = ""
    status: Optional[str] = "active"


class AssignDeliveryBoyRequest(BaseModel):
    delivery_boy_id: str


class ReviewRequest(BaseModel):
    product_id: str
    rating: int
    comment: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def strip_mongo_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(doc, dict) and "_id" in doc:
        doc.pop("_id", None)
    return doc


def normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")[-10:]


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(check, digest)
    except ValueError:
        return False


def make_token(user: Dict[str, Any]) -> str:
    payload = {
        "sub": user["id"], "role": user.get("role", "customer"),
        "name": user.get("full_name", user.get("name", "User")),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(authorization: str = Header(default="")) -> Dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required")
    try:
        payload = jwt.decode(authorization.replace("Bearer ", ""), JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") not in ["super_admin", "store_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def split_unit(variant: str) -> str:
    match = re.search(r"[a-zA-Z]+", variant or "")
    return match.group(0).lower() if match else "pc"


def price_for(category: str, variant: str, index: int) -> Dict[str, float]:
    numbers = re.findall(r"\d+\.?\d*", variant or "")
    size = float(numbers[0]) if numbers else (index % 5 + 1) * 20
    multiplier = 1.0
    if "kg" in variant.lower() or "1l" in variant.lower():
        multiplier = 1.9
    base_map = {"Masala": 36, "Tea": 95, "Coffee": 85, "Hair Oils": 70, "Shampoo & Hair Care": 88, "Baby Care": 92, "Health Drinks": 155, "Biscuits": 18, "Toothpaste": 58, "Face Cream": 54, "Pickles": 75}
    base = base_map.get(category, 45)
    mrp = max(10, round(base + size * 0.22 * multiplier + (index % 7) * 3))
    selling = round(mrp * 0.9)
    return {"mrp": float(mrp), "selling_price": float(selling)}


def brand_from_name(name: str) -> str:
    known = ["Tata", "Lipton", "Kissan", "Dabur", "Patanjali", "Colgate", "Pepsodent", "Closeup", "Sensodyne", "Himalaya", "Johnson", "Horlicks", "Complan", "Boost", "Kellogg's", "Nescafe", "Bru", "Sunsilk", "Dove", "Pantene", "Tresemme", "Parle", "Oreo", "Nivea", "Pond's", "Vicco"]
    for brand in known:
        if name.lower().startswith(brand.lower()):
            return brand
    return name.split()[0] if name else "Generic"


def product_doc(category: str, subcategory: str, name: str, variant: str, index: int) -> Dict[str, Any]:
    safe_category = re.sub(r"[^A-Z0-9]+", "", category.upper())[:6]
    safe_name = re.sub(r"[^A-Z0-9]+", "", name.upper())[:8]
    sku = f"BGS-{safe_category}-{safe_name}-{index:04d}"
    prices = price_for(category, variant, index)
    stock = 0 if index % 37 == 0 else (6 if index % 19 == 0 else 12 + (index * 7) % 90)
    return {
        "id": str(uuid.uuid4()), "product_id": sku, "product_name": f"{name} {variant}",
        "hindi_name": f"{HINDI_CATEGORY_NAMES.get(category, category)} {variant}", "english_name": name,
        "category": category, "subcategory": subcategory, "brand": brand_from_name(name),
        "variant": variant, "unit": split_unit(variant), "sku": sku,
        "barcode": str(8900000000000 + index), "mrp": prices["mrp"], "selling_price": prices["selling_price"],
        "stock_quantity": stock, "minimum_stock": 10, "product_image": CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["Biscuits"]),
        "description": f"{name} {variant} available at BARNAWAL PROVISION STORE with 30 minute delivery.",
        "status": "out_of_stock" if stock == 0 else "active", "gst_rate": 5 if category in ["Tea", "Coffee", "Masala"] else 12,
        "rating": round(4.1 + (index % 9) / 10, 1), "review_count": 8 + index % 60,
        "featured": index % 9 == 0, "best_seller": index % 11 == 0,
        "created_at": now_iso(), "updated_at": now_iso(),
    }


async def ensure_catalog_seeded() -> Dict[str, int]:
    existing_count = await db.products.count_documents({})
    existing_keys = set()
    async for product in db.products.find({}, {"_id": 0, "english_name": 1, "variant": 1, "category": 1}):
        existing_keys.add((product.get("category"), product.get("english_name"), product.get("variant")))

    existing_categories = set()
    async for category_doc in db.categories.find({}, {"_id": 0, "name": 1}):
        existing_categories.add(category_doc.get("name"))

    categories_to_add = []
    products_to_add = []
    inventory_logs = []
    index = existing_count + 1

    for category, spec in CATALOG.items():
        if category not in existing_categories:
            categories_to_add.append({
                "id": str(uuid.uuid4()), "name": category,
                "hindi_name": HINDI_CATEGORY_NAMES.get(category, category),
                "image": CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["Biscuits"]),
                "description": f"Shop {category} with delivery in 30 minutes.",
                "status": "active", "created_at": now_iso(), "updated_at": now_iso(),
            })
            existing_categories.add(category)
        for name, variants in spec["items"].items():
            for variant in variants:
                key = (category, name, variant)
                if key in existing_keys:
                    continue
                doc = product_doc(category, spec["sub"], name, variant, index)
                products_to_add.append(doc)
                inventory_logs.append({"id": str(uuid.uuid4()), "product_id": doc["id"], "sku": doc["sku"], "change_type": "catalog_migration_stock", "quantity": doc["stock_quantity"], "note": "New catalogue item imported automatically", "created_at": now_iso()})
                existing_keys.add(key)
                index += 1

    if categories_to_add:
        await db.categories.insert_many(categories_to_add)
    if products_to_add:
        await db.products.insert_many(products_to_add)
        await db.inventory_logs.insert_many(inventory_logs)
    return {"categories_added": len(categories_to_add), "products_added": len(products_to_add)}


async def seed_database() -> None:
    if await db.products.count_documents({}) > 0:
        await ensure_catalog_seeded()
        return
    categories = []
    products = []
    inventory_logs = []
    index = 1
    for category, spec in CATALOG.items():
        cat_id = str(uuid.uuid4())
        categories.append({"id": cat_id, "name": category, "hindi_name": HINDI_CATEGORY_NAMES.get(category, category), "image": CATEGORY_IMAGES.get(category), "description": f"Shop {category} with delivery in 30 minutes.", "status": "active", "created_at": now_iso(), "updated_at": now_iso()})
        for name, variants in spec["items"].items():
            for variant in variants:
                doc = product_doc(category, spec["sub"], name, variant, index)
                products.append(doc)
                inventory_logs.append({"id": str(uuid.uuid4()), "product_id": doc["id"], "sku": doc["sku"], "change_type": "seed_stock", "quantity": doc["stock_quantity"], "note": "Opening stock imported automatically", "created_at": now_iso()})
                index += 1
    admin_hash = hash_password("admin123")
    users = [
        {"id": str(uuid.uuid4()), "full_name": "Super Admin", "mobile": "8381869505", "email": "admin1@barnawal.store", "password_hash": admin_hash, "role": "super_admin", "addresses": [], "created_at": now_iso(), "updated_at": now_iso()},
        {"id": str(uuid.uuid4()), "full_name": "Store Admin", "mobile": "8858351010", "email": "admin2@barnawal.store", "password_hash": hash_password("admin123"), "role": "store_admin", "addresses": [], "created_at": now_iso(), "updated_at": now_iso()},
    ]
    await db.categories.insert_many(categories)
    await db.products.insert_many(products)
    await db.inventory_logs.insert_many(inventory_logs)
    await db.users.insert_many(users)
    await db.settings.insert_one({"id": "store-settings", **STORE_INFO, "dark_mode": True, "cod_enabled": True, "upi_enabled": False, "cards_enabled": False, "wallet_enabled": False, "updated_at": now_iso()})


@app.on_event("startup")
async def startup_seed():
    await seed_database()
    # Idempotent migration: ensure WhatsApp fields exist on the live settings doc.
    existing = await db.settings.find_one({"id": "store-settings"}, {"_id": 0})
    if existing:
        defaults = {
            "primary_whatsapp": STORE_INFO["primary_whatsapp"],
            "secondary_whatsapp": STORE_INFO["secondary_whatsapp"],
            "primary_whatsapp_link": STORE_INFO["primary_whatsapp_link"],
            "secondary_whatsapp_link": STORE_INFO["secondary_whatsapp_link"],
            "contacts": STORE_INFO["contacts"],
        }
        missing = {k: v for k, v in defaults.items() if not existing.get(k)}
        if missing:
            await db.settings.update_one({"id": "store-settings"}, {"$set": {**missing, "updated_at": now_iso()}})

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "BARNAWAL PROVISION STORE API", "store": STORE_INFO}


@api_router.get("/store")
async def get_store():
    settings = await db.settings.find_one({"id": "store-settings"}, {"_id": 0})
    return settings or STORE_INFO


@api_router.put("/admin/settings")
async def update_admin_settings(payload: Dict[str, Any], admin: Dict[str, Any] = Depends(require_admin)):
    allowed = {
        "name", "contacts", "primary_whatsapp", "secondary_whatsapp",
        "primary_whatsapp_link", "secondary_whatsapp_link",
        "delivery_time", "delivery_message", "payment_method", "payment_note",
        "min_order_amount", "delivery_fee",
    }
    update = {k: v for k, v in payload.items() if k in allowed}
    # Normalize WhatsApp numbers: strip non-digits, build wa.me link automatically.
    for key in ("primary_whatsapp", "secondary_whatsapp"):
        if key in update and update[key]:
            digits = "".join(ch for ch in str(update[key]) if ch.isdigit())
            if len(digits) == 10:
                digits = "91" + digits
            update[key] = digits
            update[f"{key}_link"] = f"https://wa.me/{digits}"
    if "contacts" in update and isinstance(update["contacts"], list):
        update["contacts"] = [str(c).strip() for c in update["contacts"] if str(c).strip()]
    update["updated_at"] = now_iso()
    await db.settings.update_one({"id": "store-settings"}, {"$set": update}, upsert=True)
    settings = await db.settings.find_one({"id": "store-settings"}, {"_id": 0})
    return settings


@api_router.post("/auth/request-otp")
async def request_otp(payload: OtpRequest):
    await db.otp_requests.insert_one({"id": str(uuid.uuid4()), "identifier": payload.identifier, "otp": DEMO_OTP, "verified": False, "created_at": now_iso()})
    return {"message": "Demo OTP generated", "demo_otp": DEMO_OTP}


@api_router.post("/auth/verify-otp")
async def verify_otp(payload: OtpVerifyRequest):
    if payload.otp != DEMO_OTP:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    await db.otp_requests.update_many({"identifier": payload.identifier}, {"$set": {"verified": True, "updated_at": now_iso()}})
    return {"message": "OTP verified", "verified": True}


@api_router.post("/auth/signup")
async def signup(payload: SignupRequest):
    mobile = normalize_phone(payload.mobile)
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    existing = await db.users.find_one({"$or": [{"mobile": mobile}, {"email": payload.email.lower()}]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")
    user = {"id": str(uuid.uuid4()), "full_name": payload.full_name, "mobile": mobile, "email": payload.email.lower(), "password_hash": hash_password(payload.password), "role": "customer", "addresses": [], "wishlist": [], "created_at": now_iso(), "updated_at": now_iso()}
    await db.users.insert_one(user)
    strip_mongo_id(user)
    public = {k: v for k, v in user.items() if k != "password_hash"}
    return {"user": public, "token": make_token(user), "message": "Signup successful"}


@api_router.post("/auth/login")
async def login(payload: LoginRequest):
    identifier = payload.identifier.lower().strip()
    mobile = normalize_phone(identifier)
    user = await db.users.find_one({"$or": [{"mobile": mobile}, {"email": identifier}]}, {"_id": 0})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid login details")
    public = {k: v for k, v in user.items() if k != "password_hash"}
    return {"user": public, "token": make_token(user), "message": "Login successful"}


@api_router.post("/auth/admin-login")
async def admin_login(payload: AdminLoginRequest):
    mobile = normalize_phone(payload.mobile)
    user = await db.users.find_one({"mobile": mobile, "role": {"$in": ["super_admin", "store_admin", "staff"]}}, {"_id": 0})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid admin login")
    public = {k: v for k, v in user.items() if k != "password_hash"}
    return {"user": public, "token": make_token(user), "message": "Admin login successful"}


@api_router.get("/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    return user


@api_router.post("/me/addresses")
async def add_address(address: AddressModel, user: Dict[str, Any] = Depends(get_current_user)):
    addr = address.model_dump()
    await db.users.update_one({"id": user["id"]}, {"$push": {"addresses": addr}, "$set": {"updated_at": now_iso()}})
    return {"address": addr, "message": "Address saved"}


@api_router.get("/categories")
async def get_categories():
    categories = await db.categories.find({}, {"_id": 0}).sort("name", 1).to_list(200)
    for cat in categories:
        cat["product_count"] = await db.products.count_documents({"category": cat["name"]})
    return categories


@api_router.get("/products")
async def get_products(q: str = "", category: str = "", featured: bool = False, best_seller: bool = False, limit: int = Query(60, le=200), skip: int = 0, include_inactive: bool = False):
    query: Dict[str, Any] = {"status": {"$nin": ["deleted", "inactive"]}}
    if include_inactive:
        query = {"status": {"$ne": "deleted"}}
    if q:
        query["$or"] = [{"product_name": {"$regex": q, "$options": "i"}}, {"english_name": {"$regex": q, "$options": "i"}}, {"hindi_name": {"$regex": q, "$options": "i"}}, {"brand": {"$regex": q, "$options": "i"}}]
    if category:
        query["category"] = category
    if featured:
        query["featured"] = True
    if best_seller:
        query["best_seller"] = True
    total = await db.products.count_documents(query)
    products = await db.products.find(query, {"_id": 0}).sort("product_name", 1).skip(skip).limit(limit).to_list(limit)
    return {"items": products, "total": total, "delivery_message": STORE_INFO["delivery_message"]}


@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id, "status": {"$nin": ["deleted", "inactive"]}}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    related = await db.products.find({"category": product["category"], "id": {"$ne": product_id}}, {"_id": 0}).limit(8).to_list(8)
    reviews = await db.reviews.find({"product_id": product_id}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return {"product": product, "related": related, "reviews": reviews, "delivery_message": STORE_INFO["delivery_message"]}


@api_router.post("/wishlist/{product_id}")
async def toggle_wishlist(product_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    current = set(user.get("wishlist", []))
    if product_id in current:
        current.remove(product_id)
        wished = False
    else:
        current.add(product_id)
        wished = True
    await db.users.update_one({"id": user["id"]}, {"$set": {"wishlist": list(current), "updated_at": now_iso()}})
    return {"wished": wished, "wishlist": list(current)}


@api_router.get("/wishlist")
async def get_wishlist(user: Dict[str, Any] = Depends(get_current_user)):
    ids = user.get("wishlist", [])
    products = await db.products.find({"id": {"$in": ids}}, {"_id": 0}).to_list(200)
    return products


@api_router.post("/reviews")
async def add_review(payload: ReviewRequest, user: Dict[str, Any] = Depends(get_current_user)):
    rating = min(5, max(1, payload.rating))
    review = {"id": str(uuid.uuid4()), "product_id": payload.product_id, "customer_id": user["id"], "customer_name": user.get("full_name"), "rating": rating, "comment": payload.comment, "created_at": now_iso()}
    await db.reviews.insert_one(review)
    strip_mongo_id(review)
    return {"review": review, "message": "Review added"}


async def _get_optional_user(authorization: str = Header(default="")) -> Optional[Dict[str, Any]]:
    if not authorization.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(authorization.replace("Bearer ", ""), JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    return await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})


@api_router.post("/orders")
async def create_order(payload: CreateOrderRequest, authorization: str = Header(default="")):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    # Resolve customer details: either from logged-in user OR from payload.customer (guest)
    user = await _get_optional_user(authorization)
    if user:
        customer_id = user["id"]
        customer_name = (payload.customer.name if payload.customer and payload.customer.name else user.get("full_name", "Customer"))
        mobile = (payload.customer.mobile if payload.customer and payload.customer.mobile else user.get("mobile", ""))
        email = (payload.customer.email if payload.customer and payload.customer.email else user.get("email", ""))
    else:
        if not payload.customer or not payload.customer.name or not payload.customer.mobile:
            raise HTTPException(status_code=400, detail="Customer name and mobile number are required")
        customer_id = "guest-" + str(uuid.uuid4())
        customer_name = payload.customer.name
        mobile = normalize_phone(payload.customer.mobile)
        email = (payload.customer.email or "").lower()

    if not payload.address.house or not payload.address.area or not payload.address.pincode:
        raise HTTPException(status_code=400, detail="Complete address (house, area, pincode) is required")

    subtotal = sum(item.quantity * item.selling_price for item in payload.items)
    if subtotal < 200:
        raise HTTPException(status_code=400, detail=f"Minimum order ₹200 required for home delivery. Your subtotal is ₹{subtotal}. Please add more items.")
    delivery_fee = 0 if subtotal > 500 else 20
    discount = 25 if payload.coupon_code and payload.coupon_code.upper() == "BGS25" else 0
    total = round(subtotal + delivery_fee - discount, 2)
    order = {
        "id": str(uuid.uuid4()),
        "order_no": f"BGS-{random.randint(100000, 999999)}",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "mobile": mobile,
        "email": email,
        "address": payload.address.model_dump(),
        "items": [item.model_dump() for item in payload.items],
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount": discount,
        "total_amount": total,
        "payment_method": "Cash on Delivery",
        "payment_note": "Pay when your order is delivered.",
        "cod_status": "pending",
        "delivery_time": "30 Minutes",
        "status": "New Order",
        "tracking": [{"status": "New Order", "time": now_iso(), "message": "Order received"}],
        "is_guest": user is None,
        "is_read": False,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.orders.insert_one(order)
    strip_mongo_id(order)
    # Create admin notification
    notification = {
        "id": str(uuid.uuid4()),
        "type": "new_order",
        "title": "New Order Received",
        "message": f"Order {order['order_no']} from {customer_name} ({mobile}) - ₹{total}",
        "order_id": order["id"],
        "order_no": order["order_no"],
        "customer_name": customer_name,
        "mobile": mobile,
        "total_amount": total,
        "is_read": False,
        "created_at": now_iso(),
    }
    await db.admin_notifications.insert_one(notification)
    for item in payload.items:
        await db.products.update_one({"id": item.product_id}, {"$inc": {"stock_quantity": -item.quantity}, "$set": {"updated_at": now_iso()}})
        await db.inventory_logs.insert_one({"id": str(uuid.uuid4()), "product_id": item.product_id, "sku": "", "change_type": "stock_out", "quantity": item.quantity, "note": f"Order {order['order_no']}", "created_at": now_iso()})
    return {"order": order, "message": "Order placed successfully"}


@api_router.get("/orders")
async def my_orders(user: Dict[str, Any] = Depends(get_current_user)):
    return await db.orders.find({"customer_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)


@api_router.get("/orders/{order_id}")
async def order_detail(order_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    query = {"id": order_id} if user.get("role") != "customer" else {"id": order_id, "customer_id": user["id"]}
    order = await db.orders.find_one(query, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@api_router.get("/notifications")
async def notifications(user: Dict[str, Any] = Depends(get_current_user)):
    return [{"id": "n1", "title": "30 Minute Delivery", "message": "Your grocery essentials are delivered fast with COD.", "created_at": now_iso()}, {"id": "n2", "title": "Offer", "message": "Use coupon BGS25 for ₹25 off.", "created_at": now_iso()}]


@api_router.get("/admin/notifications")
async def admin_notifications(_: Dict[str, Any] = Depends(require_admin)):
    notifications = await db.admin_notifications.find({}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    unread_count = await db.admin_notifications.count_documents({"is_read": False})
    return {"notifications": notifications, "unread_count": unread_count}


@api_router.put("/admin/notifications/{notification_id}/read")
async def admin_mark_notification_read(notification_id: str, _: Dict[str, Any] = Depends(require_admin)):
    await db.admin_notifications.update_one({"id": notification_id}, {"$set": {"is_read": True}})
    return {"message": "Notification marked as read"}


@api_router.put("/admin/notifications/read-all")
async def admin_mark_all_read(_: Dict[str, Any] = Depends(require_admin)):
    await db.admin_notifications.update_many({"is_read": False}, {"$set": {"is_read": True}})
    return {"message": "All notifications marked as read"}


@api_router.get("/admin/dashboard")
async def admin_dashboard(_: Dict[str, Any] = Depends(require_admin)):
    total_products = await db.products.count_documents({"status": {"$ne": "deleted"}})
    total_categories = await db.categories.count_documents({})
    total_orders = await db.orders.count_documents({})
    delivered_orders = await db.orders.count_documents({"status": "Delivered"})
    pending_orders = await db.orders.count_documents({"status": {"$in": ["New Order", "Accepted", "Packed", "Out For Delivery"]}})
    total_customers = await db.users.count_documents({"role": "customer"})
    low_stock = await db.products.count_documents({"stock_quantity": {"$gt": 0, "$lte": 10}})
    out_stock = await db.products.count_documents({"stock_quantity": {"$lte": 0}})
    orders = await db.orders.find({}, {"_id": 0}).to_list(5000)
    revenue = round(sum(order.get("total_amount", 0) for order in orders if order.get("status") != "Cancelled"), 2)
    recent = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).limit(8).to_list(8)
    top_products = await db.products.find({"best_seller": True}, {"_id": 0}).limit(8).to_list(8)
    sales_chart = [{"name": day, "orders": max(1, total_orders // 7 + i), "revenue": max(500, revenue // 7 + i * 280)} for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])]
    last_price_sync = await db.price_sync_logs.find_one({}, {"_id": 0, "matched": 0, "unmatched": 0, "skipped": 0}, sort=[("created_at", -1)])
    return {"kpis": {"total_products": total_products, "total_categories": total_categories, "total_orders": total_orders, "pending_orders": pending_orders, "delivered_orders": delivered_orders, "total_customers": total_customers, "total_revenue": revenue, "low_stock_products": low_stock, "out_of_stock_products": out_stock}, "recent_orders": recent, "top_products": top_products, "sales_chart": sales_chart, "last_price_sync": last_price_sync}


@api_router.get("/admin/products")
async def admin_products(q: str = "", category: str = "", limit: int = Query(100, le=500), _: Dict[str, Any] = Depends(require_admin)):
    return await get_products(q=q, category=category, limit=limit, include_inactive=True)


@api_router.post("/admin/products")
async def admin_add_product(payload: ProductUpsert, _: Dict[str, Any] = Depends(require_admin)):
    index = await db.products.count_documents({}) + 1
    doc = payload.model_dump()
    doc.update({"id": str(uuid.uuid4()), "product_id": f"BGS-CUSTOM-{index:04d}", "english_name": payload.english_name or payload.product_name, "sku": f"BGS-CUSTOM-{index:04d}", "barcode": str(8909000000000 + index), "minimum_stock": 10, "gst_rate": 12, "rating": 4.2, "review_count": 0, "featured": False, "best_seller": False, "created_at": now_iso(), "updated_at": now_iso()})
    if not doc.get("product_image"):
        doc["product_image"] = CATEGORY_IMAGES.get(doc["category"], CATEGORY_IMAGES["Biscuits"])
    await db.products.insert_one(doc)
    strip_mongo_id(doc)
    return {"product": doc, "message": "Product added"}


@api_router.post("/admin/products/upload-image")
async def admin_upload_product_image(file: UploadFile = File(...), _: Dict[str, Any] = Depends(require_admin)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be smaller than 5MB")
    import base64
    encoded = base64.b64encode(contents).decode("ascii")
    data_url = f"data:{file.content_type};base64,{encoded}"
    return {"url": data_url, "size": len(contents), "content_type": file.content_type}


@api_router.put("/admin/products/{product_id}")
async def admin_update_product(product_id: str, payload: ProductUpsert, _: Dict[str, Any] = Depends(require_admin)):
    data = payload.model_dump()
    data["updated_at"] = now_iso()
    result = await db.products.update_one({"id": product_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return {"product": product, "message": "Product updated"}


@api_router.delete("/admin/products/{product_id}")
async def admin_delete_product(product_id: str, _: Dict[str, Any] = Depends(require_admin)):
    await db.products.update_one({"id": product_id}, {"$set": {"status": "deleted", "updated_at": now_iso()}})
    return {"message": "Product deleted"}


@api_router.get("/admin/categories")
async def admin_categories(_: Dict[str, Any] = Depends(require_admin)):
    return await get_categories()


@api_router.post("/admin/categories")
async def admin_add_category(payload: Dict[str, str], _: Dict[str, Any] = Depends(require_admin)):
    cat = {"id": str(uuid.uuid4()), "name": payload.get("name"), "hindi_name": payload.get("hindi_name", payload.get("name")), "image": payload.get("image", CATEGORY_IMAGES["Biscuits"]), "description": payload.get("description", ""), "status": "active", "created_at": now_iso(), "updated_at": now_iso()}
    await db.categories.insert_one(cat)
    strip_mongo_id(cat)
    return {"category": cat, "message": "Category added"}


@api_router.put("/admin/categories/{category_id}")
async def admin_update_category(category_id: str, payload: Dict[str, str], _: Dict[str, Any] = Depends(require_admin)):
    payload["updated_at"] = now_iso()
    await db.categories.update_one({"id": category_id}, {"$set": payload})
    return {"message": "Category updated"}


@api_router.delete("/admin/categories/{category_id}")
async def admin_delete_category(category_id: str, _: Dict[str, Any] = Depends(require_admin)):
    await db.categories.delete_one({"id": category_id})
    return {"message": "Category deleted"}


@api_router.get("/admin/inventory")
async def admin_inventory(_: Dict[str, Any] = Depends(require_admin)):
    products = await db.products.find({"status": {"$ne": "deleted"}}, {"_id": 0}).sort("stock_quantity", 1).limit(200).to_list(200)
    logs = await db.inventory_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return {"products": products, "logs": logs}


@api_router.post("/admin/inventory/adjust")
async def admin_adjust_inventory(payload: InventoryAdjust, _: Dict[str, Any] = Depends(require_admin)):
    qty = abs(payload.quantity) if payload.change_type == "stock_in" else -abs(payload.quantity)
    await db.products.update_one({"id": payload.product_id}, {"$inc": {"stock_quantity": qty}, "$set": {"updated_at": now_iso()}})
    log = {"id": str(uuid.uuid4()), "product_id": payload.product_id, "change_type": payload.change_type, "quantity": abs(payload.quantity), "note": payload.note, "created_at": now_iso()}
    await db.inventory_logs.insert_one(log)
    strip_mongo_id(log)
    return {"log": log, "message": "Inventory updated"}


@api_router.get("/admin/orders")
async def admin_orders(status: str = "", _: Dict[str, Any] = Depends(require_admin)):
    query = {"status": status} if status else {}
    return await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)


@api_router.put("/admin/orders/{order_id}/status")
async def admin_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    set_fields = {"status": payload.status, "updated_at": now_iso()}
    delivery_boy = None
    if payload.delivery_boy_id:
        delivery_boy = await db.delivery_boys.find_one({"id": payload.delivery_boy_id}, {"_id": 0})
        if delivery_boy:
            set_fields.update({
                "delivery_boy_id": delivery_boy["id"],
                "delivery_boy_name": delivery_boy["name"],
                "delivery_boy_mobile": delivery_boy["mobile"],
            })
    elif order.get("delivery_boy_id"):
        delivery_boy = await db.delivery_boys.find_one({"id": order["delivery_boy_id"]}, {"_id": 0})
    tracking = {"status": payload.status, "time": now_iso(), "message": f"Order marked as {payload.status}"}
    await db.orders.update_one({"id": order_id}, {"$set": set_fields, "$push": {"tracking": tracking}})

    # MOCKED SMS to customer on every status change
    customer_mobile = order.get("mobile", "")
    customer_name = order.get("customer_name", "Customer")
    order_no = order.get("order_no")
    if payload.status == "Out For Delivery" and delivery_boy:
        sms_text = (
            f"Hi {customer_name}, your BARNAWAL order {order_no} (₹{order.get('total_amount')}) is OUT FOR DELIVERY. "
            f"Delivery partner: {delivery_boy['name']} ({delivery_boy['mobile']}). "
            f"Vehicle: {delivery_boy.get('vehicle','-')}. Pay on delivery. Thanks!"
        )
    else:
        sms_text = f"Hi {customer_name}, your BARNAWAL order {order_no} is now: {payload.status}. Total ₹{order.get('total_amount')} (COD)."
    sms_log = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "order_no": order_no,
        "to_mobile": customer_mobile,
        "customer_name": customer_name,
        "status": payload.status,
        "message": sms_text,
        "provider": "MOCKED",
        "delivered": True,
        "created_at": now_iso(),
    }
    await db.sms_logs.insert_one(sms_log)
    logger.info(f"[MOCKED SMS] to {customer_mobile}: {sms_text}")

    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return {"order": updated_order, "sms_log": {k: v for k, v in sms_log.items() if k != "_id"}, "message": "Order status updated"}


@api_router.put("/admin/orders/{order_id}/assign")
async def admin_assign_delivery_boy(order_id: str, payload: AssignDeliveryBoyRequest, _: Dict[str, Any] = Depends(require_admin)):
    delivery_boy = await db.delivery_boys.find_one({"id": payload.delivery_boy_id}, {"_id": 0})
    if not delivery_boy:
        raise HTTPException(status_code=404, detail="Delivery boy not found")
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.orders.update_one({"id": order_id}, {"$set": {
        "delivery_boy_id": delivery_boy["id"],
        "delivery_boy_name": delivery_boy["name"],
        "delivery_boy_mobile": delivery_boy["mobile"],
        "updated_at": now_iso(),
    }, "$push": {"tracking": {"status": "Assigned", "time": now_iso(), "message": f"Assigned to {delivery_boy['name']}"}}})
    updated = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return {"order": updated, "message": f"Assigned to {delivery_boy['name']}"}


@api_router.get("/admin/delivery-boys")
async def admin_list_delivery_boys(_: Dict[str, Any] = Depends(require_admin)):
    boys = await db.delivery_boys.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return boys


@api_router.post("/admin/delivery-boys")
async def admin_add_delivery_boy(payload: DeliveryBoyUpsert, _: Dict[str, Any] = Depends(require_admin)):
    mobile = normalize_phone(payload.mobile)
    existing = await db.delivery_boys.find_one({"mobile": mobile})
    if existing:
        raise HTTPException(status_code=409, detail="Delivery boy with this mobile already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "mobile": mobile,
        "vehicle": payload.vehicle or "",
        "status": payload.status or "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.delivery_boys.insert_one(doc)
    strip_mongo_id(doc)
    return {"delivery_boy": doc, "message": "Delivery boy added"}


@api_router.put("/admin/delivery-boys/{boy_id}")
async def admin_update_delivery_boy(boy_id: str, payload: DeliveryBoyUpsert, _: Dict[str, Any] = Depends(require_admin)):
    mobile = normalize_phone(payload.mobile)
    duplicate = await db.delivery_boys.find_one({"mobile": mobile, "id": {"$ne": boy_id}})
    if duplicate:
        raise HTTPException(status_code=409, detail="Another delivery boy already uses this mobile")
    update = {
        "name": payload.name,
        "mobile": mobile,
        "vehicle": payload.vehicle or "",
        "status": payload.status or "active",
        "updated_at": now_iso(),
    }
    result = await db.delivery_boys.update_one({"id": boy_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Delivery boy not found")
    boy = await db.delivery_boys.find_one({"id": boy_id}, {"_id": 0})
    return {"delivery_boy": boy, "message": "Delivery boy updated"}


@api_router.delete("/admin/delivery-boys/{boy_id}")
async def admin_delete_delivery_boy(boy_id: str, _: Dict[str, Any] = Depends(require_admin)):
    await db.delivery_boys.delete_one({"id": boy_id})
    return {"message": "Delivery boy removed"}


@api_router.get("/admin/sms-logs")
async def admin_sms_logs(order_id: str = "", _: Dict[str, Any] = Depends(require_admin)):
    query = {"order_id": order_id} if order_id else {}
    logs = await db.sms_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    return logs


# -------------------- Price Sync --------------------

class BulkPriceItem(BaseModel):
    product_id: str
    mrp: float
    selling_price: float


class BulkPriceUpdate(BaseModel):
    items: List[BulkPriceItem]
    source: Optional[str] = "manual_bulk_edit"


def _normalize_match_key(name: str, variant: str) -> str:
    name = re.sub(r"\s+", " ", (name or "").strip().lower())
    variant = re.sub(r"\s+", "", (variant or "").strip().lower())
    return f"{name}|{variant}"


def _build_product_lookup(products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for p in products:
        for name_field in ("english_name", "product_name"):
            n = p.get(name_field) or ""
            # Strip trailing variant from product_name if present
            stripped = n
            v = p.get("variant", "")
            if v and n.lower().endswith(v.lower()):
                stripped = n[: -len(v)].strip()
            for candidate in {n, stripped}:
                if candidate:
                    lookup[_normalize_match_key(candidate, v)] = p
    return lookup


async def _apply_price_updates(rows: List[Dict[str, Any]], source: str, admin: Dict[str, Any]) -> Dict[str, Any]:
    products = await db.products.find({"status": {"$ne": "deleted"}}, {"_id": 0}).to_list(20000)
    lookup = _build_product_lookup(products)
    matched: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    seen_keys: set = set()

    for idx, row in enumerate(rows, start=1):
        name = (row.get("product_name") or row.get("english_name") or "").strip()
        variant = (row.get("variant") or "").strip()
        if not name or not variant:
            skipped.append({"row": idx, "reason": "Missing product_name or variant", "data": row})
            continue
        try:
            mrp = float(row.get("mrp"))
            selling = float(row.get("selling_price"))
        except (TypeError, ValueError):
            skipped.append({"row": idx, "reason": "Invalid MRP or selling price", "data": row})
            continue
        if mrp <= 0 or selling <= 0:
            skipped.append({"row": idx, "reason": "MRP and selling price must be > 0", "data": row})
            continue
        if selling > mrp:
            skipped.append({"row": idx, "reason": "Selling price cannot exceed MRP", "data": row})
            continue

        key = _normalize_match_key(name, variant)
        if key in seen_keys:
            skipped.append({"row": idx, "reason": "Duplicate row in this upload", "name": name, "variant": variant})
            continue
        seen_keys.add(key)

        product = lookup.get(key)
        if not product:
            unmatched.append({"row": idx, "product_name": name, "variant": variant, "reason": "No product matched by name+variant"})
            continue

        # Optional brand validation
        brand_in_row = (row.get("brand") or "").strip().lower()
        if brand_in_row and product.get("brand") and brand_in_row != product["brand"].lower():
            unmatched.append({"row": idx, "product_name": name, "variant": variant, "reason": f"Brand mismatch (csv='{row.get('brand')}', db='{product.get('brand')}')"})
            continue

        discount = round((mrp - selling) / mrp * 100, 2) if mrp > 0 else 0
        best_price = discount >= 20
        update = {
            "mrp": mrp,
            "selling_price": selling,
            "discount_percent": discount,
            "best_price": best_price,
            "price_updated_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.products.update_one({"id": product["id"]}, {"$set": update})
        matched.append({
            "row": idx,
            "product_id": product["id"],
            "product_name": product["product_name"],
            "variant": product["variant"],
            "old_mrp": product.get("mrp"),
            "old_selling_price": product.get("selling_price"),
            "new_mrp": mrp,
            "new_selling_price": selling,
            "discount_percent": discount,
        })

    sync_log = {
        "id": str(uuid.uuid4()),
        "source": source,
        "total_rows": len(rows),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "skipped_count": len(skipped),
        "matched": matched,
        "unmatched": unmatched,
        "skipped": skipped,
        "performed_by": admin.get("full_name") or admin.get("id"),
        "created_at": now_iso(),
    }
    await db.price_sync_logs.insert_one(sync_log)
    strip_mongo_id(sync_log)
    return sync_log


@api_router.get("/admin/price-sync/template")
async def admin_price_sync_template(_: Dict[str, Any] = Depends(require_admin)):
    products = await db.products.find({"status": {"$ne": "deleted"}}, {"_id": 0}).sort("category", 1).to_list(20000)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["product_name", "variant", "brand", "category", "mrp", "selling_price"])
    for p in products:
        name = p.get("english_name") or p.get("product_name") or ""
        v = p.get("variant", "")
        if v and name.lower().endswith(v.lower()):
            name = name[: -len(v)].strip()
        writer.writerow([name, v, p.get("brand", ""), p.get("category", ""), p.get("mrp", ""), p.get("selling_price", "")])
    buf.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="barnawal-price-sync-template.csv"'}
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)


@api_router.post("/admin/price-sync/csv")
async def admin_price_sync_csv(file: UploadFile = File(...), admin: Dict[str, Any] = Depends(require_admin)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV is empty or missing header row")
    required = {"product_name", "variant", "mrp", "selling_price"}
    missing = required - {(h or "").strip().lower() for h in reader.fieldnames}
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {', '.join(missing)}")
    rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]
    report = await _apply_price_updates(rows, source=f"csv:{file.filename}", admin=admin)
    return {"message": "Price sync complete", "report": report}


@api_router.post("/admin/price-sync/bulk-edit")
async def admin_price_sync_bulk_edit(payload: BulkPriceUpdate, admin: Dict[str, Any] = Depends(require_admin)):
    products = await db.products.find({"id": {"$in": [i.product_id for i in payload.items]}, "status": {"$ne": "deleted"}}, {"_id": 0}).to_list(2000)
    id_to_product = {p["id"]: p for p in products}
    rows = []
    for item in payload.items:
        p = id_to_product.get(item.product_id)
        if not p:
            continue
        name = p.get("english_name") or p.get("product_name") or ""
        v = p.get("variant", "")
        if v and name.lower().endswith(v.lower()):
            name = name[: -len(v)].strip()
        rows.append({
            "product_name": name,
            "variant": v,
            "brand": p.get("brand", ""),
            "mrp": item.mrp,
            "selling_price": item.selling_price,
        })
    report = await _apply_price_updates(rows, source=payload.source or "manual_bulk_edit", admin=admin)
    return {"message": "Bulk price edit complete", "report": report}


@api_router.get("/admin/price-sync/logs")
async def admin_price_sync_logs(_: Dict[str, Any] = Depends(require_admin)):
    # Lightweight list view (omit big arrays)
    logs = await db.price_sync_logs.find({}, {"_id": 0, "matched": 0, "unmatched": 0, "skipped": 0}).sort("created_at", -1).limit(50).to_list(50)
    last = logs[0] if logs else None
    return {"last_sync": last, "logs": logs}


@api_router.get("/admin/price-sync/logs/{sync_id}")
async def admin_price_sync_log_detail(sync_id: str, _: Dict[str, Any] = Depends(require_admin)):
    log = await db.price_sync_logs.find_one({"id": sync_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Sync log not found")
    return log


# -------------------- end Price Sync --------------------


@api_router.get("/admin/customers")
async def admin_customers(_: Dict[str, Any] = Depends(require_admin)):
    customers = await db.users.find({"role": "customer"}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    for customer in customers:
        orders = await db.orders.find({"customer_id": customer["id"]}, {"_id": 0}).to_list(500)
        customer["total_orders"] = len(orders)
        customer["total_spent"] = round(sum(order.get("total_amount", 0) for order in orders), 2)
        customer["last_order_date"] = orders[0]["created_at"] if orders else "-"
    return customers


@api_router.get("/admin/reports")
async def admin_reports(_: Dict[str, Any] = Depends(require_admin)):
    orders = await db.orders.find({}, {"_id": 0}).to_list(5000)
    revenue = sum(order.get("total_amount", 0) for order in orders if order.get("status") != "Cancelled")
    products = await db.products.find({}, {"_id": 0}).limit(20).to_list(20)
    return {"daily_sales": round(revenue / 30 if revenue else 0, 2), "weekly_sales": round(revenue / 4 if revenue else 0, 2), "monthly_sales": round(revenue, 2), "product_performance": products, "export_formats": ["PDF", "Excel"]}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()