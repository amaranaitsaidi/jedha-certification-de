# Amazon Reviews - Relevance Analysis

Welcome to the **Amazon Reviews Relevance Analysis** application! This Streamlit application displays relevant product reviews from Snowflake with their relevance scores, designed for the Data Engineer certification [RNCP37172](https://www.francecompetences.fr/recherche/RNCP/37172/).

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

## 🌐 Deployment

### Deploy Backend (FastAPI)

The backend can be deployed using Docker:

```bash
docker build -t amazon-reviews-backend .
docker run -p 8000:8000 --env-file .env amazon-reviews-backend
```

Or deploy to cloud platforms like:
- **Render** (recommended for FastAPI)
- **Railway**
- **Heroku**

### Deploy Frontend (Streamlit Cloud)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add Snowflake credentials in **Secrets** (Settings → Secrets):

   ```toml
   SNOWFLAKE_USER = "your_user"
   SNOWFLAKE_PASSWORD = "your_password"
   SNOWFLAKE_ACCOUNT = "your_account"
   SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
   SNOWFLAKE_DATABASE = "AMAZON_REVIEWS"
   SNOWFLAKE_SCHEMA = "staging"
   SNOWFLAKE_ROLE = "ACCOUNTADMIN"
   ```

5. Set the backend URL in **Secrets** (or as an environment variable):

   ```toml
   API_URL = "https://your-backend-url.com"
   ```

6. Deploy!

---

## 📂 Project Structure

```plaintext
├── backend/
│   ├── main.py                  # FastAPI entrypoint
│   ├── database.py              # PostgreSQL setup (optional)
│   ├── models.py                # ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── crud.py                  # PostgreSQL CRUD (optional)
│   ├── snowflake_connector.py   # Snowflake connection
│   ├── snowflake_crud.py        # Snowflake queries
│   └── requirements.txt         # Backend dependencies
├── streamlit_app.py             # Streamlit frontend
├── requirements.txt             # Frontend dependencies
├── Dockerfile                   # Docker config for backend
├── .env.example                 # Example environment variables
└── README.md                    # This file
```

---

## ⚙️ Environment Variables

| Name                  | Description                              |
| --------------------- | ---------------------------------------- |
| `SNOWFLAKE_USER`      | Your Snowflake username                  |
| `SNOWFLAKE_PASSWORD`  | Your Snowflake password                  |
| `SNOWFLAKE_ACCOUNT`   | Your Snowflake account identifier        |
| `SNOWFLAKE_WAREHOUSE` | Snowflake warehouse name (e.g., COMPUTE_WH) |
| `SNOWFLAKE_DATABASE`  | Snowflake database name                  |
| `SNOWFLAKE_SCHEMA`    | Snowflake schema name                    |
| `SNOWFLAKE_ROLE`      | Snowflake role (e.g., ACCOUNTADMIN)      |
| `API_URL`             | Backend API URL (for Streamlit Cloud)    |

---

## 🤝 Contributing

Contributions are welcome! Whether you spot a bug, have an improvement, or just want to experiment:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/my-awesome-feature`.
3. Commit your changes: `git commit -m "Add my awesome feature"`.
4. Push to your branch: `git push origin feature/my-awesome-feature`.
5. Open a Pull Request and describe your changes.

---

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

*Happy coding and good luck with your certification!*
