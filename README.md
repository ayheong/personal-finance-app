# personal-finance-app

A full-stack web app that converts raw bank and credit card statements into categorized expenses and budget insights.  
Built with Flask + MongoDB, integrating a fine-tuned BERT model with regex rules for transaction classification.

---

## Features
- Secure JWT-based login  
- CSV upload with deduplication  
- Transaction categorization with BERT + regex  
- Interactive budgeting dashboard  

---

## Modeling
- Custom dataset of 2,000+ labeled transactions  
- Fine-tuned `bert-base-uncased` with Hugging Face Transformers  
- Classifies transactions into 11 categories (Housing, Food, Travel, etc.)  

---

## Setup

```bash
# Clone repo
git clone https://github.com/yourusername/personal-finance-app.git
cd personal-finance-app

# Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Run the app
python app/app.py
