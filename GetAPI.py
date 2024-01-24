from flask import Flask, request, jsonify
import requests
import json
import os
import sqlite3
import datetime

app = Flask(__name__)
db_file = 'prediction_results.db'

# Initialize database if not exists
with sqlite3.connect(db_file) as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            timestamp TEXT PRIMARY KEY,
            beauty_enhance INTEGER,
            joint_enhance INTEGER,
            bone_enhance INTEGER
        )
    ''')

def read_from_db():
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM results ORDER BY timestamp DESC LIMIT 1')
            result_data = cursor.fetchone()

        if result_data:
            keys = ['beauty_enhance', 'joint_enhance', 'bone_enhance']
            result_dict = dict(zip(keys, result_data[1:]))  # Exclude the timestamp from the result_dict
            return result_dict
        else:
            return {}
    except Exception as e:
        return {"Error": f"Unexpected error: {str(e)}"}

def initialize_counts():
    result_data = read_from_db()
    if result_data and "Error" not in result_data:
        return (
            result_data.get("beauty_enhance", 3),
            result_data.get("joint_enhance", 3),
            result_data.get("bone_enhance", 3)
        )
    else:
        return 3, 3, 3

noofribbons, noofarrows, noofstars = initialize_counts()
prediction_threshold = 0.90

def make_prediction(image_file):
    prediction_key = "27dea928805b4e6baf8b46e2854986b7"
    endpoint = 'https://cvobjectdetector-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/060c28e6-5b5f-41cb-8426-5036e6cfa1b9/detect/iterations/Iteration1/image'
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }
    response = requests.post(endpoint, headers=headers, data=image_file.read())

    if response.status_code == 200:
        result = response.json()
        return {
            "BeautyEnhance": noofribbons - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Ribbon" and obj["probability"] >= prediction_threshold),
            "JointEnhance": noofarrows - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Arrow" and obj["probability"] >= prediction_threshold),
            "BoneEnhance": noofstars - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Star" and obj["probability"] >= prediction_threshold)
        }
    else:
        return {"Error": f"{response.status_code} - {response.text}"}

def write_to_db(timestamp, beauty_enhance, joint_enhance, bone_enhance):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Check if a result for the given timestamp already exists
        cursor.execute('SELECT * FROM results WHERE timestamp = ?', (timestamp,))
        existing_result = cursor.fetchone()

        if existing_result:
            # Overwrite the existing record with the new result
            cursor.execute('''
                UPDATE results
                SET beauty_enhance = ?, joint_enhance = ?, bone_enhance = ?
                WHERE timestamp = ?
            ''', (beauty_enhance, joint_enhance, bone_enhance, timestamp))
        else:
            # Insert a new record if the timestamp doesn't exist
            cursor.execute('''
                INSERT INTO results (timestamp, beauty_enhance, joint_enhance, bone_enhance)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, beauty_enhance, joint_enhance, bone_enhance))

def read_from_db():
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM results ORDER BY timestamp DESC LIMIT 1')
            result_data = cursor.fetchone()

        if result_data:
            keys = ['beauty_enhance', 'joint_enhance', 'bone_enhance']
            result_dict = dict(zip(keys, result_data[1:]))  # Exclude the timestamp from the result_dict
            return result_dict
        else:
            return {}
    except Exception as e:
        return {"Error": f"Unexpected error: {str(e)}"}

@app.route('/', methods=['POST', 'GET'])
def detect_objects():
    global noofribbons, noofarrows, noofstars

    if request.method == 'POST':
        try:
            if 'image' not in request.files:
                return jsonify({"Error": "No image file provided"}), 400

            image_file = request.files['image']

            if image_file.filename == '':
                return jsonify({"Error": "No selected file"}), 400

            # Reset counts to initial values
            noofribbons = 3
            noofarrows = 3
            noofstars = 3

            # Make predictions
            prediction_result = make_prediction(image_file)

            # Get current timestamp
            timestamp = str(datetime.datetime.now())

            # Write results to the database, overwriting existing record if any
            write_to_db(timestamp, prediction_result["BeautyEnhance"], prediction_result["JointEnhance"], prediction_result["BoneEnhance"])

            # Update global counts
            noofribbons = prediction_result["BeautyEnhance"]
            noofarrows = prediction_result["JointEnhance"]
            noofstars = prediction_result["BoneEnhance"]

            # Return a response indicating successful image processing
            return jsonify({"Message": "Image processed successfully"})
        except Exception as e:
            return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500

    elif request.method == 'GET':
        # HTML form directly defined within the Python script
        return '''
        <!doctype html>
        <title>Upload an image</title>
        <h1>Upload an image</h1>
        <form method=post enctype=multipart/form-data>
            <input type=file name=image>
            <input type=submit value=Upload>
        </form>
        '''

@app.route('/result', methods=['GET'])
def retrieve_result():
    try:
        # Read the latest result from the database
        result_data = read_from_db()

        if result_data and "Error" not in result_data:
            # Create the desired JSON format
            result_json = {
                "items": [
                    {"name": "beauty_enhance", "quantity": result_data.get("beauty_enhance", 0)},
                    {"name": "bone_enhance", "quantity": result_data.get("bone_enhance", 0)},
                    {"name": "joint_enhance", "quantity": result_data.get("joint_enhance", 0)}
                ]
            }
            return jsonify(result_json)
        else:
            return jsonify({"Error": "Result not found"}), 404
    except Exception as e:
        return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)


