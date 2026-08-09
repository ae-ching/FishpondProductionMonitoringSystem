# Fishpond Production Monitoring System

## Overview

The Fishpond Production Monitoring System is a web-based application developed to monitor fishpond production and support harvest prediction. The system provides features for managing fishpond information, recording harvest data, viewing production analytics, and generating harvest predictions using a machine learning model.

The application is built with Django, with a separate machine learning component used to train and evaluate the harvest prediction model.

## Features

- User registration and login
- Fishpond management
- Harvest data recording
- Harvest prediction using machine learning
- Production analytics and data visualization
- Dashboard for monitoring fishpond production
- Application settings

## Tech Stack

### Backend
- Python
- Django

### Frontend
- HTML
- CSS
- JavaScript

### Database
- SQLite

### Machine Learning
- Python
- scikit-learn
- pandas
- Random Forest Regression

## Machine Learning

The system uses a Random Forest regression model to predict fishpond harvest production.

The machine learning component includes:

- Dataset preparation
- Exploratory data analysis
- Model training
- Model evaluation
- Harvest prediction
- Saved machine learning models and feature encoders for use by the web application

The trained model and supporting files are stored in the `ml-training/models/` directory.

## Project Structure

```text
FishpondProductionMonitoringSystem/
│
├── arich_project/
│   ├── arich_app/
│   │   ├── migrations/
│   │   ├── static/
│   │   ├── templates/
│   │   ├── forms.py
│   │   ├── ml_loader.py
│   │   ├── models.py
│   │   ├── prediction_service.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── arich_project/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── dashboard/
│   │   └── templates/
│   │       └── dashboard.html
│   │
│   ├── db.sqlite3
│   └── manage.py
│
├── ml-training/
│   ├── dataset/
│   │   └── fishpond_harvest_dataset.csv
│   │
│   ├── models/
│   │   ├── random_forest_model.pkl
│   │   ├── fish_encoder.pkl
│   │   └── feature_columns.pkl
│   │
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── exploratory_data_analysis.py
│   ├── predict.py
│   └── requirements.txt
│
├── build.sh
├── manage.py
├── requirements.txt
└── .gitignore