# Blink App for Blepharospasm Analysis using Streamlit

The Blink app is based on Streamlit wich is a library that replicates a high level front-end environment with interactions with the main Data Science libraries focused in
data visualization.

For the database, I used google docs to store all patients data, to enable historical data to be collected and evaluated, and used the Dlib's HOG+SVM facial landmark predictor
Machine Learn model as the main resource of the app, focused in properly tracking the disease.

I also adapted some code from pyimagesearch in https://pyimagesearch.com/2021/04/19/face-detection-with-dlib-hog-and-cnn/. 
