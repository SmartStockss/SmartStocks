from flask import Flask, request, jsonify
import requests
import json
import os
import datetime

app = Flask(__name__)
result_file = 'prediction_results.txt'

def read_from_file():
    try:
        with open(result_file, 'r') as file:
            data = json.load(file)

        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_to_file(data):
    with open(result_file, 'w') as file:
        json.dump(data, file)

def initialize_counts():
    result_data = read_from_file()
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
    # ... (unchanged)

def write_to_file(data):
    with open(result_file, 'w') as file:
        json.dump(data, file)

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

            # Write results to the file, overwriting existing record if any
            write_to_file({
                "timestamp": timestamp,
                "beauty_enhance": prediction_result["BeautyEnhance"],
                "joint_enhance": prediction_result["JointEnhance"],
                "bone_enhance": prediction_result["BoneEnhance"]
            })

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

def retrieve_result():
    try:
        # Read the latest result from the file
        result_data = read_from_file()

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



