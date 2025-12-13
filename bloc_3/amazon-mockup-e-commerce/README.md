# Amazon Reviews - Relevance Analysis

---

## 🚀 Features

* **Snowflake Integration**: Retrieves data directly from Snowflake data warehouse
* **Buyer-Specific Reviews**: View reviews for products purchased by a specific buyer
* **Relevance Scoring**: Displays reviews with calculated relevance scores
* **Rich Metadata**: Shows rating, text length, keyword scores, confidence scores
* **Review Images**: Displays images associated with reviews
* **Streamlit UI**: Clean, interactive interface for exploring reviews

---

## 🔧 Prerequisites

* **Python** (3.9+)
* **Snowflake Account** with access to the review data
* **Docker** (optional, for backend deployment)

---

## 💻 Local Development

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/amazon-mockup-e-commerce.git
   cd amazon-mockup-e-commerce
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment**

   Create a `.env` file in the project root with your Snowflake credentials:

   ```env
   # Snowflake Configuration
   SNOWFLAKE_USER=your_user
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_WAREHOUSE=COMPUTE_WH
   SNOWFLAKE_DATABASE=AMAZON_REVIEWS
   SNOWFLAKE_SCHEMA=staging
   SNOWFLAKE_ROLE=ACCOUNTADMIN
   ```

4. **Start the Backend (FastAPI)**

   ```bash
   cd backend
   python main.py
   ```

   The backend API will be available at **http://localhost:8000**

5. **Start Streamlit**

   In a new terminal:

   ```bash
   streamlit run streamlit_app.py
   ```

   Visit **[http://localhost:8501](http://localhost:8501)** to access the application.

6. **Use the Application**

   * Enter a Buyer ID (e.g., `d4a89317dd13a4a86e9f4677523427df2ff0751ee3bfbed2aab2839c0b7873bb`)
   * Select a product from the dropdown
   * View relevant reviews with scores and images

---