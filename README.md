# Stock Portfolio Management Tool

This is a command-line application for managing stock portfolios, stock lists, and social investing features. It allows users to:

- Sign up, log in, and manage their account
- Create and manage multiple portfolios
- Buy and sell stocks, view historical and predicted prices
- Create and share stock lists with friends
- Write and manage reviews for stock lists
- Add friends and manage friend requests
- View portfolio and stock statistics

## Requirements

- Python 3.8+
- PostgreSQL database
- Required Python packages (see below)

## Setup

1. **Clone the repository**  
   `git clone <repo-url>`

2. **Install dependencies**
```
pip install psycopg2-binary python-dotenv pwinput plotext pandas scikit-learn
```
3. **Configure environment variables**  
Create a `.env` file with your PostgreSQL credentials:
```
POSTGRES_VM_HOST=your_host
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```
4. **Set up the database**  
Ensure your PostgreSQL database is running and the required tables are created.

## Running the App
```
python stock_app.py
```


Follow the on-screen menu to use the application.

## Notes

- Sample data for S&P 500 stocks is available in `SP500History.csv`
- All user data is stored in a PostgreSQL database.
- ANSI color formatting is used for a better command-line experience.
- For any issues, check your database connection and environment variables.
