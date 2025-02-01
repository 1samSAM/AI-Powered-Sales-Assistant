# Real-Time AI Sales Intelligence and Sentiment-Driven Deal Negotiation Assistant 

Enhancing sales performance through AI-driven insights, real-time analytics, and personalized deal recommendations.

---

## 📜 Project Overview

The **Real-Time AI-Powered Sales Intelligence Tool** is designed to revolutionize sales processes by leveraging cutting-edge AI models and real-time data analytics. It assists sales representatives in live customer interactions by providing sentiment analysis, tone detection, tailored deal recommendations, and negotiation strategies.

---

## ✨ Key Features

1. **Real-Time Sentiment & Tone Analysis**  
   Understand buyer emotions and intent during live calls using HuggingFace pretrained models.

2. **Dynamic Deal Recommendations**  
   Leverage CRM data and Retrieval-Augmented Generation (RAG) frameworks to suggest optimal deal terms.

3. **AI-Powered Negotiation Coach**  
   Provide live, personalized negotiation tips using Groq LLM Llama 7B.

4. **Post-Call Insights Hub**  
   Automatically summarize key takeaways and recommend actionable steps for follow-ups.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Frontend**: Streamlit
- **AI Models**:  
  - HuggingFace pretrained models for sentiment, tone, and intent analysis  
  - Groq LLM Llama 7B for negotiation strategy generation
- **Database**: SQLite (for customer and interaction data)
- **Google Sheets**: For tracking performance metrics
- **Deployment**: Local and Cloud-ready

---

## Deployment & Access

The AI-Powered Sales Intelligence tool has been successfully deployed and is now available for testing. You can try the live application at:

🔗 [[ Streamlit App URL](https://real-time-ai-sales-intelligence.streamlit.app/)]

This application provides dynamic deal recommendations and post-call insights based on real-time buyer signals. It utilizes NLP, sentiment analysis, and CRM data to assist sales teams in optimizing customer interactions.

Feel free to explore the features and provide feedback! 🚀

## 🔧 System Architecture

**Components**:  
- **Inputs**:  
  - CRM Database (Customer details, interaction history)  
  - Excel file (200 car details via RAG framework)  
  - Live call data  

- **AI Models**:  
  - HuggingFace for sentiment, tone, and intent analysis  
  - Groq LLM Llama 7B for live negotiation and deal structuring  

- **Outputs**:  
  - Real-time insights  
  - Deal recommendations  
  - Negotiation feedback  

**System Flow**:  
Inputs → AI Processing → Outputs (Insights, Recommendations, Feedback)

---

## 🚀 Installation and Setup

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/1samSAM/Real-time-Ai-sales-intelligence.git
   cd real-time-sales-intelligence

2. **Install Dependencies**

 ```
 pip install -r requirements.txt
 ```
 4. **Set Up Google Cloud Service Account**

 Create a service account in Google Cloud with access to Google Sheets and Drive APIs.
 Save the credentials as alert.json in the root directory.
5. **Run the Application**
 ``` 
 streamlit run app.py
 ```
## 🧠 Core Functionalities
1. Sentiment & Intent Analysis
Real-time analysis of buyer emotions, tone, and intent during calls. Outputs actionable insights to sales reps.

2. Dynamic Deal Recommendations
Combines RAG framework with CRM data to generate personalized deal terms for better conversion rates.

3. AI-Powered Negotiation Assistant
Live guidance for sales reps to handle buyer objections, adjust offers, and close deals effectively.

4. Post-Call Insights Hub
Summarizes call outcomes and stores insights in Google Sheets for tracking and future analysis.

## 📊 Performance Metrics Tracking
The tool updates the following metrics in Google Sheets:

Sales representative performance
Negotiation results and feedback
Buyer sentiment trends
Time-stamped call insights

## 🛡️ Future Upgrades
Expand support for additional languages using multilingual AI models.
Integrate voice-to-text transcription for live call analysis.
Incorporate advanced dashboards for visualizing sales trends.
## 🤝 Contributing
We welcome contributions! To get started:

**Fork the repository**
```
Create a new branch (git checkout -b feature/your-feature)
Commit your changes (git commit -m 'Add your feature')
Push to the branch (git push origin feature/your-feature)
```
Open a Pull Request
## Project Structure

```bash
.
├── SalesCRM.db             # SQLite database for CRM data
├── crm_database_create.py  # Script for creating the CRM database
├── indexing.py             # Script for vector creation using the RAG framework
├── main.py                 # Main application file for running the tool
├── negotiation.py          # Module handling negotiation processes
├── product_details.xlsx    # Excel file containing car details
├── requirements.txt        # List of dependencies for the project
├── state.py                # State management logic
├── utils.py                # Utility functions used across the project
└── README.md               # Project documentation
```




## 📝 License
This project is licensed under the MIT License. See the LICENSE file for details.

## 🙌 Acknowledgements
Special thanks to:

HuggingFace for their powerful pretrained models
LangChain and RAG for enabling seamless data retrieval
Groq for providing advanced NLP capabilities 
Google Cloud for the Sheets API.
SQLite for lightweight database management.
Contribution
Pull requests are welcome! For major changes, please open an issue to discuss your proposed changes first.
