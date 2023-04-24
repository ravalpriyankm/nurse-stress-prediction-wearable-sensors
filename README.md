# Nurse-stress-prediction-wearable-sensors
This repository contains code and data for predicting stress levels in nurses using wearable sensors.

# Project Description
This project investigates the use of physiological signals from wearable devices to detect stress levels in nurses working in a hospital. The dataset contains information collected from nurses who wore a watch that recorded their heart rate, skin temperature, and electrodermal activity (EDA) while they reported their corresponding levels of stress.

The aim of this project is to evaluate the performance of different machine learning models for predicting stress levels based on the recorded physiological signals. The project also examines which physiological signals are most relevant for detecting stress and provides recommendations for improving the accuracy and reliability of stress detection using wearable technology.

# Files
data/: This folder contains the raw and processed data used in the project.
For Download CLick here
https://drive.google.com/drive/folders/10s_mez9cQ0J0J7hUnkNCVE3BVTNT8j1V?usp=sharing

notebooks/: This folder contains Jupyter notebooks used for data cleaning, exploratory data analysis, and model training and evaluation.
src/: This folder contains Python scripts used for data processing and model training and evaluation.
README.md: This file provides an overview of the project and instructions for running the code.

# Requirements
Python 3.7 or higher
Jupyter Notebook
Required Python packages are listed in requirements.txtTo run the code, you will need to install the following libraries:
pandas
numpy
scikit-learn
matplotlib

# Results
The project found that the Random Forest Classifier and Decision Tree Classifier models performed the best for predicting stress levels based on the recorded physiological signals. The study also found that EDA is a more significant indicator of stress compared to temperature and heart rate. Finally, the project provides recommendations for improving stress detection using wearable technology, such as addressing class imbalance in the dataset and ensuring algorithm transparency.

# Recommendations
Based on the analysis, the following recommendations are provided to the company:

1. Address the class imbalance in the dataset by using oversampling techniques or adjusting the decision threshold for the minority classes.
2. Assess the relevance of the physiological signals provided for detecting stress accurately and consider incorporating other signals or features that are more    specific to stress.
3. Optimize for recall to minimize false negatives, even at the expense of lower precision.
4. Ensure that the algorithm's decision-making process is transparent and explainable to end-users.

# License
This project is licensed under the MIT License - see the LICENSE.md file for details.
