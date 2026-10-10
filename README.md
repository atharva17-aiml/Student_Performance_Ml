# Student Performance ML System

A full-stack Flask-based Student Performance Prediction System that uses Machine Learning to predict a student's final performance (G3) based on academic and personal input factors.

The system provides user authentication, profile management, ML-based prediction, prediction history, analytics, administrator controls, audit logging, and personalized recommendations.

---

## Features

### User Features

- User registration and login
- Secure password hashing
- Logout functionality
- Profile management
- Student performance prediction
- Prediction input validation
- Prediction history
- Dashboard with personalized statistics
- Personalized performance recommendations
- Session management

### Password Recovery

- Forgot password functionality
- OTP-based password verification
- Password reset functionality
- OTP expiration handling

### Machine Learning

- Student final score prediction
- Linear Regression model evaluation
- Random Forest model evaluation
- Automatic selection of the best-performing model
- Model evaluation using:
  - R² Score
  - Mean Absolute Error (MAE)
  - Root Mean Squared Error (RMSE)
- Model metadata and training report generation

### Admin Features

- Admin dashboard
- View registered users
- View all predictions
- Prediction analytics
- Performance distribution
- Predictions per day
- CSV export
- Admin password reset
- Audit log monitoring
- Application activity tracking

### Analytics

- Prediction performance analysis
- Score distribution
- Prediction statistics
- Visual charts
- Good-performance and risk-performance classification

---

## Tech Stack

### Backend

- Python
- Flask
- MySQL
- Jinja2

### Machine Learning

- Scikit-learn
- Pandas
- NumPy
- Matplotlib

### Frontend

- HTML5
- CSS3
- Jinja2 Templates
- Font Awesome
- JavaScript

### Deployment

- Gunicorn
- Render

---

## Machine Learning Model

The system predicts the student's final score (G3).

### Input Features

The prediction model uses:

- `studytime`
- `failures`
- `absences`
- `health`
- `G1`
- `G2`

### Algorithms Evaluated

1. Linear Regression
2. Random Forest Regressor

The system evaluates both models and selects the better-performing model based on validation performance.

### Current Model

The current training pipeline selects:

**Random Forest Regressor**

Model version:

**v2.0**

### Model Performance

The current trained model achieved approximately:

| Metric | Random Forest |
|--------|--------------:|
| Cross-Validation R² | 0.8681 |
| Test R² | 0.8383 |
| MAE | 1.1541 |
| RMSE | 1.8211 |

> Model performance may change when the dataset or training configuration changes.

---

## Prediction Features

The prediction form accepts:

| Feature | Description | Range |
|---------|-------------|------:|
| Study Time | Weekly study-time category | 1–4 |
| Failures | Number of previous failures | 0–10 |
| Absences | Number of absences | 0–100 |
| Health | Current health status | 1–5 |
| G1 | First-period grade | 0–20 |
| G2 | Second-period grade | 0–20 |

The application validates all prediction inputs before sending them to the ML model.

---

## Personalized Recommendations

After generating a prediction, the application provides personalized recommendations based on:

- Predicted score
- Study time
- Previous failures
- Absences
- Health
- G1 and G2 performance
- Academic performance trends

The recommendation system is **rule-based personalization**, using the ML prediction and student inputs to generate relevant suggestions.

---

## Project Structure

```text
Student_Performance_Ml/
│
├── app.py
├── train_model.py
├── database.py
├── migrate_users.py
├── requirements.txt
├── render.yaml
├── .gitignore
│
├── dataset/
│   └── student_data.csv
│
├── model/                         # Generated locally after training
│   ├── model.pkl
│   ├── metadata.pkl
│   ├── model_metrics.csv
│   └── training_report.txt
│
├── services/
│   ├── db_service.py
│   ├── ml_service.py
│   ├── validation.py
│   ├── audit_service.py
│   └── recommendation_service.py
│
├── static/
│   └── css/
│       ├── global.css
│       └── style.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── profile.html
    ├── history.html
    ├── analysis.html
    ├── admin.html
    ├── audit_logs.html
    ├── forgot.html
    ├── verify_otp.html
    └── reset_password.html